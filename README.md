# 🏥 AZ Hospital Price Transparency Dashboard
### SQL + Python + Tableau | 15 Hospitals | 14 CMS Procedures

[![Python](https://img.shields.io/badge/Python-3.x-blue)](https://python.org)
[![Tableau](https://img.shields.io/badge/Tableau-Live%20Dashboard-orange)](https://public.tableau.com/app/profile/janhavi.mane/viz/AZHospitalPriceTransparencyDashboard/Dashboard1)
[![SQL](https://img.shields.io/badge/SQL-SQLite-green)]()

🔗 **[Live Tableau Dashboard](https://public.tableau.com/app/profile/janhavi.mane/viz/AZHospitalPriceTransparencyDashboard/Dashboard1)**

---

## 📋 Project Overview

The same MRI scan can cost $500 at one Arizona hospital and $3,000 at another — for the exact same patient. The U.S. government recently required hospitals to publish their prices publicly. This project analyzes that data to answer a concrete business question:

> **If a 5,000-employee self-insured employer in Arizona steered members to lower-cost hospitals, how much would they save annually?**

**Answer: $1M+**

---

## 🔍 Key Findings

| Finding | Value |
|---|---|
| Hospitals analyzed | 15 Arizona hospitals |
| Procedures analyzed | 14 CMS shoppable services |
| Max price variation (same procedure) | 3x |
| Avg commercial vs Medicare rate | 254% |
| Potential employer annual savings | $1M+ |
| Most variable procedure | Cesarean Section |
| Best value hospital | Yuma Regional Medical Center |

---

## 📊 Dashboard Features

The Tableau dashboard has 5 interactive sheets:

1. **MRI Price Strip Plot** — hero visual showing price variation across hospitals
2. **Hospital Scorecard** — ranked table with markup vs Medicare + quality rating + value score
3. **Payer Comparison** — who negotiates the best rates?
4. **Procedure × Hospital Heatmap** — full matrix of all 14 procedures × 15 hospitals
5. **Employer Savings Calculator** — interactive slider for company size → real-time savings

---

## 🗂️ Repository Structure

```
hospital-price-analysis/
├── config.py              ← Settings + Medicare baseline rates
├── 01_get_data.py         ← Download + generate hospital price data
├── 02_sql_analysis.py     ← 6 SQL queries answering business questions
├── 03_tableau_prep.py     ← Generate Tableau-ready CSV files
├── requirements.txt
└── outputs/
    ├── hospital_prices.db      ← SQLite database
    ├── tableau_main.csv        ← Main Tableau data source
    ├── tableau_scorecard.csv   ← Hospital scorecard
    ├── tableau_savings.csv     ← Employer savings model
    ├── hospital_scorecard.csv
    ├── procedure_variation.csv
    └── analysis_summary.json
```

---

## 🚀 How to Run

```bash
git clone https://github.com/JanhaviMane10/hospital-price-analysis.git
cd hospital-price-analysis
pip install -r requirements.txt

python 01_get_data.py       # Download + generate data
python 02_sql_analysis.py   # Run SQL analysis + charts
python 03_tableau_prep.py   # Generate Tableau CSV files

# Then open Tableau and connect to outputs/tableau_main.csv
```

---

## 🛠️ SQL Queries

The analysis answers 6 business questions using SQL:

1. **Ownership type analysis** — do for-profit hospitals charge more?
2. **Hospital scorecard** — price + quality ranking for all 15 hospitals
3. **Procedure variation** — which procedures have the most price variation?
4. **Payer analysis** — which insurers negotiate the best deals?
5. **Employer savings** — current vs smart steerage costs
6. **Best 3 hospitals** — top recommendations combining price + quality

---

## 💡 Business Recommendation

Based on the analysis, a 5,000-employee self-insured employer should:

1. **Steer elective procedures** to the bottom quartile hospitals
2. **Focus on high-variation procedures** — C-sections, knee/hip replacements, endoscopies
3. **Renegotiate payer contracts** — significant variation in negotiated rates across insurers
4. **Projected savings: $1M+ annually**

---

## 📌 Data Notes

- Price data uses RAND-validated commercial rate distributions (commercial rates avg 254% of Medicare per RAND 2022)
- 15 real Arizona hospitals with authentic ownership/rating data
- 14 CMS-mandated shoppable services with real Medicare baseline rates

---

## 🔧 Technologies

`Python` `SQL` `SQLite` `pandas` `matplotlib` `Tableau Public`
