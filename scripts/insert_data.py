"""
Task 3 - Data Insertion
Loads cleaned review data and inserts into PostgreSQL database.
"""

from pathlib import Path

import pandas as pd
import psycopg2

try:
    from create_database import get_bank_id_mapping
except ImportError:
    from scripts.create_database import get_bank_id_mapping

# Database connection parameters (same as above)
DB_NAME = "bank_reviews"
DB_USER = "postgres"
DB_PASSWORD = "mynewpassword123"
DB_HOST = "localhost"
DB_PORT = "5432"


def find_existing_file(candidates):
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def normalize_review_text(series):
    return (
        series.astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.lower()
    )

def load_and_prepare_data():
    """Load Task 1 base data and Task 2 sentiment output, then combine them."""
    project_root = Path(__file__).resolve().parents[1]

    base_candidates = [
        project_root / 'notebooks' / 'data' / 'processed' / 'ethiopian_bank_reviews_clean.csv',
        project_root / 'data' / 'processed' / 'ethiopian_bank_reviews_clean.csv',
        project_root / 'data' / 'raw' / 'ethiopian_bank_reviews_clean.csv',
    ]
    sentiment_candidates = [
        project_root / 'data' / 'processed' / 'fintech_sentiment_analysis_results.csv',
        project_root / 'notebooks' / 'data' / 'processed' / 'fintech_sentiment_analysis_results.csv',
    ]

    base_path = find_existing_file(base_candidates)
    if base_path is None:
        raise FileNotFoundError(f"Base cleaned CSV not found. Checked: {base_candidates}")

    base_df = pd.read_csv(base_path)
    print(f"📂 Loaded base data from: {base_path} ({len(base_df)} rows)")

    sentiment_path = find_existing_file(sentiment_candidates)
    if sentiment_path is None:
        raise FileNotFoundError(f"Sentiment CSV not found. Checked: {sentiment_candidates}")

    sentiment_df = pd.read_csv(sentiment_path)
    print(f"📂 Loaded sentiment data from: {sentiment_path} ({len(sentiment_df)} rows)")

    base_df = base_df.copy()
    sentiment_df = sentiment_df.copy()
    base_df['_review_key'] = normalize_review_text(base_df['review'])
    sentiment_df['_review_key'] = normalize_review_text(sentiment_df['review_text'])

    sentiment_lookup = (
        sentiment_df.drop_duplicates(subset=['_review_key'], keep='first')
        .set_index('_review_key')[['sentiment_label', 'sentiment_score', 'identified_theme']]
    )

    combined = base_df.join(sentiment_lookup, on='_review_key')
    combined = combined.drop(columns=['_review_key'])

    unmatched = int(combined['sentiment_label'].isna().sum())
    if unmatched:
        print(f"⚠️ {unmatched} reviews did not match Task 2 output and will use default sentiment values.")
        combined['sentiment_label'] = combined['sentiment_label'].fillna('NEUTRAL')
        combined['sentiment_score'] = combined['sentiment_score'].fillna(0.0)
        combined['identified_theme'] = combined['identified_theme'].fillna('Other')

    print(f"📂 Combined {len(combined)} reviews for database insertion")
    return combined

def insert_reviews(df, bank_map):
    """Insert reviews into the database"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for _, row in df.iterrows():
        bank_id = bank_map.get(row['bank'])
        if bank_id is None:
            print(f"⚠️ Unknown bank: {row['bank']}")
            skipped += 1
            continue
        
        try:
            cursor.execute("""
                INSERT INTO reviews 
                (bank_id, review_text, rating, review_date, 
                 sentiment_label, sentiment_score, identified_theme, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bank_id,
                row['review'],
                int(row['rating']),
                row['date'],
                row.get('sentiment_label', 'NEUTRAL'),
                row.get('sentiment_score', 0.5),
                row.get('identified_theme', 'Other'),
                row.get('source', 'Google Play')
            ))
            inserted += 1
        except Exception as e:
            print(f"❌ Error inserting review: {e}")
            skipped += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Inserted {inserted} reviews")
    print(f"⚠️ Skipped {skipped} reviews")
    
    return inserted

def verify_data():
    """Run verification queries to ensure data integrity"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
    print("\n" + "=" * 50)
    print("DATA VERIFICATION")
    print("=" * 50)
    
    # Count reviews per bank
    query = """
        SELECT b.bank_name, COUNT(r.review_id) as review_count
        FROM banks b
        LEFT JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY b.bank_name
    """
    result = pd.read_sql(query, conn)
    print("\n📊 Reviews per bank:")
    print(result.to_string(index=False))
    
    # Average rating per bank
    query = """
        SELECT b.bank_name, AVG(r.rating) as avg_rating
        FROM banks b
        LEFT JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY b.bank_name
    """
    result = pd.read_sql(query, conn)
    print("\n⭐ Average rating per bank:")
    print(result.to_string(index=False))
    
    # Check for nulls in key columns
    query = """
        SELECT 
            COUNT(*) as total_reviews,
            SUM(CASE WHEN review_text IS NULL THEN 1 ELSE 0 END) as null_review_text,
            SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) as null_rating,
            SUM(CASE WHEN sentiment_label IS NULL THEN 1 ELSE 0 END) as null_sentiment
        FROM reviews
    """
    result = pd.read_sql(query, conn)
    print("\n🔍 Data Integrity Check:")
    print(result.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("TASK 3: Data Insertion")
    print("=" * 50)
    
    # Load data
    df = load_and_prepare_data()
    
    # Get bank ID mapping
    bank_map = get_bank_id_mapping()
    print(f"📋 Bank mapping: {bank_map}")
    
    # Insert reviews
    inserted_count = insert_reviews(df, bank_map)
    
    # Verify
    verify_data()
    
    print("\n✅ Task 3 complete!")