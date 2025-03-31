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
st.set_page_config(page_title="LLMOチェック Perplexity (Selenium)", layout="wide")
st.title("🤖 LLMOチェックツール v0.3a (Perplexity + Selenium)")
st.markdown("Seleniumを使ってPerplexityのAI検索結果から、指定ドメインの引用有無を確認します。")

# 入力フォーム
with st.form("perplexity_form"):
    domain = st.text_input("調査対象ドメイン（例: xxxxx.co.jp）", "")
    keywords_input = st.text_area("キーワード一覧（1行に1キーワード、最大5件）", "")
    enable_debug = st.checkbox("デバッグモード（取得した引用URLを表示）", value=False)
    submitted = st.form_submit_button("SeleniumでAI分析スタート")

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
        url = f"https://www.perplexity.ai/search?q={query}"
        driver.get(url)
        time.sleep(5)  # PerplexityのJS読み込み待ち

        found = False
        match_url = ""
        debug_urls = []

        try:
            links = driver.find_elements(By.CSS_SELECTOR, "a")
            for link_elem in links:
                href = link_elem.get_attribute("href")
                if href:
                    debug_urls.append(href)
                    if domain.lower() in href.lower():
                        found = True
                        match_url = href
                        break
        except:
            pass

        result_data.append({
            "キーワード": kw,
            "ヒット": "○" if found else "×",
            "引用URL": match_url,
            "引用URL一覧": "; ".join(debug_urls) if enable_debug else ""
        })

    driver.quit()

    df = pd.DataFrame(result_data)
    st.success(f"分析完了！{len(df)} 件中 {df['ヒット'].tolist().count('○')} 件ヒットしました。")
    st.dataframe(df)

    hit_rate = df["ヒット"].tolist().count("○") / len(df) * 100
    st.metric("Perplexityヒット率 (Selenium)", f"{hit_rate:.1f}%")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("CSVとしてダウンロード", data=csv, file_name=f"llmo_perplexity_selenium_results_{date.today()}.csv", mime="text/csv")

else:
    st.info("ドメインとキーワードを入力して『SeleniumでAI分析スタート』を押してください。最大5件まで対応。")
