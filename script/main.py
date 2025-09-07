import gspread
import google.generativeai as genai
import json
import time
import os
from dotenv import load_dotenv

# ==== CONFIG ====
CREDENTIALS_PATH = "script/credentials.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1D0vJKgS5tj38mYEff97mGi8_bWGMG_LBkfIE59HTK-A/edit?usp=sharing"
SOURCE_SHEET_NAME = "Clean"
MODEL_NAME = "gemini-2.0-flash"
# ======================

# Load .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY not found in .env")

# Setup Gemini API
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# Setup Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_url(SPREADSHEET_URL)
worksheet = sh.worksheet(SOURCE_SHEET_NAME)

# Read all data
rows = worksheet.get_all_records()
headers = worksheet.row_values(1)

print("Columns detected:", headers)

# Add sentiment column if missing
if "sentiment" not in headers:
    worksheet.update_cell(1, len(headers) + 1, "sentiment")
    headers.append("sentiment")

# Find index of sentiment column
sentiment_idx = headers.index("sentiment") + 1

# Iterate each row
for i, row in enumerate(rows, start=2):  # start=2 since row 1 is header
    cleaned_text = row.get("cleaned_text", "").strip()
    if not cleaned_text:
        continue

    # Skip if sentiment already exists
    if row.get("sentiment", "").strip():
        continue

    # Prompt context
    prompt = f"""
You are a sentiment classification model for Indonesian text.
Some comments may include slang, abbreviations, or unique words,
but classify based on the main meaning.

Your task: provide exactly 1 label from the following list:
- "positive"
- "neutral"
- "negative"

Text: "{cleaned_text}"

Answer only in JSON format:
{{"label": "positive"}}
"""

    try:
        response = model.generate_content(prompt)
        raw_output = response.text.strip()

        print(f"\nDEBUG row {i-1}")
        print("cleaned_text:", cleaned_text)
        print("raw response:", raw_output)

        # Safe JSON parsing
        sentiment = "unclassified"
        try:
            data = json.loads(raw_output)
            if "label" in data:
                sentiment = data["label"].lower().strip()
        except json.JSONDecodeError:
            pass

        print("final label:", sentiment)

        # Update sheet
        worksheet.update_cell(i, sentiment_idx, sentiment)

        # Avoid rate limit (free tier max 15 req/min)
        time.sleep(5)

    except Exception as e:
        print(f"❌ Error at row {i}: {e}")
        worksheet.update_cell(i, sentiment_idx, "error")
        time.sleep(5)

print("✅ Classification completed. Results written to sheet 'Clean'.")
