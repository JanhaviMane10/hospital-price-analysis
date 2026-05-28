# ============================================================
# config.py — Hospital Price Transparency Analysis
# ============================================================

import os

# --- Paths ---
DATA_DIR    = "data"
OUTPUT_DIR  = "outputs"

for folder in [DATA_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

# --- Focus area ---
TARGET_STATE = "AZ"   # Arizona (ASU is in Arizona)
TARGET_CITY  = "Phoenix"

# --- The 14 CMS shoppable services we analyze ---
# These are procedures CMS requires hospitals to post prices for
CMS_SHOPPABLE_SERVICES = {
    "70553": "MRI Brain with Contrast",
    "71250": "CT Chest",
    "74177": "CT Abdomen & Pelvis",
    "93000": "Electrocardiogram (ECG)",
    "85025": "Complete Blood Count (CBC)",
    "80053": "Comprehensive Metabolic Panel",
    "36415": "Blood Draw",
    "99213": "Office Visit (Established Patient)",
    "99283": "Emergency Dept Visit (Moderate)",
    "27447": "Total Knee Replacement",
    "27130": "Total Hip Replacement",
    "43239": "Upper GI Endoscopy",
    "45378": "Colonoscopy",
    "59510": "Cesarean Section",
}

# --- Business scenario ---
EMPLOYER_SIZE        = 5000    # employees
ANNUAL_VISITS_PER_EE = 4.2     # average healthcare visits per employee per year
SHOPPABLE_PCT        = 0.30    # % of visits that are shoppable procedures

# --- Medicare baseline rates (2024, approximate) ---
MEDICARE_RATES = {
    "70553": 446,    # MRI Brain
    "71250": 312,    # CT Chest
    "74177": 389,    # CT Abdomen
    "93000": 28,     # ECG
    "85025": 11,     # CBC
    "80053": 14,     # Metabolic Panel
    "36415": 3,      # Blood Draw
    "99213": 115,    # Office Visit
    "99283": 186,    # ED Visit
    "27447": 1600,   # Knee Replacement
    "27130": 1545,   # Hip Replacement
    "43239": 612,    # Upper GI Endoscopy
    "45378": 492,    # Colonoscopy
    "59510": 2100,   # C-Section
}
