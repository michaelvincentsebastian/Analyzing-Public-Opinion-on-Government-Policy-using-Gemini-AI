import gspread
import google.generativeai as genai
import json
import time
import os
import re
from dotenv import load_dotenv

# ==== SETUP ====
CREDENTIALS_PATH = "script/credentials.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1D0vJKgS5tj38mYEff97mGi8_bWGMG_LBkfIE59HTK-A/edit?usp=sharing"
SOURCE_SHEET_NAME = "Clean"
MODEL_NAME = "gemini-2.0-flash"
DEBUG_MODE = True  # 🔑 False = hanya tulis ke Sheets, True = print reasoning di console

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

    # Prompt dengan konteks (RAG-style knowledge base)
    prompt = f"""
You are an AI trained to classify public comments into sentiment categories 
(positive, neutral, negative) with awareness of sarcasm, slang, and political context.

To improve accuracy, use the following knowledge base of unusual, sarcastic, or foreign phrases: 

[KONTEKS KATA/PHRASE]
- "Gw takut dia kek Munir" → Kekhawatiran bahwa seseorang akan bernasib seperti Munir (aktivis HAM yang diracun). Nada: serius, negatif.
- "please god protect all the people who fight for justice" → Permohonan tulus, empati. Nada: positif.
- "Pasti mau dikasi kerdus isi indomie" → Sarkasme terhadap bantuan yang dianggap remeh. Nada: negatif.
- "Dulu kita sering lihat petinggi negara makan di warung sederhana" → Sindiran bahwa pejabat sekarang tidak merakyat. Nada: negatif.
- "Gak sekalian bikin partai??" → Sarkastik, menuduh terlalu politis. Nada: negatif.
- "terimakasih orang baik" → Bisa tulus (positif) atau sarkas (negatif) tergantung konteks.
- "Nanti ada yg bilang 'itu hoaks'" → Prediksi sinis, nada negatif.
- "kok kayak akting ya, muka tegang amat" → Meragukan ketulusan, sindiran. Nada: negatif.
- "sehat selalu orang2 yg benar2 berjuang" → Dukungan tulus, nada positif.

TASK:
1. Jika ada komentar yang mengandung frasa di knowledge base, gunakan arti dan konteksnya untuk klasifikasi.
2. Jika tidak ada, gunakan analisis sentimen standar berdasarkan bahasa alami.
3. Output dalam format JSON ketat:
{{
  "sentiment": "positive|neutral|negative",
  "reasoning": "short explanation (max 1-2 sentences)"
}}
Only respond with JSON, no explanations outside.

Text: "{cleaned_text}"
"""

    try:
        response = model.generate_content(prompt)
        raw_output = response.text.strip()

        print(f"\nDEBUG row {i-1}")
        print("cleaned_text:", cleaned_text)
        print("raw response:", raw_output)

        # --- CLEANING STEP (Fix triple backticks) ---
        clean_output = raw_output
        if clean_output.startswith("```"):
            clean_output = re.sub(r"^```[a-zA-Z]*\n?", "", clean_output)  # hapus ```json
            clean_output = re.sub(r"```$", "", clean_output).strip()     # hapus penutup ```

        # Safe JSON parsing
        sentiment = "unclassified"
        reasoning = ""
        try:
            data = json.loads(clean_output)
            if "sentiment" in data:
                sentiment = data["sentiment"].lower().strip()
            if "reasoning" in data:
                reasoning = data["reasoning"].strip()
        except json.JSONDecodeError:
            # --- Fallback regex parse ---
            match = re.search(r'"sentiment"\s*:\s*"(\w+)"', clean_output)
            if match:
                sentiment = match.group(1).lower().strip()

        print("final label:", sentiment)
        if DEBUG_MODE and reasoning:
            print("reasoning:", reasoning)

        # Update only sentiment to sheet
        worksheet.update_cell(i, sentiment_idx, sentiment)

        # Avoid rate limit
        time.sleep(5)

    except Exception as e:
        print(f"❌ Error at row {i}: {e}")
        worksheet.update_cell(i, sentiment_idx, "error")
        time.sleep(5)

print("✅ Classification completed. Results written to sheet 'Clean'.")
