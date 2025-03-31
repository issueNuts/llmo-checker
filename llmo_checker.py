import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
import time

# --- Streamlit UI ---
st.title("🔍 LLMOチェックツール v0.1")
st.markdown("指定したドメインが各キーワードでGoogle検索結果の上位に出てくるかをチェックします。")

# 入力フォーム
domain = st.text_input("調査対象ドメイン（例: xxxxx.co.jp）", "")
keywords_input = st.text_area("キーワード一覧（1行に1キーワード、最大10件）", "")

if st.button("分析スタート") and domain and keywords_input:
    keywords = [k.strip() for k in keywords_input.strip().split("\n") if k.strip()][:10]
    result_data = []

    headers = {"User-Agent": "Mozilla/5.0"}

    for kw in keywords:
        query = kw.replace(" ", "+")
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.g")

        found = False
        match_url = ""
        snippet = ""

        for r in results[:5]:
            link_tag = r.find("a")
            if link_tag and link_tag.has_attr("href"):
                link = link_tag["href"]
                text = r.get_text()
                if domain in link or domain in text:
                    found = True
                    match_url = link
                    snippet = text[:150]
                    break

        result_data.append({
            "キーワード": kw,
            "ヒット": "○" if found else "×",
            "URL": match_url,
            "抜粋": snippet
        })

        time.sleep(1.5)  # Googleへの負荷を避けるため少し待機

    df = pd.DataFrame(result_data)
    st.success(f"検索完了！{len(df)} 件中 {df['ヒット'].tolist().count('○')} 件ヒットしました。")
    st.dataframe(df)

    # ヒット率の集計
    hit_rate = df["ヒット"].tolist().count("○") / len(df) * 100
    st.metric("ヒット率", f"{hit_rate:.1f}%")

    # CSVダウンロード
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("CSVとしてダウンロード", data=csv, file_name=f"llmo_results_{date.today()}.csv", mime="text/csv")
else:
    st.info("ドメインとキーワードを入力して『分析スタート』を押してください。")
