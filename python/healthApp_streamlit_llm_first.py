
# ======================================================
# Health Tracker App — LLM-FIRST Q&A (Groq) + Safe Execution
# ======================================================
# Behavior:
#   - ALWAYS tries Groq (LLM) first for every question.
#   - Executes the returned plan safely on your CSV.
#   - If Groq is unavailable / plan invalid, it falls back to rule-based (optional).
#
# Setup:
#   export GROQ_API_KEY="gsk_..."
#   streamlit run healthApp_streamlit_llm_first.py
# ======================================================

import streamlit as st
import pandas as pd
import numpy as np
import os
import csv
import uuid
import json
import requests
from datetime import datetime, date, timedelta

# ---------------- CONFIG ----------------
DATA_FILE = "health_data_draft.csv"

SCHEMA = [
    "record_id", "created_at", "source", "date",
    "calories_eaten", "sleep_hours", "steps",
    "exercise_scale", "mood",
    "calories_burned", "health_score"
]

# ---------------- STEP 1: DATA SAFETY ----------------
def create_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="") as f:
            csv.writer(f).writerow(SCHEMA)

def ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    for c in SCHEMA:
        if c not in df.columns:
            df[c] = np.nan
    return df[SCHEMA]

def compute_calories_burned(steps, exercise):
    return round(float(steps) * 0.04 + float(exercise) * 50, 2)

def compute_health_score(df: pd.DataFrame) -> pd.Series:
    score = (
        df["sleep_hours"].between(6.5, 8).astype(int) +
        df["steps"].between(5000, 10000).astype(int) +
        df["exercise_scale"].between(1, 3).astype(int) +
        (((1700 + df["calories_burned"]) - df["calories_eaten"]).abs() <= 200).astype(int)
    )
    return score

def load_data() -> pd.DataFrame:
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=SCHEMA)

    df = pd.read_csv(DATA_FILE)
    df = ensure_schema(df)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()

    for c in ["calories_eaten", "sleep_hours", "steps", "exercise_scale", "mood"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["mood"] = pd.to_numeric(df["mood"], errors="coerce").fillna(0).round().astype(int).clip(0, 5)

    df["calories_burned"] = df.apply(
        lambda r: compute_calories_burned(r["steps"], r["exercise_scale"]), axis=1
    )
    df["health_score"] = compute_health_score(df)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_csv(DATA_FILE, index=False)
    return df

# ---------------- Optional fallback: RULE-BASED ----------------
def answer_rule_based(df: pd.DataFrame, q: str):
    q = (q or "").strip().lower()
    if not q or df.empty:
        return None

    today = pd.to_datetime(date.today())

    if "step" in q:
        col = "steps"
    elif "sleep" in q:
        col = "sleep_hours"
    elif "calorie" in q:
        col = "calories_burned"
    elif "mood" in q:
        col = "mood"
    elif "score" in q:
        col = "health_score"
    else:
        return None

    dts = pd.to_datetime(df["date"], errors="coerce")
    dfx = df.copy()

    if "today" in q:
        dfx = dfx[dfx["date"] == today.strftime("%Y-%m-%d")]
    elif "yesterday" in q:
        dfx = dfx[dfx["date"] == (today - timedelta(days=1)).strftime("%Y-%m-%d")]
    elif "this month" in q or "this_month" in q:
        dfx = dfx[(dts.dt.year == today.year) & (dts.dt.month == today.month)]
    elif "last month" in q or "last_month" in q:
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        dfx = dfx[(dts.dt.year == last_month_end.year) & (dts.dt.month == last_month_end.month)]

    if dfx.empty:
        return "No data found for that period."

    series = pd.to_numeric(dfx[col], errors="coerce")

    if "avg" in q or "average" in q or "mean" in q:
        return f"Average {col.replace('_',' ')}: {series.mean():.2f}"
    return f"Total {col.replace('_',' ')}: {series.sum():.0f}"

# ---------------- LLM: GROQ PLANNER ----------------
def groq_plan(question: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not set. In terminal: export GROQ_API_KEY='gsk_...'"}

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a planner for a health-tracker dataset. "
                    "Return ONLY a valid JSON object. No extra text, no markdown. "
                    "Allowed keys: metric, operation, period_1, period_2, aggregation. "
                    "Allowed metrics: steps, sleep_hours, calories_eaten, calories_burned, mood, health_score, exercise_scale. "
                    "Allowed operations: aggregate, compare, trend, >, <, >=, <=. "
                    "Allowed periods: today, yesterday, last_7_days, this_week, this_month, last_month, all_time. "
                    "Aggregation should be one of: sum, mean, max, min, count."
                )
            },
            {"role": "user", "content": question}
        ],
        "temperature": 0
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=20
    )

    try:
        data = r.json()
    except Exception:
        return {"error": f"Non-JSON response from Groq (HTTP {r.status_code})"}

    if "error" in data:
        return {"error": data["error"]}

    content = data["choices"][0]["message"]["content"]

    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except Exception:
        return {"error": "LLM did not return valid JSON", "raw_response": content}

# ---------------- Plan Normalization + Execution ----------------
METRIC_MAP = {
    "steps": "steps",
    "sleep_hours": "sleep_hours",
    "calories_eaten": "calories_eaten",
    "calories_burned": "calories_burned",
    "mood": "mood",
    "health_score": "health_score",
    "exercise_scale": "exercise_scale",

    # common synonyms
    "distance_walked": "steps",
    "walking_distance": "steps",
    "steps_walked": "steps",
    "sleep": "sleep_hours",
    "calories": "calories_burned",
    "burned_calories": "calories_burned",
    "calories_intake": "calories_eaten",
    "intake": "calories_eaten",
}

AGG_MAP = {
    "sum": "sum",
    "total": "sum",
    "mean": "mean",
    "avg": "mean",
    "average": "mean",
    "max": "max",
    "min": "min",
    "count": "count",
}

ALLOWED_PERIODS = {"today","yesterday","last_7_days","this_week","this_month","last_month","all_time"}

def filter_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    dfx = df.copy()
    dfx["date"] = pd.to_datetime(dfx["date"], errors="coerce")
    dfx = dfx.dropna(subset=["date"]).copy()
    today_dt = pd.to_datetime(date.today())

    period = (period or "all_time").lower().strip()
    if period not in ALLOWED_PERIODS:
        period = "all_time"

    if period == "today":
        return dfx[dfx["date"] == today_dt]
    if period == "yesterday":
        return dfx[dfx["date"] == (today_dt - timedelta(days=1))]
    if period == "last_7_days":
        return dfx[dfx["date"] >= (today_dt - timedelta(days=7))]
    if period == "this_week":
        start = today_dt - timedelta(days=int(today_dt.dayofweek))
        return dfx[dfx["date"] >= start]
    if period == "this_month":
        return dfx[(dfx["date"].dt.year == today_dt.year) & (dfx["date"].dt.month == today_dt.month)]
    if period == "last_month":
        first_this_month = today_dt.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        return dfx[(dfx["date"].dt.year == last_month_end.year) & (dfx["date"].dt.month == last_month_end.month)]
    return dfx

def normalize_plan(plan: dict) -> dict:
    if not isinstance(plan, dict):
        return {"error": "Plan is not a JSON object"}

    metric_raw = str(plan.get("metric", "")).strip().lower()
    op_raw = str(plan.get("operation", "")).strip().lower()
    p1 = str(plan.get("period_1", "all_time")).strip().lower()
    p2 = str(plan.get("period_2", "all_time")).strip().lower()
    agg_raw = str(plan.get("aggregation", "sum")).strip().lower()

    metric = METRIC_MAP.get(metric_raw)
    if not metric:
        return {"error": f"Unsupported metric '{metric_raw}'."}

    if p1 not in ALLOWED_PERIODS:
        p1 = "all_time"
    if p2 not in ALLOWED_PERIODS:
        p2 = "all_time"

    operation = op_raw
    if operation in {">","<",">=","<="}:
        operation = "compare"
    if operation not in {"aggregate","compare","trend"}:
        operation = "aggregate"

    aggregation = AGG_MAP.get(agg_raw, "sum")

    return {"metric": metric, "operation": operation, "period_1": p1, "period_2": p2, "aggregation": aggregation}

def aggregate_series(series: pd.Series, agg: str):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return None
    if agg == "count":
        return int(s.shape[0])
    return float(getattr(s, agg)())

def execute_plan(df: pd.DataFrame, plan: dict):
    n = normalize_plan(plan)
    if "error" in n:
        return f"❌ {n['error']}", None

    metric = n["metric"]
    operation = n["operation"]
    p1 = n["period_1"]
    p2 = n["period_2"]
    agg = n["aggregation"]

    if df.empty:
        return "No data yet. Add entries first.", None

    if operation == "trend":
        dfx = filter_period(df, p1)
        if dfx.empty:
            return f"No data found for {p1}.", None
        dfx["date"] = pd.to_datetime(dfx["date"], errors="coerce")
        dfx = dfx.dropna(subset=["date"]).sort_values("date")
        out = dfx[["date", metric]].copy()
        return f"Showing {metric.replace('_',' ')} trend for {p1}.", out

    if operation == "compare":
        a = filter_period(df, p1)
        b = filter_period(df, p2)
        va = aggregate_series(a[metric] if not a.empty else pd.Series(dtype=float), agg)
        vb = aggregate_series(b[metric] if not b.empty else pd.Series(dtype=float), agg)

        if va is None or vb is None:
            return f"No numeric data to compare for {metric.replace('_',' ')}.", None

        diff = va - vb
        pct = None if vb == 0 else (diff / vb) * 100.0

        metric_label = metric.replace("_", " ")
        agg_label = "average" if agg == "mean" else agg

        if diff > 0:
            direction = "higher than"
        elif diff < 0:
            direction = "lower than"
        else:
            direction = "the same as"

        if pct is None:
            return (
                f"{agg_label.capitalize()} {metric_label}: {p1} = {va:.2f}, {p2} = {vb:.2f}. "
                f"{p1} is {direction} {p2} by {diff:.2f}.",
                None
            )

        return (
            f"{agg_label.capitalize()} {metric_label}: {p1} = {va:.2f}, {p2} = {vb:.2f}. "
            f"{p1} is {direction} {p2} by {diff:.2f} ({pct:.1f}%).",
            None
        )

    dfx = filter_period(df, p1)
    if dfx.empty:
        return f"No data found for {p1}.", None

    val = aggregate_series(dfx[metric], agg)
    if val is None:
        return f"No numeric values available for {metric.replace('_',' ')} in {p1}.", None

    metric_label = metric.replace("_", " ")
    if agg == "sum":
        return f"Total {metric_label} for {p1}: {val:.2f}", None
    if agg == "mean":
        return f"Average {metric_label} for {p1}: {val:.2f}", None
    if agg == "max":
        return f"Max {metric_label} for {p1}: {val:.2f}", None
    if agg == "min":
        return f"Min {metric_label} for {p1}: {val:.2f}", None
    if agg == "count":
        return f"Count of {metric_label} entries for {p1}: {int(val)}", None

    return f"{agg.capitalize()} {metric_label} for {p1}: {val:.2f}", None

# ---------------- UI ----------------
st.set_page_config(page_title="Health App", layout="wide")
st.title("🏥 Health Tracker — LLM-FIRST Q&A")

create_file()
df = load_data()

st.header("➕ Add Entry")
with st.form("add"):
    d = st.date_input("Date", date.today())
    c = st.number_input("Calories eaten", min_value=0, step=1)
    s = st.number_input("Sleep hours", min_value=0.0, max_value=24.0, step=0.5)
    stp = st.number_input("Steps", min_value=0, step=1)
    ex = st.number_input("Exercise (0–5)", min_value=0, max_value=5, step=1)
    m = st.number_input("Mood (0–5)", min_value=0, max_value=5, step=1)
    ok = st.form_submit_button("Save")

    if ok:
        row = {
            "record_id": uuid.uuid4().hex,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source": "user",
            "date": d.strftime("%Y-%m-%d"),
            "calories_eaten": float(c),
            "sleep_hours": float(s),
            "steps": int(stp),
            "exercise_scale": int(ex),
            "mood": int(m),
            "calories_burned": compute_calories_burned(int(stp), int(ex)),
            "health_score": 0
        }
        df2 = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df2 = ensure_schema(df2)
        df2.to_csv(DATA_FILE, index=False)
        st.success("Saved ✅")

df = load_data()

st.header("💬 Ask your health data (LLM-first)")
st.caption("Ask naturally: 'Did I sleep more this month than last month?' • 'Compare steps this week vs last week' • 'trend sleep this_month'")

q = st.text_input("Ask a question")

if q:
    # ALWAYS call LLM first
    plan = groq_plan(q)

    if isinstance(plan, dict) and plan.get("error"):
        st.error(plan["error"])
        if plan.get("raw_response"):
            st.code(plan["raw_response"])

        # Optional fallback so you still get something if Groq is down:
        fallback = answer_rule_based(df, q)
        if fallback:
            st.warning("Groq failed, showing fallback answer:")
            st.success(fallback)
    else:
        answer_text, chart_df = execute_plan(df, plan)
        st.success(answer_text)

        if chart_df is not None and not chart_df.empty:
            metric_col = [c for c in chart_df.columns if c != "date"][0]
            chart_df = chart_df.sort_values("date")
            st.line_chart(chart_df.set_index("date")[[metric_col]])

        with st.expander("Show raw AI plan (debug)"):
            st.json(plan)
