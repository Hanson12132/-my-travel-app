import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 1. 網頁基本設定 & 隱藏側邊欄多餘內容
st.set_page_config(
    page_title="✈️ 我們的雲端旅遊手冊", 
    layout="wide", 
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    try:
        # ttl=0 確保每次都抓最新資料
        data = conn.read(worksheet=sheet_name, ttl=0)
        data = data.dropna(how="all")
        return data
    except Exception as e:
        st.error(f"讀取分頁【{sheet_name}】失敗，請檢查 Google Sheets 分頁名稱是否完全正確。")
        return pd.DataFrame()

# --- 2. 側邊欄：實用連結與工具 ---
with st.sidebar:
    st.header("🧳 旅遊工具箱")
    
    st.subheader("🔗 快速連結")
    st.link_button("🌐 Visit Japan Web", "https://vjw-lp.digital.go.jp/zh-hant/")
    st.link_button("🏮 日本氣象查詢", "https://www.japan.travel/tw/weather/")
    st.link_button("🔤 Google 翻譯", "https://translate.google.com/")
    
    st.divider()
    
    st.subheader("💱 快速匯率換算")
    rate = st.number_input("1 JPY 換 TWD", value=0.2150, format="%.4f")
    jpy_amt = st.number_input("輸入日幣", min_value=0)
    st.metric("等於台幣", f"${round(jpy_amt * rate, 2)}")
    
    st.divider()
    
    if st.button("🔄 強制刷新雲端資料"):
        st.cache_data.clear()
        st.rerun()

# --- 主畫面 ---
st.title("🌍 專屬旅遊規劃 & 指引手冊")

tab1, tab2, tab3, tab4 = st.tabs(["📅 每日行程", "💰 費用明細", "✅ 待辦清單", "📌 注意事項"])

# --- Tab 1: 每日行程 ---
with tab1:
    df_itinerary = get_data("itinerary")
    
    if not df_itinerary.empty:
        # 資料轉換
        df_itinerary["日期"] = pd.to_datetime(df_itinerary["日期"], errors='coerce')
        df_itinerary = df_itinerary.dropna(subset=["日期"])
        df_itinerary["日期"] = df_itinerary["日期"].dt.date
        
        # A. 導覽模式 (放在上方)
        st.subheader("🚩 旅遊當下導覽模式")
        today = date.today()
        unique_dates = sorted(df_itinerary["日期"].unique())
        
        for i, d in enumerate(unique_dates):
            is_past = d < today
            status_icon = "⌛" if is_past else "🚩"
            with st.expander(f"Day {i+1}：{d} {status_icon} {'(已結束)' if is_past else ''}", expanded=not is_past):
                day_data = df_itinerary[df_itinerary["日期"] == d].sort_values("時間")
                for _, row in day_data.iterrows():
                    col_t, col_c = st.columns([1, 5])
                    col_t.info(f"**{row['時間']}**")
                    with col_c:
                        st.write(f"**{row['活動']}**")
                        if pd.notna(row['備註']) and str(row['備註']) != "nan":
                            st.caption(f"📝 {row['備註']}")
                        # 導覽模式按鈕串聯地圖連結
                        if pd.notna(row['地圖連結']) and str(row['地圖連結']).startswith("http"):
                            st.link_button("📍 開啟導航", row['地圖連結'])
        
        st.divider()

        # B. 行程編輯器 (放在下面)
        st.subheader("📝 行程編輯器")
        edited_itinerary = st.data_editor(
            df_itinerary, 
            num_rows="dynamic", 
            use_container_width=True, 
            hide_index=True, # 刪除編號欄
            column_config={
                "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
                "地圖連結": st.column_config.LinkColumn("地圖連結", help="請貼上完整的 Google 地圖網址")
            },
            key="itinerary_editor"
        )
        if st.button("💾 儲存行程更改", key="save_itinerary"):
            conn.update(worksheet="itinerary", data=edited_itinerary)
            st.success("行程已同步！")
            st.rerun()
    else:
        st.warning("請在 Google Sheets 的 itinerary 分頁填入資料。")

# --- Tab 2: 費用明細 ---
with tab2:
    st.subheader("💰 費用明細")
    df_expenses = get_data("expenses")
    if not df_expenses.empty:
        edited_expenses = st.data_editor(
            df_expenses, 
            num_rows="dynamic", 
            use_container_width=True, 
            hide_index=True, # 刪除編號欄
            key="expense_editor"
        )
        if st.button("💰 儲存費用更改", key="save_expenses"):
            conn.update(worksheet="expenses", data=edited_expenses)
            st.success("費用已同步！")
            st.rerun()
        
        # 計算台幣
        edited_expenses["金額"] = pd.to_numeric(edited_expenses["金額"], errors='coerce').fillna(0)
        edited_expenses["匯率"] = pd.to_numeric(edited_expenses["匯率"], errors='coerce').fillna(1)
        total_twd = (edited_expenses["金額"] * edited_expenses["匯率"]).sum()
        st.metric("預計花費總額 (TWD)", f"${total_twd:,.0f}")
    else:
        st.write("目前無費用資料。")

# --- Tab 3: 待辦清單 ---
with tab3:
    st.subheader("✅ 待辦清單")
    df_tasks = get_data("tasks")
    if not df_tasks.empty:
        # 強制轉換狀態為布林值以顯示勾選框
        df_tasks["狀態"] = df_tasks["狀態"].astype(str).str.upper().isin(["TRUE", "1", "YES", "T"]).astype(bool)
        
        edited_tasks = st.data_editor(
            df_tasks,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True, # 刪除編號欄
            column_config={"狀態": st.column_config.CheckboxColumn("狀態", default=False)},
            key="tasks_editor"
        )
        if st.button("💾 儲存清單", key="save_tasks"):
            conn.update(worksheet="tasks", data=edited_tasks)
            st.success("清單已同步！")
            st.rerun()

# --- Tab 4: 注意事項 ---
with tab4:
    st.subheader("📌 注意事項")
    df_notes = get_data("notes")
    if not df_notes.empty:
        edited_notes = st.data_editor(
            df_notes, 
            num_rows="dynamic", 
            use_container_width=True, 
            hide_index=True, # 刪除編號欄
            column_config={"網址連結": st.column_config.LinkColumn("網址連結")},
            key="notes_editor"
        )
        if st.button("📌 儲存筆記", key="save_notes"):
            conn.update(worksheet="notes", data=edited_notes)
            st.success("筆記已同步！")
            st.rerun()
