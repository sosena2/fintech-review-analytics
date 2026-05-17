# Fintech Review Analytics

Customer Experience Analytics for Ethiopian fintech apps. This repository turns Google Play reviews into cleaned datasets, sentiment scores, themes, and stakeholder-ready insights for three banks:

- Commercial Bank of Ethiopia
- Bank of Abyssinia
- Dashen Bank

## Task 1: Scraping and Preprocessing

Task 1 collects Google Play reviews, cleans them, and saves an analysis-ready CSV.

What it does:

- Scrapes app metadata and reviews with `google-play-scraper`
- Removes duplicate reviews
- Drops missing review text or rating values
- Normalizes dates to `YYYY-MM-DD`
- Saves the cleaned dataset as `notebooks/data/processed/ethiopian_bank_reviews_clean.csv`

Main notebook:

- [notebooks/task1_scraping_preprocessing.ipynb](notebooks/task1_scraping_preprocessing.ipynb)

Output columns:

- `review`
- `rating`
- `date`
- `bank`
- `source`

## Task 2: Sentiment and Thematic Analysis

Task 2 loads the cleaned Task 1 output and enriches it with sentiment labels, confidence scores, and themes.

What it does:

- Applies VADER sentiment scoring
- Compares VADER/TextBlob with optional Transformer sentiment
- Extracts TF-IDF keywords and n-grams
- Maps recurring review patterns into business themes such as Stability, Account, UX, Features, and Performance
- Aggregates sentiment by bank and by star rating
- Saves the Task 2 output CSV as `data/processed/fintech_sentiment_analysis_results.csv`

Main notebook:

- [notebooks/task2_sentiment_thematic_analysis.ipynb](notebooks/task2_sentiment_thematic_analysis.ipynb)

Task 2 output schema:

- `review_id`
- `review_text`
- `sentiment_label`
- `sentiment_score`
- `identified_theme`

## Repository Structure

- `data/` - generated data artifacts
- `notebooks/` - analysis notebooks
- `scripts/` - reusable scripts
- `src/` - source code package
- `tests/` - automated tests

## How to Run

Activate the virtual environment, then open the notebooks in order.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\venv\Scripts\Activate.ps1
```

Then run Task 1 first, followed by Task 2.

## Notes

- The repository keeps generated CSV files out of version control via `.gitignore`.
- Transformer sentiment in Task 2 is optional and may download model weights on first run.
- The cleaned data currently contains 1,135 reviews total across the three banks.

## Deliverables

- Cleaned review dataset for downstream analysis
- Sentiment comparison and theme extraction notebook
- Analysis-ready CSV for reporting and visualization
