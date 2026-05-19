-- Task 3 - Database Schema
-- PostgreSQL database for bank reviews analytics

-- Create database
CREATE DATABASE bank_reviews;

-- Connect to database
\c bank_reviews;

-- Banks table: Stores bank metadata
CREATE TABLE banks (
    bank_id SERIAL PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL UNIQUE,
    app_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table: Stores processed review data
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    bank_id INTEGER REFERENCES banks(bank_id) ON DELETE CASCADE,
    review_text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_date DATE NOT NULL,
    sentiment_label VARCHAR(10),
    sentiment_score DECIMAL(4,3),
    identified_theme VARCHAR(50),
    source VARCHAR(50) DEFAULT 'Google Play',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_reviews_bank_id ON reviews(bank_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_date ON reviews(review_date);
CREATE INDEX idx_reviews_sentiment ON reviews(sentiment_label);
CREATE INDEX idx_reviews_theme ON reviews(identified_theme);

-- Insert bank data
INSERT INTO banks (bank_name, app_name) VALUES
    ('Commercial Bank of Ethiopia', 'com.combanketh.mobilebanking'),
    ('Bank of Abyssinia', 'com.boa.boaMobileBanking'),
    ('Dashen Bank', 'com.dashen.dashensuperapp')
ON CONFLICT (bank_name) DO NOTHING;

-- Sample verification queries

-- 1. Count reviews per bank
SELECT b.bank_name, COUNT(r.review_id) as review_count
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name
ORDER BY b.bank_name;

-- 2. Average rating per bank
SELECT b.bank_name, ROUND(AVG(r.rating), 2) as avg_rating
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name
ORDER BY avg_rating DESC;

-- 3. Sentiment distribution by bank
SELECT b.bank_name, r.sentiment_label, COUNT(*) as count
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name, r.sentiment_label
ORDER BY b.bank_name, r.sentiment_label;

-- 4. Most common themes per bank
SELECT b.bank_name, r.identified_theme, COUNT(*) as theme_count
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name, r.identified_theme
ORDER BY b.bank_name, theme_count DESC;