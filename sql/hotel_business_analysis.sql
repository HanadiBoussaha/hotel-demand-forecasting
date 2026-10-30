CREATE DATABASE hotel_revenue;
USE hotel_revenue;

CREATE TABLE daily_demand (
    arrival_date DATE,
    hotel VARCHAR(30),
    bookings INT,
    cancellations INT,
    avg_adr DECIMAL(10,2),
    total_revenue DECIMAL(14,2),
    avg_lead_time DECIMAL(10,2),
    avg_stay_nights DECIMAL(10,2),
    cancellation_rate DECIMAL(10,2)
);

CREATE TABLE monthly_performance (
    arrival_date_year INT,
    arrival_date_month VARCHAR(15),
    hotel VARCHAR(30),
    bookings INT,
    cancellations INT,
    avg_adr DECIMAL(10,2),
    total_revenue DECIMAL(14,2),
    avg_lead_time DECIMAL(10,2),
    avg_stay_nights DECIMAL(10,2),
    month_number INT,
    cancellation_rate DECIMAL(10,2)
);

CREATE TABLE market_segment (
    hotel VARCHAR(30),
    market_segment VARCHAR(30),
    bookings INT,
    cancellations INT,
    avg_adr DECIMAL(10,2),
    total_revenue DECIMAL(14,2),
    avg_lead_time DECIMAL(10,2),
    avg_stay_nights DECIMAL(10,2),
    cancellation_rate DECIMAL(10,2)
);

CREATE TABLE channel_performance (
    hotel VARCHAR(30),
    distribution_channel VARCHAR(30),
    bookings INT,
    cancellations INT,
    avg_adr DECIMAL(10,2),
    total_revenue DECIMAL(14,2),
    avg_lead_time DECIMAL(10,2),
    cancellation_rate DECIMAL(10,2)
);

-- Total bookings by hotel
SELECT hotel, SUM(bookings) AS total_bookings
FROM daily_demand
GROUP BY hotel;

-- Cancellation rate by hotel
SELECT hotel, ROUND(SUM(cancellations) * 100.0 / SUM(bookings), 2) AS cancellation_rate
FROM daily_demand
GROUP BY hotel;

-- Revenue by hotel
SELECT hotel, ROUND(SUM(total_revenue), 2) AS revenue
FROM daily_demand
GROUP BY hotel
ORDER BY revenue DESC;

-- Average ADR by hotel
SELECT hotel, ROUND(AVG(avg_adr), 2) AS avg_adr
FROM daily_demand
GROUP BY hotel;

-- Monthly bookings
SELECT arrival_date_year, arrival_date_month, hotel, bookings
FROM monthly_performance
ORDER BY arrival_date_year, month_number;

-- Top 5 months by revenue
SELECT arrival_date_year, arrival_date_month, hotel, total_revenue
FROM monthly_performance
ORDER BY total_revenue DESC
LIMIT 5;

-- Market segment performance
SELECT market_segment, SUM(bookings) AS bookings
FROM market_segment
GROUP BY market_segment
ORDER BY bookings DESC;

-- Distribution channel performance
SELECT distribution_channel, SUM(bookings) AS bookings
FROM channel_performance
GROUP BY distribution_channel
ORDER BY bookings DESC;