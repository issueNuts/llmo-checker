import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
import time

# --- Streamlit UI ---
st.set_page_config(page_title="LLMOチェック Light版", layout="wide")
st.title("🔍 LLMOチェックツール Light版 (オンライン対応)")
st.markdown("Google検索を軽量方式（requests + BeautifulSoup）で調査します。Streamlit Cloud対応。")

# 入力フォーム
with st.form("llmo_light_form"):
    domain = st.text_input("調査対象ドメイン（例: yahoo.co.jp）", "")
    keywords_input = st.text_area("キーワード一覧（1行に1キーワード、最大10件）", "")
    enable_debug = st.checkbox("デバッグモード（解析中のURLを表示）", value=False)
    submitted = st.form_submit_button("分析スタート")

# --- 処理 ---
if submitted and domain and keywords_input:
    keywords = [k.strip() for k in keywords_input.strip().split("\n") if k.strip()][:10]
    result_data = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for kw in keywords:
        query = kw.replace(" ", "+")
        url = f"https://www.google.co.jp/search?q={query}&hl=ja"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.tF2Cxc, div.g, div.MjjYud")

        found = False
        match_url = ""
        snippet = ""
        debug_urls = []

        for r in results[:5]:
            link_tag = r.find("a", href=True)
            if link_tag:
                link = link_tag["href"]
                text = r.get_text()
                debug_urls.append(link)
                if domain.lower() in link.lower() or f"www.{domain}".lower() in link.lower() or domain.lower() in text.lower():
                    found = True
                    match_url = link
                    snippet = text[:150]
                    break

        result_data.append({
            "キーワード": kw,
            "ヒット": "○" if found else "×",
            "URL": match_url,
            "抜粋": snippet,
            "デバッグURL一覧": "; ".join(debug_urls) if enable_debug else ""
        })

        time.sleep(1.5)

    df = pd.DataFrame(result_data)
    st.success(f"検索完了！{len(df)} 件中 {df['ヒット'].tolist().count('○')} 件ヒットしました。")
    st.dataframe(df)

    hit_rate = df["ヒット"].tolist().count("○") / len(df) * 100
    st.metric("ヒット率", f"{hit_rate:.1f}%")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("CSVとしてダウンロード", data=csv, file_name=f"llmo_light_results_{date.today()}.csv", mime="text/csv")

else:
    st.info("ドメインとキーワードを入力して『分析スタート』を押してください。最大10件まで対応。")
