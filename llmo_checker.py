import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
import time

# --- Streamlit UI ---
st.set_page_config(page_title="LLMOチェック v0.1b", layout="wide")
st.title("🔍 LLMOチェックツール v0.1b")
st.markdown("指定ドメインが各キーワードでGoogleやAI検索にどれくらい出てくるかを調査・可視化します。")

# 入力フォーム
with st.form("llmo_form"):
    domain = st.text_input("調査対象ドメイン（例: xxxxx.co.jp）", "")
    keywords_input = st.text_area("キーワード一覧（1行に1キーワード、最大10件）", "")
    enable_debug = st.checkbox("デバッグモード（解析中のURLを表示）", value=False)
    submitted = st.form_submit_button("分析スタート")

# --- 処理 ---
if submitted and domain and keywords_input:
    keywords = [k.strip() for k in keywords_input.strip().split("\n") if k.strip()][:10]
    result_data = []

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    for kw in keywords:
        query = kw.replace(" ", "+")
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.tF2Cxc")

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
                # ゆるい一致判定
                if domain in link or f"www.{domain}" in link or domain in text:
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

        time.sleep(1.5)  # 負荷対策

    df = pd.DataFrame(result_data)
    st.success(f"検索完了！{len(df)} 件中 {df['ヒット'].tolist().count('○')} 件ヒットしました。")
    st.dataframe(df)

    # ヒット率の集計
    hit_rate = df["ヒット"].tolist().count("○") / len(df) * 100
    st.metric("ヒット率", f"{hit_rate:.1f}%")

    # CSVダウンロード
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("CSVとしてダウンロード", data=csv, file_name=f"llmo_results_{date.today()}.csv", mime="text/csv")

    # TODO: AI検索連携（Perplexity APIなど）を次バージョンで追加
    st.info("※ 次回バージョンでPerplexity（AI検索）にも対応予定です。")

else:
    st.info("ドメインとキーワードを入力して『分析スタート』を押してください。")
