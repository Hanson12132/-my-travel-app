import streamlit as st
import pandas as pd
from datetime import datetime, date

# 網頁基本設定
st.set_page_config(page_title="✈️ 我們的旅遊手冊", layout="wide")

st.title("🌍 全方位旅遊規劃手冊")

# --- 1. 資料初始化 ---

# 行程表資料 (加入日期欄位，格式為 YYYY-MM-DD)
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = pd.DataFrame([
        {"日期": date(2024, 5, 20), "時間": "10:00", "活動": "桃園機場報到", "備註": "記得帶護照", "地圖": "https://google.com"},
        {"日期": date(2024, 5, 20), "時間": "14:00", "活動": "抵達東京", "備註": "領取 JR Pass", "地圖": "https://google.com"},
        {"日期": date(2024, 5, 21), "時間": "09:00", "活動": "築地市場吃早餐", "備註": "早點起床避開人潮", "地圖": "https://google.com"},
        {"日期": date(2024, 5, 22), "時間": "11:00", "活動": "淺草寺參拜", "備註": "可以租和服", "地圖": "https://google.com"}
    ])

# 費用表資料
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame([
        {"項目": "機票", "幣別": "TWD", "金額": 15000, "匯率": 1.0, "備註": "已付"},
        {"項目": "拉麵", "幣別": "JPY", "金額": 1200, "匯率": 0.215, "備註": "晚餐"}
    ])

# 注意事項資料
if 'notes' not in st.session_state:
    st.session_state.notes = pd.DataFrame([
        {"類別": "交通", "內容": "JR Pass 預約網站", "連結": "https://www.japanrailpass.net/"}
    ])

# --- 2. 側邊欄：匯率小工具 ---
st.sidebar.header("💱 匯率小工具")
quick_rate = st.sidebar.number_input("目前匯率 (如 JPY 換 TWD)", value=0.215, format="%.4f")
quick_jpy = st.sidebar.number_input("輸入外幣金額", min_value=0)
st.sidebar.metric("換算台幣", f"${round(quick_jpy * quick_rate, 2)}")

# --- 3. 主要功能分頁 ---
tab1, tab2, tab3, tab4 = st.tabs(["📅 行程規劃", "💰 費用明細", "✅ 待辦事項", "📌 注意事項與連結"])

# --- Tab 1: 行程規劃 (加入自動收合邏輯) ---
with tab1:
    st.subheader("📝 編輯所有行程")
    # 主編輯表格，讓你可以自由新增日期與活動
    edited_itinerary = st.data_editor(
        st.session_state.itinerary, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD", required=True),
        }
    )
    st.session_state.itinerary = edited_itinerary
    
    st.divider()
    st.subheader("📍 每日行程導覽 (自動收合已結束的天數)")
    
    # 取得今天的日期 (用於判斷是否收合)
    today = date.today()
    
    # 將行程依照日期排序
    sorted_df = st.session_state.itinerary.sort_values(by=["日期", "時間"])
    
    # 找出所有不重複的日期
    unique_dates = sorted_df["日期"].unique()
    
    for i, d in enumerate(unique_dates):
        # 轉換日期格式以便比較
        current_date = pd.to_datetime(d).date() if isinstance(d, str) else d
        
        # 判斷狀態與標籤
        if current_date < today:
            status_label = "⌛ 已結束"
            is_expanded = False # 過去的行程預設收合
        elif current_date == today:
            status_label = "🚩 今日行程"
            is_expanded = True  # 今天的行程預設開啟
        else:
            status_label = "🗓️ 尚未到達"
            is_expanded = True  # 未來的行程預設開啟 (你也可以改為 False)

        # 建立收合區塊 (Expander)
        with st.expander(f"第 {i+1} 天：{current_date} ({status_label})", expanded=is_expanded):
            day_items = sorted_df[sorted_df["日期"] == d]
            for _, row in day_items.iterrows():
                c1, c2 = st.columns([1, 4])
                c1.info(f"**{row['時間']}**")
                with c2:
                    st.write(f"**{row['活動']}**")
                    if row['備註']: st.caption(f"📝 {row['備註']}")
                    if row['地圖']: st.link_button("🗺️ 導航", row['地圖'])

# --- Tab 2: 費用明細 ---
with tab2:
    st.subheader("💰 多幣別費用計算")
    edited_exp = st.data_editor(
        st.session_state.expenses, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "幣別": st.column_config.SelectboxColumn("幣別", options=["TWD", "JPY", "USD", "EUR", "KRW"]),
            "匯率": st.column_config.NumberColumn("匯率", format="%.4f")
        }
    )
    st.session_state.expenses = edited_exp

    if not st.session_state.expenses.empty:
        # 計算總支出
        temp_df = st.session_state.expenses.copy()
        temp_df['台幣換算'] = temp_df['金額'] * temp_df['匯率']
        total_twd = temp_df['台幣換算'].sum()
        st.metric("目前總支出 (TWD)", f"${total_twd:,.0f}")
        st.dataframe(temp_df, use_container_width=True)

# --- Tab 3: 待辦事項 (保持不變) ---
with tab3:
    st.subheader("✅ 出發前準備")
    st.checkbox("辦理旅平險")
    st.checkbox("確認護照效期")
    st.checkbox("購買網路卡")

# --- Tab 4: 注意事項與連結 ---
with tab4:
    st.subheader("📌 旅遊重要資訊")
    st.session_state.notes = st.data_editor(st.session_state.notes, num_rows="dynamic", use_container_width=True)
    
    st.divider()
    for index, row in st.session_state.notes.iterrows():
        col_cat, col_cont, col_btn = st.columns([1, 3, 1])
        col_cat.warning(row['類別'])
        col_cont.write(row['內容'])
        if row['連結']: col_btn.link_button("前往", row['連結'])
