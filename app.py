import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="✈️ 雲端旅遊手冊", layout="wide")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取資料函數
def get_data(sheet_name):
    return conn.read(worksheet=sheet_name).dropna(how="all")

st.title("🌍 雲端同步旅遊規劃")

tab1, tab2, tab3 = st.tabs(["📅 行程", "💰 費用", "🔄 同步狀態"])

with tab1:
    st.subheader("編輯行程 (修改後請按下方按鈕存檔)")
    df_itinerary = get_data("itinerary")
    
    # 編輯器
    edited_itinerary = st.data_editor(df_itinerary, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 儲存行程到 Google Sheets"):
        conn.update(worksheet="itinerary", data=edited_itinerary)
        st.success("存檔成功！同行者現在也能看到了。")

    st.divider()
    # 自動收合邏輯 (保持與之前相同)
    today = date.today()
    for d in sorted(edited_itinerary["日期"].unique()):
        is_expanded = pd.to_datetime(d).date() >= today
        with st.expander(f"📅 日期：{d}", expanded=is_expanded):
            day_items = edited_itinerary[edited_itinerary["日期"] == d]
            for _, row in day_items.iterrows():
                col1, col2 = st.columns([1, 4])
                col1.info(row['時間'])
                st.write(f"**{row['活動']}**")
                if row['地圖']: st.link_button("🗺️ 導航", row['地圖'])

with tab2:
    st.subheader("費用明細")
    df_expenses = get_data("expenses")
    edited_expenses = st.data_editor(df_expenses, num_rows="dynamic", use_container_width=True)
    
    if st.button("💰 儲存費用"):
        conn.update(worksheet="expenses", data=edited_expenses)
        st.rerun()

    # 計算總和
    total = (edited_expenses["金額"] * edited_expenses["匯率"]).sum()
    st.metric("預算總計 (TWD)", f"${total:,.0f}")

with tab3:
    st.write("✅ 目前已連線至 Google Sheets")
    st.write("你可以隨時打開 Google Sheets App 直接改表，網頁重新整理後就會更新。")
