# ============================================================
# 03_tableau_prep.py — Prepare files for Tableau Dashboard
#
# WHAT THIS FILE DOES:
# Creates clean, Tableau-optimized CSV files and prints
# step-by-step instructions for building the dashboard.
# ============================================================

import pandas as pd
import numpy as np
import sqlite3
import warnings
warnings.filterwarnings("ignore")

from config import *

DB_PATH = f"{OUTPUT_DIR}/hospital_prices.db"
conn    = sqlite3.connect(DB_PATH)

print("📊 Preparing Tableau-ready files...\n")

# ── File 1: Main price data for Tableau ──────────────────────
main_df = pd.read_sql("""
SELECT
    p.hospital_name,
    p.city,
    p.state,
    h.hospital_ownership,
    h.overall_rating,
    p.cpt_code,
    p.procedure_name,
    p.payer,
    p.gross_charge,
    p.cash_price,
    p.negotiated_rate,
    p.medicare_rate,
    p.markup_vs_medicare,
    CASE
        WHEN p.payer IN ('Medicare','Medicaid/AHCCCS') THEN 'Government'
        WHEN p.payer = 'Cash/Self-Pay' THEN 'Cash'
        ELSE 'Commercial'
    END as payer_type,
    CASE
        WHEN p.markup_vs_medicare < 1.5 THEN '1: Low (<1.5x Medicare)'
        WHEN p.markup_vs_medicare < 2.5 THEN '2: Mid (1.5-2.5x Medicare)'
        WHEN p.markup_vs_medicare < 3.5 THEN '3: High (2.5-3.5x Medicare)'
        ELSE '4: Very High (>3.5x Medicare)'
    END as price_tier
FROM prices p
JOIN hospitals h ON p.provider_id = h.provider_id
""", conn)

main_df.to_csv(f"{OUTPUT_DIR}/tableau_main.csv", index=False)
print(f"✅ tableau_main.csv — {len(main_df):,} rows")

# ── File 2: Hospital scorecard for Tableau ───────────────────
scorecard_df = pd.read_sql("""
SELECT
    p.hospital_name,
    p.city,
    h.hospital_ownership,
    h.overall_rating,
    ROUND(AVG(CASE WHEN p.payer NOT IN ('Medicare','Medicaid/AHCCCS','Cash/Self-Pay')
              THEN p.negotiated_rate END), 0) as avg_commercial_rate,
    ROUND(AVG(CASE WHEN p.payer NOT IN ('Medicare','Medicaid/AHCCCS','Cash/Self-Pay')
              THEN p.markup_vs_medicare END), 2) as avg_markup,
    ROUND(AVG(CASE WHEN p.payer = 'Cash/Self-Pay'
              THEN p.negotiated_rate END), 0) as avg_cash_price,
    COUNT(DISTINCT p.cpt_code) as procedures_posted,
    CASE
        WHEN AVG(CASE WHEN p.payer NOT IN ('Medicare','Medicaid/AHCCCS','Cash/Self-Pay')
                 THEN p.markup_vs_medicare END) < 2.0
             AND h.overall_rating >= 4 THEN 'Best Value'
        WHEN AVG(CASE WHEN p.payer NOT IN ('Medicare','Medicaid/AHCCCS','Cash/Self-Pay')
                 THEN p.markup_vs_medicare END) < 2.0 THEN 'Lowest Price'
        WHEN h.overall_rating >= 4 THEN 'High Quality'
        ELSE 'Average'
    END as recommendation
FROM prices p
JOIN hospitals h ON p.provider_id = h.provider_id
GROUP BY p.hospital_name, p.city, h.hospital_ownership, h.overall_rating
ORDER BY avg_markup ASC
""", conn)

scorecard_df.to_csv(f"{OUTPUT_DIR}/tableau_scorecard.csv", index=False)
print(f"✅ tableau_scorecard.csv — {len(scorecard_df)} hospitals")

# ── File 3: Employer savings model ───────────────────────────
savings_df = pd.read_sql("""
WITH avg_prices AS (
    SELECT cpt_code, procedure_name,
           AVG(negotiated_rate) as current_avg
    FROM prices
    WHERE payer NOT IN ('Medicare','Medicaid/AHCCCS','Cash/Self-Pay')
    GROUP BY cpt_code, procedure_name
),
low_prices AS (
    SELECT cpt_code,
           AVG(negotiated_rate) as smart_avg
    FROM (
        SELECT cpt_code, negotiated_rate,
               NTILE(4) OVER (PARTITION BY cpt_code ORDER BY negotiated_rate) as q
        FROM prices
        WHERE payer NOT IN ('Medicare','Medicaid/AHCCCS','Cash/Self-Pay')
    ) WHERE q = 1
    GROUP BY cpt_code
)
SELECT
    a.cpt_code,
    a.procedure_name,
    ROUND(a.current_avg, 0) as current_avg_price,
    ROUND(l.smart_avg, 0) as smart_avg_price,
    ROUND(a.current_avg - l.smart_avg, 0) as savings_per_case,
    ROUND((a.current_avg - l.smart_avg) / a.current_avg * 100, 1) as savings_pct
FROM avg_prices a
JOIN low_prices l ON a.cpt_code = l.cpt_code
ORDER BY savings_per_case DESC
""", conn)

savings_df.to_csv(f"{OUTPUT_DIR}/tableau_savings.csv", index=False)
print(f"✅ tableau_savings.csv — {len(savings_df)} procedures")

conn.close()

# ── Print Tableau instructions ────────────────────────────────
print("""
╔══════════════════════════════════════════════════════════════╗
║          TABLEAU DASHBOARD BUILD INSTRUCTIONS               ║
╚══════════════════════════════════════════════════════════════╝

FILES TO IMPORT INTO TABLEAU:
  outputs/tableau_main.csv        ← Main data source
  outputs/tableau_scorecard.csv   ← Hospital scorecard
  outputs/tableau_savings.csv     ← Employer savings

YOUR DASHBOARD HAS 5 SHEETS + 1 DASHBOARD:

────────────────────────────────────────────────────────────────
SHEET 1: "MRI Price Strip Plot" (The Hero Visual)
────────────────────────────────────────────────────────────────
Data source: tableau_main.csv
Filter: cpt_code = 70553 AND payer_type = Commercial

Drag to:
  Columns: negotiated_rate (AVG)
  Rows: hospital_name
  Color: price_tier

Add reference line: Average → constant value → 446 (Medicare)
Title: "MRI Brain: Same Procedure, $X to $Y Across AZ Hospitals"
Sort: by avg negotiated_rate ascending

────────────────────────────────────────────────────────────────
SHEET 2: "Hospital Scorecard" (The Main Table)
────────────────────────────────────────────────────────────────
Data source: tableau_scorecard.csv

Drag to:
  Rows: hospital_name, city
  Columns: avg_markup, avg_commercial_rate, overall_rating, recommendation
  Color: avg_markup (diverging, green=low, red=high)

Format as a highlight table / text table
Add conditional formatting: recommendation column colored by value

────────────────────────────────────────────────────────────────
SHEET 3: "Payer Comparison" (Who Gets Best Deal?)
────────────────────────────────────────────────────────────────
Data source: tableau_main.csv
Filter: cpt_code = 70553 (MRI as example)

Drag to:
  Columns: payer
  Rows: negotiated_rate (AVG)
  Color: payer_type

Sort by negotiated_rate ascending
Add reference line at Medicare rate (446)

────────────────────────────────────────────────────────────────
SHEET 4: "Procedure Variation Heatmap"
────────────────────────────────────────────────────────────────
Data source: tableau_main.csv
Filter: payer_type = Commercial

Drag to:
  Columns: procedure_name
  Rows: hospital_name
  Color: markup_vs_medicare (sequential blue)

This creates a heatmap showing which hospital × procedure combos are expensive

────────────────────────────────────────────────────────────────
SHEET 5: "Employer Savings Calculator"
────────────────────────────────────────────────────────────────
Data source: tableau_savings.csv

Drag to:
  Rows: procedure_name
  Columns: savings_per_case (bar), current_avg_price, smart_avg_price
  Color: savings_pct

Add a parameter: "Number of Employees" (integer, default 5000)
Create calculated field: [savings_per_case] * [Number of Employees] * 0.012
(0.012 = avg shoppable visits per employee per year)

This makes the dashboard interactive — employers can slide to their size!

────────────────────────────────────────────────────────────────
DASHBOARD LAYOUT:
────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│  HEADLINE: "AZ hospitals charge up to Xx more than Medicare │
│  for the same procedure. Here's how to save $X,XXX,XXX."   │
├──────────────────────────┬──────────────────────────────────┤
│   Sheet 1: MRI Strip     │    Sheet 2: Hospital Scorecard  │
│   Plot (hero visual)     │    (filterable table)            │
├──────────────────────────┴──────────────────────────────────┤
│   Sheet 4: Heatmap (procedure × hospital)                   │
├──────────────────────────┬──────────────────────────────────┤
│   Sheet 3: Payer         │    Sheet 5: Employer Savings     │
│   Comparison             │    Calculator (interactive)      │
└──────────────────────────┴──────────────────────────────────┘

FILTERS TO ADD TO DASHBOARD:
  - City (multi-select)
  - Procedure (dropdown)
  - Payer (dropdown)
  - Hospital Rating (slider, 1-5)

────────────────────────────────────────────────────────────────
PUBLISH TO TABLEAU PUBLIC:
────────────────────────────────────────────────────────────────
  1. File → Save to Tableau Public As...
  2. Create a free account at public.tableau.com
  3. Your dashboard will get a public URL like:
     public.tableau.com/views/HospitalPriceTransparencyArizona/...
  4. Add this URL to your resume and LinkedIn!
""")

print("✅ Done! Open Tableau and follow the instructions above.")
print(f"   All CSV files are in: {OUTPUT_DIR}/")
