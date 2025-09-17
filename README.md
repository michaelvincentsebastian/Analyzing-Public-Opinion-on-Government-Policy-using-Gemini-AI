# Sentiment Analysis Pipeline with Google Sheets + Gemini API

## 📌 Overview

### This project is a simple pipeline for performing **sentiment analysis** on TikTok comments in Indonesian.

Tiktok Comments scrapped from -> [Tiktok URL List](tiktok-url-list.txt)

It combines:

- **Apify** (for scraping TikTok comments),
- **Google Sheets** (as the data hub),
- **Gemini API** (for sentiment classification).

👉 [View Dataset Here](https://docs.google.com/spreadsheets/d/1D0vJKgS5tj38mYEff97mGi8_bWGMG_LBkfIE59HTK-A/edit?usp=sharing)

---

## 📂 Project Structure

```text
📦 Analyzing-Public-Opinion-on-Government-Policy-using-Gemini-AI
 ┣ 📂script
 ┃ ┣ 📜cleaning.py
 ┃ ┣ 📜credentials.json
 ┃ ┣ 📜main.py
 ┃ ┗ 📜summary.py
 ┣ 📜.env
 ┣ 📜.gitattributes
 ┣ 📜.gitignore
 ┣ 📜accounts.db
 ┣ 📜README.md
 ┗ 📜tiktok-url-list.txt
```

---

## 🔄 Workflow

1. **Data Collection (Apify → CSV → Google Sheets)**
   - Extract TikTok comments using [Apify TikTok Scraper](https://apify.com/apify/tiktok-scraper).
   - Download the scraped data as a **CSV file**.
   - Upload the CSV file into **Google Sheets**, worksheet: `Clean`.

2. **Data Cleaning (`cleaning.py`)**
   - Make a worksheet for cleaned data (`Clean`)
   - Run Cleaning Function that:
     1. Remove emoticons (non-ASCII) with `encode("ascii", "ignore")` and `decode()`
     2. Lowercase the comments with `lower()`
     3. Remove whitespace at the beginning and end of comments with `strip()`
     4. Remove specific symbols such as `@ # % * _ -` using regex:  
        ```python
        re.sub(r"[@#%*_\-]", " ", text)
        ```
     5. Remove mentions starting with `@` using regex:  
        ```python
        re.sub(r"@\S+", "", text)
        ```
     6. Remove multiple spaces with regex:  
        ```python
        re.sub(r"\s+", " ", text)
        ```
   - Make a new column `cleaned_text` to store the cleaned comments
   - Write results to worksheet `Clean` by replacing it if already exists

3. **Sentiment Classification (`main.py`)**
   - Reads `cleaned_text` from the `Clean` worksheet.
   - Sends each comment to **Gemini** via **API Key** for sentiment classification (`positive`, `neutral`, `negative`).
   - Writes the resulting sentiment label back into the same worksheet under the `sentiment` column.

4. **Summarizing (`summary.py`)**
   - Counts the total number of each sentiment label (`positive`, `neutral`, `negative`, `unclassified`, `error`).
   - Updates the summary into the `Output` worksheet and prints it in the console/log.

---

## 🛠 Tools & Setup

- **Python 3.10+**
- **Libraries:**
  - `gspread` → Google Sheets access
  - `google-generativeai` → Gemini API access
  - `pandas` → data handling
  - `python-dotenv` → environment variables
- **Apify** → data extraction from TikTok
- **Google Cloud Service Account** → authentication with `credentials.json`
- **.env file** → store Gemini API key securely

### Example `.env`:
```bash
GEMINI_API_KEY=your_api_key_here
```

---

## ⚠️ Limitations

1. Gemini API Quota
    - Free-tier limit: 200 requests/day.
    - Example: if 13 are used for testing, the remaining quota is 187.
    - Retries or failed requests also consume quota.

2. Rate Limit
    - Free-tier allows max 15 requests/minute.
    - Script uses time.sleep(5) to avoid hitting this limit.

3. Unclassified Outputs
    - Sometimes Gemini returns invalid or non-JSON responses.
    - Script marks them as unclassified.

4. External Dependencies
    - Relies on Apify (scraping) and Google Sheets API (data handling).
    - Any downtime or quota issues will break the pipeline.

---

## ▶️ Quick Start

1. Install dependencies: 
    pip install -r requirements.txt

2. Run sentiment classification:
    python main.py

3. Generate summary:
    python summary.py

---

## 📊 Example Output

### After running summary.py, you will see something like:
Sentiment     Total
positive      18
neutral       29
negative      81
unclassified  55
error         0

### Pie Chart for the Data Distribution:
![Sentiment Distribution](sentiment-distribution.png)

---
