#!/usr/bin/env python3
"""Standalone scraper and preprocessing script for Task 1.

Usage:
  python scripts/src/scrape_preprocess.py --output notebooks/data/processed/ethiopian_bank_reviews_clean.csv --count 500

The script attempts to scrape Google Play reviews for the configured BANKS. If the
`google_play_scraper` package is not available or scraping fails, the script will
exit with a helpful message. It also supports reusing an existing cleaned CSV.
"""
import argparse
import os
import re
import sys
from datetime import datetime
import logging
import uuid

import numpy as np
import pandas as pd

try:
    from google_play_scraper import reviews, app, Sort
    HAS_SCRAPER = True
except Exception:
    HAS_SCRAPER = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BANKS = [
    {
        'bank': 'Commercial Bank of Ethiopia',
        'app_name': 'CBE Mobile Banking',
        'app_id': 'com.combanketh.mobilebanking',
        'source': 'google_play',
        'source_url': 'https://play.google.com/store/apps/details?id=com.combanketh.mobilebanking',
    },
    {
        'bank': 'Bank of Abyssinia',
        'app_name': 'BOA Mobile Banking',
        'app_id': 'com.boa.boaMobileBanking',
        'source': 'google_play',
        'source_url': 'https://play.google.com/store/apps/details?id=com.boa.boaMobileBanking',
    },
    {
        'bank': 'Dashen Bank',
        'app_name': 'Dashen SuperApp',
        'app_id': 'com.dashen.dashensuperapp',
        'source': 'google_play',
        'source_url': 'https://play.google.com/store/apps/details?id=com.dashen.dashensuperapp',
    }
]


def clean_review_text(text: str) -> str:
    if pd.isna(text):
        return ''
    text = str(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def scrape_reviews_for_bank(bank_config, count=500):
    logging.info(f"Scraping reviews for {bank_config['bank']} ({bank_config['app_id']})")
    if not HAS_SCRAPER:
        raise RuntimeError('google_play_scraper package is not available in this environment')

    result, _ = reviews(
        bank_config['app_id'],
        lang='en',
        country='et',
        sort=Sort.NEWEST,
        count=count,
        filter_score_with=None,
    )

    rows = []
    for r in result:
        rows.append({
            'review_id': r.get('reviewId', '') or '',
            'review': r.get('content', '') or '',
            'rating': r.get('score', np.nan),
            'date': r.get('at', None),
            'bank': bank_config['bank'],
            'app_name': bank_config['app_name'],
            'source': bank_config['source'],
            'source_url': bank_config['source_url'],
        })

    logging.info(f"Collected {len(rows)} reviews for {bank_config['bank']}")
    return rows


def assemble_and_clean(raw_rows):
    df_raw = pd.DataFrame(raw_rows)
    logging.info(f"Combined raw dataset shape: {df_raw.shape}")

    df = df_raw.copy()
    df = df.dropna(subset=['review', 'rating'])
    df = df.drop_duplicates(subset=['review_id'], keep='first')
    df = df.drop_duplicates(subset=['review'], keep='first')
    df['review'] = df['review'].apply(clean_review_text)
    df = df[df['review'].str.len() > 0]
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df = df.dropna(subset=['date'])
    df = df[df['rating'].between(1, 5)]
    df['rating'] = df['rating'].astype(int)

    # Ensure review_id exists
    if 'review_id' not in df.columns or df['review_id'].isnull().any() or (df['review_id'] == '').any():
        df['review_id'] = [str(uuid.uuid4()) for _ in range(len(df))]

    final = df[['review_id', 'review', 'rating', 'date', 'bank', 'source']].copy()
    return final


def main():
    parser = argparse.ArgumentParser(description='Scrape and preprocess Google Play reviews for the target banks')
    parser.add_argument('--count', type=int, default=500, help='Max reviews per bank')
    parser.add_argument('--output', type=str, default=os.path.join('notebooks', 'data', 'processed', 'ethiopian_bank_reviews_clean.csv'))
    parser.add_argument('--force', action='store_true', help='Force scraping even if output exists')

    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    if os.path.exists(args.output) and not args.force:
        logging.info(f"Found existing cleaned CSV at {args.output}. Use --force to overwrite.")
        try:
            df_existing = pd.read_csv(args.output)
            logging.info(f"Existing CSV shape: {df_existing.shape}")
            return 0
        except Exception as exc:
            logging.warning(f"Could not read existing CSV: {exc}. Will attempt to re-scrape.")

    if not HAS_SCRAPER:
        logging.error('google_play_scraper is not installed in this environment; cannot scrape.')
        logging.error('If you only want to preprocess an existing CSV, run the notebook or provide the CSV manually.')
        return 2

    raw_rows = []
    for bank in BANKS:
        try:
            raw_rows.extend(scrape_reviews_for_bank(bank, count=args.count))
        except Exception as exc:
            logging.error(f"Error scraping {bank['bank']}: {exc}")

    if len(raw_rows) == 0:
        logging.error('No reviews were collected. Exiting.')
        return 3

    df_clean = assemble_and_clean(raw_rows)
    df_clean.to_csv(args.output, index=False)
    logging.info(f"Saved cleaned dataset to: {args.output} (shape: {df_clean.shape})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
