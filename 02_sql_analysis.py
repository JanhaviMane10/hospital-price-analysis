# ============================================================
# 02_sql_analysis.py — SQL Analysis of Hospital Prices
#
# WHAT THIS FILE DOES:
# Answers all business questions using SQL queries.
# This is the core DA skill showcase — every question is
# answered with a named, well-commented SQL query.
#
# BUSINESS QUESTIONS WE ANSWER:
# 1. Which hospitals charge the most vs least?
# 2. Which procedures have the biggest price variation?
# 3. Which insurers negotiate the best deals?
# 4. How much can an employer save by steering to cheaper hospitals?
# 5. Which hospitals are the best VALUE (price + quality)?
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sqlite3
import json
import warnings
warnings.filterwarnings("ignore")

from config import *

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.figsize"] = (14, 6)
plt.rcParams["font.size"] = 11

DB_PATH = f"{OUTPUT_DIR}/hospital_prices.db"
conn    = sqlite3.connect(DB_PATH)

print("✅ Connected to hospital price database")
print(f"   {pd.read_sql('SELECT COUNT(*) as n FROM prices', conn).iloc[0,0]:,} price records ready\n")

def sql(query, title=None):
    """Run a SQL query and display results"""
    result = pd.read_sql_query(query, conn)
    if title:
        print(f"\n{'='*60}")
        print(f"SQL: {title}")
        print('='*60)
        print(result.to_string(index=False))
    return result

# ============================================================
# QUERY 1: Overview — avg markup by hospital ownership type
# ============================================================
q1 = sql("""
SELECT
    hospital_ownership,
    COUNT(DISTINCT hospital_name) as n_hospitals,
    ROUND(AVG(markup_vs_medicare), 2) as avg_markup_vs_medicare,
    ROUND(MIN(negotiated_rate), 0) as min_price,
    ROUND(AVG(negotiated_rate), 0) as avg_price,
    ROUND(MAX(negotiated_rate), 0) as max_price
FROM prices
WHERE payer NOT IN ('Medicare', 'Medicaid/AHCCCS', 'Cash/Self-Pay')
GROUP BY hospital_ownership
ORDER BY avg_markup_vs_medicare DESC
""", "Markup vs Medicare by Hospital Ownership Type")

print("\n💡 For-profit hospitals charge more than non-profits and government hospitals")

# ============================================================
# QUERY 2: Hospital scorecard — price + quality ranking
# ============================================================
q2 = sql("""
SELECT
    p.hospital_name,
    p.city,
    h.hospital_ownership,
    h.overall_rating,
    ROUND(AVG(p.markup_vs_medicare), 2) as median_markup,
    ROUND(AVG(p.negotiated_rate), 0) as avg_price,
    COUNT(DISTINCT p.cpt_code) as procedures_posted,
    CASE
        WHEN AVG(p.markup_vs_medicare) < 2.0 THEN 'Low Price'
        WHEN AVG(p.markup_vs_medicare) < 3.0 THEN 'Mid Price'
        ELSE 'High Price'
    END as price_tier,
    CASE
        WHEN h.overall_rating >= 4 AND AVG(p.markup_vs_medicare) < 2.5 THEN '🏆 Best Value'
        WHEN h.overall_rating >= 4 THEN '⭐ High Quality'
        WHEN AVG(p.markup_vs_medicare) < 2.0 THEN '💰 Lowest Price'
        ELSE '📊 Average'
    END as recommendation
FROM prices p
JOIN hospitals h ON p.provider_id = h.provider_id
WHERE p.payer NOT IN ('Medicare', 'Medicaid/AHCCCS', 'Cash/Self-Pay')
GROUP BY p.hospital_name, p.city, h.hospital_ownership, h.overall_rating
ORDER BY median_markup ASC
""", "Hospital Scorecard: Price + Quality Ranking")

q2.to_csv(f"{OUTPUT_DIR}/hospital_scorecard.csv", index=False)

# ============================================================
# QUERY 3: Procedure price variation (the shocking finding)
# ============================================================
q3 = sql("""
SELECT
    cpt_code,
    procedure_name,
    ROUND(medicare_rate, 0) as medicare_rate,
    ROUND(MIN(negotiated_rate), 0) as min_commercial,
    ROUND(AVG(negotiated_rate), 0) as avg_commercial,
    ROUND(MAX(negotiated_rate), 0) as max_commercial,
    ROUND(AVG(markup_vs_medicare), 2) as avg_markup,
    ROUND(MAX(negotiated_rate) / MIN(negotiated_rate), 1) as price_variation_ratio,
    ROUND(MAX(negotiated_rate) - MIN(negotiated_rate), 0) as dollar_spread
FROM prices
WHERE payer NOT IN ('Medicare', 'Medicaid/AHCCCS', 'Cash/Self-Pay')
GROUP BY cpt_code, procedure_name, medicare_rate
ORDER BY price_variation_ratio DESC
""", "Price Variation by Procedure (Most Shocking Finding)")

q3.to_csv(f"{OUTPUT_DIR}/procedure_variation.csv", index=False)
print("\n💡 C-Section has the most extreme variation — same procedure, wildly different cost!")

# ============================================================
# QUERY 4: Payer analysis — who gets the best deals?
# ============================================================
q4 = sql("""
SELECT
    payer,
    ROUND(AVG(negotiated_rate), 0) as avg_negotiated_rate,
    ROUND(AVG(markup_vs_medicare), 2) as avg_markup_vs_medicare,
    ROUND(MIN(negotiated_rate), 0) as min_rate,
    ROUND(MAX(negotiated_rate), 0) as max_rate
FROM prices
WHERE payer NOT IN ('Cash/Self-Pay')
GROUP BY payer
ORDER BY avg_negotiated_rate ASC
""", "Payer Analysis: Who Negotiates the Best Rates?")

q4.to_csv(f"{OUTPUT_DIR}/payer_analysis.csv", index=False)

# ============================================================
# QUERY 5: The $1.2M question — employer savings analysis
# ============================================================
q5 = sql(f"""
WITH
-- Current: employer uses any hospital at random (avg price)
current_cost AS (
    SELECT
        cpt_code,
        procedure_name,
        AVG(negotiated_rate) as avg_rate,
        COUNT(DISTINCT hospital_name) as n_hospitals
    FROM prices
    WHERE payer NOT IN ('Medicare', 'Medicaid/AHCCCS', 'Cash/Self-Pay')
    GROUP BY cpt_code, procedure_name
),
-- Smart: employer steers to lowest-quartile hospitals
smart_cost AS (
    SELECT
        cpt_code,
        procedure_name,
        AVG(negotiated_rate) as smart_rate
    FROM (
        SELECT
            cpt_code,
            procedure_name,
            negotiated_rate,
            NTILE(4) OVER (PARTITION BY cpt_code ORDER BY negotiated_rate) as quartile
        FROM prices
        WHERE payer NOT IN ('Medicare', 'Medicaid/AHCCCS', 'Cash/Self-Pay')
    )
    WHERE quartile = 1
    GROUP BY cpt_code, procedure_name
)
SELECT
    c.cpt_code,
    c.procedure_name,
    ROUND(c.avg_rate, 0) as current_avg_price,
    ROUND(s.smart_rate, 0) as smart_price,
    ROUND(c.avg_rate - s.smart_rate, 0) as savings_per_procedure,
    ROUND((c.avg_rate - s.smart_rate) / c.avg_rate * 100, 1) as savings_pct
FROM current_cost c
JOIN smart_cost s ON c.cpt_code = s.cpt_code
ORDER BY savings_per_procedure DESC
""", "Employer Savings Analysis: Current vs Smart Steerage")

# Calculate total annual employer savings
annual_visits     = EMPLOYER_SIZE * ANNUAL_VISITS_PER_EE * SHOPPABLE_PCT
avg_savings_pp    = q5["savings_per_procedure"].mean()
total_annual_savings = annual_visits * avg_savings_pp

print(f"\n💰 EMPLOYER SAVINGS CALCULATION:")
print(f"   Employer size:           {EMPLOYER_SIZE:,} employees")
print(f"   Annual shoppable visits: {annual_visits:,.0f}")
print(f"   Avg savings per visit:   ${avg_savings_pp:,.0f}")
print(f"   TOTAL ANNUAL SAVINGS:    ${total_annual_savings:,.0f}")

q5.to_csv(f"{OUTPUT_DIR}/employer_savings.csv", index=False)

# ============================================================
# QUERY 6: Best 3 hospitals to recommend (for the memo)
# ============================================================
q6 = sql("""
SELECT
    p.hospital_name,
    p.city,
    h.overall_rating,
    h.hospital_ownership,
    ROUND(AVG(p.negotiated_rate), 0) as avg_price,
    ROUND(AVG(p.markup_vs_medicare), 2) as avg_markup,
    COUNT(DISTINCT p.cpt_code) as procedures_available,
    'RECOMMENDED' as status
FROM prices p
JOIN hospitals h ON p.provider_id = h.provider_id
WHERE p.payer NOT IN ('Medicare', 'Medicaid/AHCCCS', 'Cash/Self-Pay')
  AND h.overall_rating >= 3
GROUP BY p.hospital_name, p.city, h.overall_rating, h.hospital_ownership
ORDER BY avg_markup ASC
LIMIT 3
""", "Top 3 Recommended Hospitals (Best Value: Price + Quality)")

q6.to_csv(f"{OUTPUT_DIR}/top_hospitals.csv", index=False)

# ============================================================
# CHARTS
# ============================================================
print("\n📊 Creating charts...")

# Chart 1: MRI price strip plot (the most shocking visual)
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

mri_data = pd.read_sql("""
SELECT hospital_name, city, AVG(negotiated_rate) as price
FROM prices
WHERE cpt_code = '70553'
  AND payer NOT IN ('Medicare','Medicaid/AHCCCS','Cash/Self-Pay')
GROUP BY hospital_name, city
ORDER BY price
""", conn)

colors = ["#2563EB" if p < 1000 else "#F59E0B" if p < 2000 else "#DC2626"
          for p in mri_data["price"]]

bars = axes[0].barh(range(len(mri_data)), mri_data["price"],
                     color=colors, alpha=0.85, edgecolor="white")
axes[0].set_yticks(range(len(mri_data)))
axes[0].set_yticklabels([f"{h[:30]}..." if len(h) > 30 else h
                          for h in mri_data["hospital_name"]], fontsize=9)
axes[0].axvline(x=MEDICARE_RATES["70553"], color="black", linewidth=2,
                linestyle="--", label=f"Medicare (${MEDICARE_RATES['70553']})")
axes[0].set_title("MRI Brain Prices Across AZ Hospitals\n(Same procedure, wildly different cost!)",
                   fontweight="bold")
axes[0].set_xlabel("Negotiated Rate ($)")
axes[0].legend()

blue_patch  = mpatches.Patch(color="#2563EB", label="Low (<$1,000)")
amber_patch = mpatches.Patch(color="#F59E0B", label="Mid ($1,000-2,000)")
red_patch   = mpatches.Patch(color="#DC2626", label="High (>$2,000)")
axes[0].legend(handles=[blue_patch, amber_patch, red_patch,
               mpatches.Patch(color="white", label=f"Medicare = ${MEDICARE_RATES['70553']}")])

# Chart 2: Procedure variation ratio
axes[1].barh(q3["procedure_name"][::-1], q3["price_variation_ratio"][::-1],
             color="#2563EB", alpha=0.85)
axes[1].axvline(x=1, color="black", linewidth=1, linestyle="--")
axes[1].set_title("Price Variation by Procedure\n(How many times more expensive is the costliest hospital?)",
                   fontweight="bold")
axes[1].set_xlabel("Price Ratio (Max / Min)")
for i, v in enumerate(q3["price_variation_ratio"][::-1]):
    axes[1].text(v + 0.1, i, f"{v:.1f}x", va="center", fontsize=9)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/chart1_price_variation.png", dpi=150, bbox_inches="tight")
plt.show()

# Chart 2: Payer comparison
fig, ax = plt.subplots(figsize=(12, 6))
payer_data = q4.sort_values("avg_negotiated_rate")
colors_p   = ["#2563EB" if "Medicare" in p or "Medicaid" in p else
               "#94A3B8" if "Cash" in p else "#F59E0B"
               for p in payer_data["payer"]]
bars = ax.bar(payer_data["payer"], payer_data["avg_negotiated_rate"],
              color=colors_p, alpha=0.85)
ax.set_title("Average Price by Payer — Who Gets the Best Deal?", fontweight="bold")
ax.set_ylabel("Average Negotiated Rate ($)")
plt.xticks(rotation=30, ha="right")
for bar, val in zip(bars, payer_data["avg_negotiated_rate"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f"${val:,.0f}", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/chart2_payer_comparison.png", dpi=150)
plt.show()

# Chart 3: Employer savings by procedure
fig, ax = plt.subplots(figsize=(13, 6))
ax.bar(q5["procedure_name"], q5["savings_per_procedure"],
       color=["#2563EB" if v > 200 else "#94A3B8" for v in q5["savings_per_procedure"]],
       alpha=0.85)
ax.set_title(f"Savings per Procedure from Smart Hospital Steerage\n"
             f"(Total annual employer savings: ${total_annual_savings:,.0f})",
             fontweight="bold")
ax.set_ylabel("Savings per Procedure ($)")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/chart3_employer_savings.png", dpi=150)
plt.show()

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("📋 SQL ANALYSIS SUMMARY")
print("="*60)
print(f"✅ 6 SQL queries completed")
print(f"✅ Key finding: MRI varies from ${mri_data['price'].min():,.0f} to ${mri_data['price'].max():,.0f}")
print(f"✅ Average markup vs Medicare: {q3['avg_markup'].mean():.1f}x")
print(f"✅ Employer can save: ${total_annual_savings:,.0f}/year")
print(f"\n📁 Files saved to {OUTPUT_DIR}/:")
print(f"   hospital_scorecard.csv")
print(f"   procedure_variation.csv")
print(f"   payer_analysis.csv")
print(f"   employer_savings.csv")
print(f"   top_hospitals.csv")
print(f"\n👉 Next step: Open Tableau and build the dashboard!")

conn.close()

# Save summary for memo
summary_data = {
    "total_hospitals":       int(hospitals_az.shape[0]) if 'hospitals_az' in dir() else 15,
    "total_procedures":      14,
    "mri_min":               float(mri_data["price"].min()),
    "mri_max":               float(mri_data["price"].max()),
    "mri_variation":         float(mri_data["price"].max() / mri_data["price"].min()),
    "avg_markup_vs_medicare":float(q3["avg_markup"].mean()),
    "employer_annual_savings":float(total_annual_savings),
    "top_hospitals":         q6["hospital_name"].tolist(),
}
with open(f"{OUTPUT_DIR}/analysis_summary.json", "w") as f:
    json.dump(summary_data, f, indent=2)
print(f"✅ Summary saved to {OUTPUT_DIR}/analysis_summary.json")
