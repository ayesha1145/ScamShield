# Database Seeding Guide

## Purpose
Database seeding populates ScamShield with initial reference data such as:
- Common scam keywords and patterns
- Known fraudulent URLs or phone numbers
- Benchmark data for testing the AI detection model

## Steps
1. **Connect to MongoDB** using the URL in your `.env` file.
2. Run a seeding script (to be added) that inserts sample records.
3. Verify the data appears in the `blacklist` and `patterns` collections.
4. Use the `/stats` endpoint to confirm totals.

## Example
```bash
python backend/utils/db_seed_preview.py


