import streamlit as st 
import requests
import urllib.parse
import os
from dotenv import load_dotenv
import datetime
import re

load_dotenv()

# レイアウト調整（スライダーを左、検索ボックスを右）
col1, col2, col3 = st.columns([1, 2, 2])  # 左 1: 右 2 の比率で分割

with col1:
    rating_threshold = st.slider("Googleマップ評価", 2.0, 5.0, 3.0, step=0.1)

with col2:
    search_query_1 = st.text_input("エリア・駅（例:銀座、渋谷）", "")

with col3:
    search_query_2 = st.text_input("キーワード（例:焼肉、店名）", "")


def get_instagram_search_url(store_name):
    """店名からInstagramの検索URLを作成"""
    base_url = "https://www.instagram.com/explore/search/keyword/?q="
    return base_url + store_name.replace(" ", "%20")

def bold_today_hours(text):
    """今日の曜日の営業時間を太字にする"""
    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    
    # 今日の曜日を取得
    today_index = datetime.datetime.today().weekday()  # 0=月, 6=日
    today_name = weekdays[today_index]

    # 今日の曜日の部分を **で囲んで太字** にする
    return re.sub(f"({today_name}.*?)$", r"**\1**", text, flags=re.MULTILINE)

# APIキーの取得（環境変数 or 直接設定）
api_key = os.getenv("API_KEY")

# APIのURLとヘッダー情報
url = "https://places.googleapis.com/v1/places:searchText"
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": api_key,
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.currentOpeningHours,places.reviews,places.googleMapsLinks,places.rating"
}

# 検索パラメータ
params = {
    "textQuery":  f"{search_query_1} AND {search_query_2}",
    "languageCode": "ja",
}

# 検索ボタンを設置
if st.button("検索"):
    # APIリクエスト
    response = requests.post(url, headers=headers, json=params)

    # レスポンスの処理
    if response.status_code == 200:
        places = response.json()
        
        # フィルタリングして表示
        filtered_places = []
        
        for place in places.get("places", []):
            name = place.get("displayName", {}).get("text", "名前なし")
            rating = place.get("rating", 0.0)  # 評価がない場合は0.0とする
            google_maps_link = place.get("googleMapsLinks", {}).get("placeUri", "リンクなし")
            opening_hours = place.get("currentOpeningHours", {}).get("weekdayDescriptions", ["営業時間情報なし"])
            opening_hours_text = "\n".join(opening_hours)

            # 今日の曜日だけ太字にする
            opening_hours_text = bold_today_hours(opening_hours_text)

            instagram_url = get_instagram_search_url(name)

            # スライダーの閾値以上の評価の店舗のみ追加
            if rating >= rating_threshold:
                filtered_places.append({
                    "name": name,
                    "rating": rating,
                    "google_maps_link": google_maps_link,
                    "instagram_url": instagram_url,
                    "opening_hours": opening_hours_text
                })

        # Streamlit で結果を表示
        if filtered_places:
            for place in filtered_places:
                st.write(f"### {place['name']}")
                st.write(f"⭐ 評価: {place['rating']}")
                st.write(f"[Googleマップで見る]({place['google_maps_link']})")
                st.write(f"[Instagramで検索]({place['instagram_url']})")
                st.write(f"**営業時間:**\n{place['opening_hours']}", unsafe_allow_html=True)
                st.write("---")
        else:
            st.write("該当する店舗が見つかりませんでした。")
    else:
        st.error(f"APIリクエストに失敗しました: {response.status_code}")
        st.write(response.text)
