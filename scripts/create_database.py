"""
Task 3 - Database Setup
Creates PostgreSQL database and tables for storing bank reviews
"""

import psycopg2
from psycopg2 import sql
import pandas as pd

# Database connection parameters
DB_NAME = "bank_reviews"
DB_USER = "postgres"  
DB_PASSWORD = "mynewpassword123"  
DB_HOST = "localhost"
DB_PORT = "5432"

def create_database():
    """Create the bank_reviews database if it doesn't exist"""
    # Connect to default postgres database
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print(f"✅ Database '{DB_NAME}' created")
    else:
        print(f"ℹ️ Database '{DB_NAME}' already exists")
    
    cursor.close()
    conn.close()

def create_tables():
    """Create banks and reviews tables with proper schema"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    
    # Create banks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banks (
            bank_id SERIAL PRIMARY KEY,
            bank_name VARCHAR(100) NOT NULL UNIQUE,
            app_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Banks table created")
    
    # Create reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id SERIAL PRIMARY KEY,
            bank_id INTEGER REFERENCES banks(bank_id),
            review_text TEXT NOT NULL,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            review_date DATE NOT NULL,
            sentiment_label VARCHAR(10),
            sentiment_score DECIMAL(4,3),
            identified_theme VARCHAR(50),
            source VARCHAR(50) DEFAULT 'Google Play',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Reviews table created")
    
    conn.commit()
    cursor.close()
    conn.close()

def insert_banks():
    """Insert bank information into banks table"""
    banks_data = [
        ("Commercial Bank of Ethiopia", "com.combanketh.mobilebanking"),
        ("Bank of Abyssinia", "com.boa.boaMobileBanking"),
        ("Dashen Bank", "com.dashen.dashensuperapp")
    ]
    
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    
    for bank_name, app_name in banks_data:
        cursor.execute("""
            INSERT INTO banks (bank_name, app_name)
            VALUES (%s, %s)
            ON CONFLICT (bank_name) DO NOTHING
        """, (bank_name, app_name))
    
    conn.commit()
    print(f"✅ Inserted {len(banks_data)} banks")
    
    cursor.close()
    conn.close()

def get_bank_id_mapping():
    """Get mapping of bank names to their IDs"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
    bank_map = pd.read_sql("SELECT bank_id, bank_name FROM banks", conn)
    conn.close()
    return dict(zip(bank_map['bank_name'], bank_map['bank_id']))

if __name__ == "__main__":
    print("=" * 50)
    print("TASK 3: Database Setup")
    print("=" * 50)
    
    create_database()
    create_tables()
    insert_banks()
    
    print("\n✅ Database setup complete!")