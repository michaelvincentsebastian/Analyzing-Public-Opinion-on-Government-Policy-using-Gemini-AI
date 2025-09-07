import gspread
import pandas as pd

# ==== CONFIG ====
CREDENTIALS_PATH = "script/credentials.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1D0vJKgS5tj38mYEff97mGi8_bWGMG_LBkfIE59HTK-A/edit?usp=sharing"
SOURCE_SHEET_NAME = "Clean"
OUTPUT_SHEET_NAME = "Output"
# =====================

# Setup Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_url(SPREADSHEET_URL)
ws_clean = sh.worksheet(SOURCE_SHEET_NAME)
ws_output = sh.worksheet(OUTPUT_SHEET_NAME)

# Get all data from Clean
rows = ws_clean.get_all_records()
df = pd.DataFrame(rows)

if "sentiment" not in df.columns:
    print("⚠️ Column 'sentiment' not found in sheet Clean.")
    exit()

# Count sentiment totals
counts = df["sentiment"].value_counts().to_dict()

# Ensure all categories are present
summary = {
    "positive": counts.get("positive", 0),
    "neutral": counts.get("neutral", 0),
    "negative": counts.get("negative", 0),
    "unclassified": counts.get("unclassified", 0),
    "error": counts.get("error", 0)
}

print("📊 Sentiment Summary:", summary)

# Update to Output worksheet
ws_output.clear()
ws_output.update(
    [["Sentiment", "Total"]] +
    [[k, v] for k, v in summary.items()]
)

print("✅ Sentiment summary successfully written to sheet 'Output'.")
