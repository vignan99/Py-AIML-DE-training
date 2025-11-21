show tables;
select * from actor ;


create database games;

use games;

create table Games2025 (
g_id INT PRIMARY KEY,
name VARCHAR(100)
);


insert into games2025 (g_id, name) values (1, 'GTA VI'),
(2, 'Fortnite'),
(3, 'Among Us'),
(4, 'Valorant');

alter table games2025 
add column rating int ; 

alter table games2025
drop column name;

select * from games2025;



drop table Games2025;


-- inbuilt functions--  


use sakila;

select first_name, lpad(rpad(first_name,7, '_'),12,'*') from staff ;

select first_name, lpad(substring(first_name, -5,3),6,'*') from actor;

select concat('fullName : "', first_name,'_', last_name,'"') as FullName from actor;

select reverse (concat('fullName : "', first_name,'_', last_name,'"')) as reversed_FullName from actor;

select first_name,last_name ,length( (concat(first_name,last_name))) as length_fullName from actor;

select title, substring(description,locate('of', description),10) as halfDesc from film;

select first_name, concat(upper(substring(first_name,1,1)),lower(substring(first_name,2,10))) as firstLcap from actor;

select first_name, concat(upper(left(first_name,1)),lower(substring(first_name,2))) as firstLcap from actor;

select first_name, concat(lower(left(first_name,1)),upper(right(first_name,length(first_name)-1))) as firstLcap from actor;

select description, replace(description, 'of', 'FOR ' ) from film;

select replacement_cost, round(replacement_cost) from film;

select replacement_cost, round(1.2) from film;


select replacement_cost, ceil(replacement_cost) from film;

select replacement_cost, ceil(1.2) from film;

select replacement_cost, floor(replacement_cost) from film;

select rental_rate, round(power(rental_rate, 2 )) as hiked_rates from film; 

select rental_rate, cast(round(power(rental_rate, 2),2) as decimal(10,2)) as hiked_rates from film;

select title,rental_rate, round(length/rental_rate) as best_value_score from film order by best_value_score desc;


select first_name from actor where first_name regexp '^[aeiou]';

select first_name from actor where first_name not regexp '^[aeiou]';


select email from customer where email regexp '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$';


select avg(length) from film;
select avg(length),min(length),max(length) from film;

select title,length, 
case
when length < 100 then 'short'
when length between 100 and 150 then 'midLength'
when length > 150 then 'lengthy'
end as lengthCat
from film;

select title,trim(title) from film;

-------------------------------------------------- subqueries------------------------------- 

-- find the last registered customer-- 
select first_name, last_name
from customer
where customer_id = (select max(customer_id) from customer);

select title from film where rental_duration = (select max(rental_duration) from film);

-- nested-- actors who acted in kids movies
select first_name from actor where actor_id in (
    select actor_id from film_actor where film_id in (
        select film_id from film where rating in ('PG','PG-13')  )   );



-- select movies with rental rate more than the average ....co related-- 
select title, rating, rental_rate from film f1
where rental_rate > (select avg(rental_rate) from film f2 where f2.rating = f1.rating);


-- select rating, avg(rental_rate) as avg_rate from film group by rating;


-- average rental rate for each rating , and those which are > 3-- derived table
select rating, avg_rate from (select rating, avg(rental_rate) as avg_rate from film group by rating ) as rating_avg where avg_rate > 3;

-- co related-- find the number of rentals per customer.  
select first_name, last_name,(select count(*) from rental r where r.customer_id = c.customer_id) as rental_count from customer c limit 5;













