import os
import google.generativeai as genai
import gspread
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- 1. Konfigurasi dan Otentikasi ---
load_dotenv()
api_key = os.getenv("GEMINI_AI_API_KEY")
genai.configure(api_key=api_key)

gc = gspread.service_account(filename='script/credentials.json')
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1D0vJKgS5tj38mYEff97mGi8_bWGMG_LBkfIE59HTK-A/edit?usp=sharing'
sh = gc.open_by_url(spreadsheet_url)
worksheet = sh.worksheet("Sheet1")

# --- 2. Fungsi Klasifikasi Sentimen ---
def klasifikasi_sentimen(teks):
    prompt = f"""
    Klasifikasikan sentimen dari teks berikut.
    Hanya berikan satu kata sebagai jawaban: Positif, Negatif, atau Netral.

    Teks: "{teks}"
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        sentimen = response.text.strip()
        if sentimen in ["Positif", "Negatif", "Netral"]:
            return sentimen
        else:
            return "Tidak Diketahui"
    except Exception as e:
        print(f"Error saat mengklasifikasi: {e}")
        return "Gagal"

# --- 3. Proses Scraping, Analisis, dan Penyimpanan ---
def jalankan_analisis():
    keyword = "demo DPR"
    url_pencarian = f'https://www.detik.com/search/searchall?query={keyword}'
    headers = {"User-Agent": "Mozilla/5.0"}

    print(f"Memulai scraping berita dengan keyword '{keyword}' dari Detik.com...")

    try:
        response = requests.get(url_pencarian, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Coba selector terbaru
        artikel_links = soup.select("article.list-content__item")

        scraped_texts = []
        for artikel in artikel_links:
            judul_tag = artikel.select_one("a.media__link")
            ringkasan_tag = artikel.select_one("p.media__snippet")

            if judul_tag and ringkasan_tag:
                judul = judul_tag.get_text(strip=True)
                ringkasan = ringkasan_tag.get_text(strip=True)
                scraped_texts.append(judul + " " + ringkasan)

        # Fallback kalau tidak ada data
        if not scraped_texts:
            print("⚠️ Tidak ada artikel yang ditemukan dengan selector default.")
            print("Menampilkan potongan HTML untuk debug (cek class terbaru di browser):\n")
            print(soup.prettify()[:2000])  # tampilkan 2000 karakter pertama
            return

    except requests.exceptions.RequestException as e:
        print(f"Error saat terhubung ke web: {e}")
        return

    df = pd.DataFrame({'teks_analisis': scraped_texts})
    df['sentimen'] = [klasifikasi_sentimen(teks) for teks in df['teks_analisis']]

    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("Analisis selesai. Data sentimen sudah ditambahkan ke Google Spreadsheet.")

# --- 4. Visualisasi Data ---
def visualisasi_data():
    try:
        data_rows = worksheet.get_all_values()
        df = pd.DataFrame(data_rows[1:], columns=data_rows[0])
    except gspread.exceptions.APIError as e:
        print(f"Error saat membaca spreadsheet: {e}")
        return

    if 'sentimen' not in df.columns or df['sentimen'].empty:
        print("Kolom 'sentimen' belum ada atau kosong di spreadsheet.")
        return

    sentimen_counts = df['sentimen'].value_counts()
    plt.figure(figsize=(8, 6))
    sentimen_counts.plot(kind='bar', color=['green', 'red', 'gray'])
    plt.title('Distribusi Sentimen Data')
    plt.xlabel('Sentimen')
    plt.ylabel('Jumlah')
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--')
    plt.tight_layout()
    plt.show()
    print("Visualisasi berhasil dibuat.")

# --- Jalankan Program Utama ---
if __name__ == "__main__":
    jalankan_analisis()
    visualisasi_data()
