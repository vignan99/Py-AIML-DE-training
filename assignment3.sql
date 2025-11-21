
select * from payment;

#q1
select * from customer where customer_id in ( select customer_id from payment group by customer_id having count(payment_id) > 5);

#q2
select first_name, last_name from actor where actor_id in (select actor_id from film_actor group by actor_id having count(film_id) > 10);

#q3
select first_name, last_name from customer where customer_id not in (select customer_id from payment);

#q4
select title from film where rental_rate > (select avg(rental_rate) from film);

#q5
select title from film where film_id not in (select film_id from rental);

#q6


#q7
select * from staff where staff_id in (select staff_id from payment where amount > (select avg(amount) from payment));

#q8
select title, rental_duration from film where rental_duration > (select avg(rental_duration) from film);
select avg(rental_duration) from film;

#q9
select * from customer where address_id = (select address_id from customer where customer_id = 1);

#q10
select payment_id, amount from payment where amount > (select avg(amount) from payment) order by amount;
select avg(amount) from payment


#





