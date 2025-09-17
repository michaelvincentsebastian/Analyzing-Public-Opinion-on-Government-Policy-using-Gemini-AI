import re
import gspread
import pandas as pd

# --- Connect to Google Sheets ---
gc = gspread.service_account(filename='script/credentials.json')
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1D0vJKgS5tj38mYEff97mGi8_bWGMG_LBkfIE59HTK-A/edit?usp=sharing'
sh = gc.open_by_url(spreadsheet_url)

# --- Get data from worksheet "Raw" ---
worksheet = sh.worksheet("Raw")  
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- Cleaning function for comments ---
def clean_comment(text):
    if not isinstance(text, str):
        return ""
    # 1. Remove emoticons (non-ASCII)
    text = text.encode("ascii", "ignore").decode()
    # 2. Lowercase
    text = text.lower()
    # 3. Strip leading/trailing spaces
    text = text.strip()
    # 4. Remove specific symbols
    text = re.sub(r"[@#%*_\-]", " ", text)
    # 5. Remove mentions starting with @
    text = re.sub(r"@\S+", "", text)
    # 6. Remove multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# --- Apply cleaning ---
df["cleaned_text"] = df["text"].apply(clean_comment)

# --- Write results to worksheet "Clean" ---
try:
    ws_cleaned = sh.worksheet("Clean")
    sh.del_worksheet(ws_cleaned)  # remove if already exists
except:
    pass

ws_cleaned = sh.add_worksheet(title="Clean", rows=str(len(df)+1), cols=str(len(df.columns)+1))

# Upload cleaned dataframe
ws_cleaned.update([df.columns.values.tolist()] + df.values.tolist())

print("✅ Cleaning completed & results written to worksheet 'Cleaned'")
