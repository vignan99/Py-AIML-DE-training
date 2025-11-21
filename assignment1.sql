show databases;

show tables;

select * from customer;

#q1
select * from customer where first_name like 'J%' and active in (1) ;

#q2
select * from film where title like '%ACTION%' or description like '%WAR%';

#q3
select * from customer where last_name != 'smith' and first_name like '%a';

#q4
select * from film where rental_rate > 3.0 and replacement_cost is not NULL;

#q5
select store_id, count(*) as NumOfActiveCusts from customer where active = 1 group by store_id ;
-- select * from customer where store_id = 1 and active = 1;

#q6 
select distinct rating as rating_type from film ;

#q7 
select count(*) as filmsLen100plus , rental_duration from film group by rental_duration having avg(length) > 100 ;

#q8

select date(payment_date) as pay_date, sum(amount) as sum from payment group by date(payment_date) having count(payment_date) > 100 ; 

-- select count(payment_date) from payment;
-- select * from payment limit last 5;

-- select sum(amount) from (select amount from payment limit 5 ) as Squery ;

-- select sum(amount) from payment where payment_date like '%2005-05-25%';

#q9
select * from customer ;

select * from customer where email is NULL or email like '%.org' ; 


#q10
select * from film where rating in ('PG', 'G') order by rental_rate desc;


#q11
select length, count(*) from film  where title like 'T%' group by length having count(*) > 5;


#q12
-- select * from actor;
-- select * from film;
-- select * from actor_info; -- group by first_name;
select actor_id, count(*) as no_of_films_done from film_actor group by actor_id having count(*) > 10;


#q13
select title,rental_rate, length from film order by rental_rate desc, length desc limit 5; 

#q14
select customer_id, count(*) from rental group by customer_id order by count(*) desc;

#q15
select * from rental;
select * from film_list;
select * from film;
select * from inventory;
select * from film_category;
select * from category;
select distinct f.title from film f, rental r, inventory i where f.film_id = i.film_id and i.inventory_id not in (select distinct inventory_id from rental);




#q16
select s.name, p.staff_id, sum(p.amount) from payment p join  staff_list s on s.ID = p.staff_id group by staff_id order by staff_id desc;
-- select * from staff_list;

#q17
select category,count(*) from film_list group by category ;

#q18
select customer_id, sum(amount) from payment group by customer_id order by sum(amount) limit 3;

#q19
select f.title, count(f.title) from film f, rental r, inventory i where f.film_id = i.film_id and r.inventory_id = i.inventory_id and r.rental_date like '%-05-%' and f.rental_duration > 5  group by f.title ;

#q20 
select f.title, count(category_id) from film f join film_category fc on f.film_id = fc.category_id group by fc.category_id having count(category_id) > 50;



select * from rental;
select * from film_list;
select * from film;
select * from inventory;
select * from film_category;
select * from category;
select * from address;
select * from payment;




