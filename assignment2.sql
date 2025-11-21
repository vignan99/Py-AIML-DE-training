use sakila;

show tables;

select * from customer;
#q1
select email, count(*) from customer group by email having count(*) > 1;

select first_name, last_name,  count(*) from customer group by first_name, last_name having count(*) > 1;

#q2
select sum(length(regexp_replace(description, '[^aA]', ''))) as total_a_count from film;

-- or  
select length(description) - length(replace(lower(description),'a','')) as aCount from film;


#q3
select sum(length(regexp_replace(description,'[^aeiouAEIOU]',''))) as total_vowels from film;

-- or if for each separately

select sum(length(description) - length(replace(lower(description),'a',''))) as aCount,
	sum(length(description) - length(replace(lower(description),'e',''))) as eCount,
    sum(length(description) - length(replace(lower(description),'i',''))) as iCount,
    sum(length(description) - length(replace(lower(description),'o',''))) as oCount,
    sum(length(description) - length(replace(lower(description),'u',''))) as uCount
    from film;




#q4
select customer_id, extract(month from payment_date) as month, sum(amount) as total_payment from payment group by customer_id, extract(month from payment_date) order by customer_id,extract(month from payment_date);

#q5
select case when (2024 % 4 = 0 and (2024 % 100 != 0 or 2024 % 400 = 0)) then '2024 is a leap year' else '2024 is not leap year' end as leap_year_check;

#q7
select payment_date, concat('q', extract(quarter from payment_date)) as quarter from payment;



#q8 -not working
select concat(year(curdate()) - year('1999-06-03'), ' years, ', month(curdate()) - month('1999-06-03'), ' months, ', day(curdate()) - day('2000-07-08'), ' days') as age;
              
select concat(floor(datediff(curdate(),'1999-06-03')/365), 'years,', floor((datediff(curdate(),'1999-06-03') % 365)/30), 'months,', (datediff(curdate(),'1999-06-03') % 365) % 30, 'days') as age;










