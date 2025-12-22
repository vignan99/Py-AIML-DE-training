
###dropdown###########
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import csv
from datetime import datetime

DATA_FILE = "health_data_draft.csv"

###createing or 
def create_file_if_not_exists():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "date",
                "calories_eaten",
                "sleep_hours",
                "steps",
                "exercise_scale",
                # "calories_burned",
                "mood"
            ])

###loading the csv and cleaning it 
def load_and_clean_data():
    df = pd.read_csv(DATA_FILE)

    if df.empty:
        return df

    numeric_cols = [
        "calories_eaten",
        "sleep_hours",
        "steps",
        "exercise_scale",
        "mood"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    # df['mood'] = df['mood'].round(0).astype(int)
    # df["mood"] = df["mood"].round().astype(int)

    df["mood"] = df["mood"].round().astype(int).clip(0,5)




    # compute calories burned
    df["calories_burned"] = (df["steps"] * 0.04 + df["exercise_scale"] * 50).round(2)

    # clean dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # health score
    BMR = 1700
    df["health_score"] = 0

    df.loc[df["sleep_hours"].between(6.5, 8), "health_score"] += 1
    df.loc[df["steps"].between(5000, 10000), "health_score"] += 1
    df.loc[df["exercise_scale"].between(1, 3), "health_score"] += 1
    df.loc[((BMR + df["calories_burned"]) - df["calories_eaten"]).abs() <= 200, "health_score"] += 1

    
    df.to_csv(DATA_FILE, index=False)

    return df
##

####ui
st.set_page_config(page_title="Health Tracker", layout="wide")
st.title("📊 Health Activity Tracker")

create_file_if_not_exists()

if "df" not in st.session_state:
    st.session_state.df = load_and_clean_data()

### add rows 
st.header("➕ Add Daily Entry")

with st.form("add_entry_form"):
    new_date = st.date_input("Date", datetime.today())
    new_calories = st.number_input("Calories Eaten", min_value=0, step=1)
    new_sleep = st.number_input("Sleep Hours", min_value=0.0, max_value=24.0, step=0.5)
    new_steps = st.number_input("Steps", min_value=0, step=1)
    new_exercise = st.number_input("Exercise Scale (0–5)", min_value=0, max_value=5, step=1)
    new_mood = st.number_input("Mood (0–5)", min_value=0, max_value=5, step=1)

    submitted = st.form_submit_button("Add Entry")

    if submitted:
        calories_burned = round(new_steps * 0.04 + new_exercise * 50, 2)

        new_row = pd.DataFrame([{
            "date": new_date.strftime("%Y-%m-%d"),
            "calories_eaten": new_calories,
            "sleep_hours": new_sleep,
            "steps": new_steps,
            "exercise_scale": new_exercise,
            "calories_burned": calories_burned,
            # "mood": int(new_mood)
            "mood": int(round(new_mood)) 
        }])

        new_row.to_csv(DATA_FILE, mode="a", header=False, index=False)

        st.session_state.df = load_and_clean_data()
        st.success("✅ Entry added and cleaned")

df = st.session_state.df

###dropdown selecter
st.header("📂 View Options")

view = st.selectbox(
    "Choose what to display",
    [
        "Basic Stats",
        "Steps & Calories Trends",
        "Sleep vs Mood",
        "Healthy / Happy Days",
        "Health Score Over Time"
    ]
)

df_sorted = df.sort_values("date")

####grpahs/charts
if not df.empty:

    if view == "Basic Stats":
        st.subheader("📈 Basic Stats")
        st.write(f"Total entries: {len(df)}")
        st.write(f"Average steps: {df['steps'].mean():.0f}")
        st.write(f"Average sleep: {df['sleep_hours'].mean():.2f}")
        st.write(f"Average mood: {df['mood'].mean():.2f}")
        st.write(f"Average health score: {df['health_score'].mean():.2f}")

    elif view == "Steps & Calories Trends":
        st.subheader("🚶 Steps Over Time")
        st.line_chart(df_sorted.set_index("date")[["steps"]])

        st.subheader("🔥 Calories Burned Over Time")
        st.line_chart(df_sorted.set_index("date")[["calories_burned"]])

    elif view == "Sleep vs Mood":
        st.subheader("😴 Sleep vs Mood")
        fig, ax = plt.subplots()
        ax.scatter(df["sleep_hours"], df["mood"])
        ax.set_xlabel("Sleep Hours")
        ax.set_ylabel("Mood")
        ax.grid(True)
        st.pyplot(fig)

    elif view == "Healthy / Happy Days":
        st.subheader("Mood on Balanced Days (Health Score ≥ 3)")
        healthy = df_sorted[df_sorted["health_score"] >= 3]

        if not healthy.empty:
            st.line_chart(healthy.set_index("date")[["mood"]])
        else:
            st.info("No balanced days yet. Consistency > intensity.")

        st.subheader("Health Score Distribution")
        st.bar_chart(df["health_score"].value_counts().sort_index())

    elif view == "Health Score Over Time":
        st.subheader("Health Score Over Time")
        st.line_chart(df_sorted.set_index("date")[["health_score"]])

else:
    st.info("No data yet. Add entries to begin.")
