import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import date
import time

# --- Streamlit UI ---
st.set_page_config(page_title="LLMOチェック v0.2 (Selenium版)", layout="wide")
st.title("🔍 LLMOチェックツール v0.2 (Selenium対応)")
st.markdown("Seleniumを使ってGoogleの検索結果を実際のブラウザで取得します。ブランド名などの精度が向上します。")

# 入力フォーム
with st.form("llmo_form"):
    domain = st.text_input("調査対象ドメイン（例: yahoo.co.jp）", "")
    keywords_input = st.text_area("キーワード一覧（1行に1キーワード、最大5件）", "")
    enable_debug = st.checkbox("デバッグモード（解析中のURLを表示）", value=False)
    submitted = st.form_submit_button("分析スタート")

# --- 処理 ---
if submitted and domain and keywords_input:
    keywords = [k.strip() for k in keywords_input.strip().split("\n") if k.strip()][:5]
    result_data = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=ja-JP")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    for kw in keywords:
        query = kw.replace(" ", "+")
        search_url = f"https://www.google.co.jp/search?q={query}&hl=ja"
        driver.get(search_url)
        time.sleep(2.5)

        elements = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc, div.g, div.MjjYud")

        found = False
        match_url = ""
        snippet = ""
        debug_urls = []

        for elem in elements[:5]:
            try:
                link = elem.find_element(By.TAG_NAME, "a").get_attribute("href")
                text = elem.text
                debug_urls.append(link)
                if domain.lower() in link.lower() or f"www.{domain}".lower() in link.lower() or domain.lower() in text.lower():
                    found = True
                    match_url = link
                    snippet = text[:150]
                    break
            except:
                continue

        result_data.append({
            "キーワード": kw,
            "ヒット": "○" if found else "×",
            "URL": match_url,
            "抜粋": snippet,
            "デバッグURL一覧": "; ".join(debug_urls) if enable_debug else ""
        })

    driver.quit()

    df = pd.DataFrame(result_data)
    st.success(f"検索完了！{len(df)} 件中 {df['ヒット'].tolist().count('○')} 件ヒットしました。")
    st.dataframe(df)

    hit_rate = df["ヒット"].tolist().count("○") / len(df) * 100
    st.metric("ヒット率", f"{hit_rate:.1f}%")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("CSVとしてダウンロード", data=csv, file_name=f"llmo_selenium_results_{date.today()}.csv", mime="text/csv")

else:
    st.info("ドメインとキーワードを入力して『分析スタート』を押してください。最大5件まで対応。")
