import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 網頁基本設定
st.set_page_config(page_title="✈️ 我們的雲端旅遊手冊", layout="wide", page_icon="🌍")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    try:
        # 【關鍵修正】：加入 ttl=0，強制每次都從 Google Sheets 抓取最新資料
        data = conn.read(worksheet=sheet_name, ttl=0)
        data = data.dropna(how="all")
        return data
    except Exception as e:
        st.error(f"讀取分頁【{sheet_name}】失敗，請確認名稱是否正確。")
        return pd.DataFrame()

# 增加一個手動刷新按鈕在側邊欄，確保資料同步
if st.sidebar.button("🔄 手動刷新資料"):
    st.cache_data.clear() # 清除所有快取
    st.rerun()

st.title("🌍 專屬旅遊規劃 & 指引手冊")

tab1, tab2, tab3, tab4 = st.tabs(["📅 每日行程", "💰 費用明細", "✅ 待辦清單", "📌 注意事項"])

# --- Tab 1: 每日行程 ---
with tab1:
    st.subheader("行程編輯器")
    df_itinerary = get_data("itinerary")
    if not df_itinerary.empty:
        df_itinerary["日期"] = pd.to_datetime(df_itinerary["日期"], errors='coerce')
        df_itinerary = df_itinerary.dropna(subset=["日期"])
        df_itinerary["日期"] = df_itinerary["日期"].dt.date
        
        edited_itinerary = st.data_editor(df_itinerary, num_rows="dynamic", use_container_width=True, key="itinerary_editor")
        
        if st.button("💾 儲存行程更改", key="save_itinerary"):
            conn.update(worksheet="itinerary", data=edited_itinerary)
            st.success("行程已同步至雲端！")
            st.rerun()
            
        st.divider()
        st.subheader("🚩 導覽模式")
        today = date.today()
        unique_dates = sorted(edited_itinerary["日期"].unique())
        for i, d in enumerate(unique_dates):
            is_past = d < today
            with st.expander(f"Day {i+1}：{d} {'⌛' if is_past else '🚩'}", expanded=not is_past):
                day_data = edited_itinerary[edited_itinerary["日期"] == d].sort_values("時間")
                for _, row in day_data.iterrows():
                    col_t, col_c = st.columns([1, 4])
                    col_t.info(f"**{row['時間']}**")
                    with col_c:
                        st.write(f"**{row['活動']}**")
                        if pd.notna(row['地圖連結']): st.link_button("🗺️ 導航", row['地圖連結'])

# --- Tab 2: 費用明細 ---
with tab2:
    st.subheader("多幣別記帳本")
    df_expenses = get_data("expenses")
    if not df_expenses.empty:
        edited_expenses = st.data_editor(df_expenses, num_rows="dynamic", use_container_width=True, key="expense_editor")
        if st.button("💰 儲存費用更改", key="save_expenses"):
            conn.update(worksheet="expenses", data=edited_expenses)
            st.success("費用已同步！")
            st.rerun()
        edited_expenses["金額"] = pd.to_numeric(edited_expenses["金額"], errors='coerce').fillna(0)
        edited_expenses["匯率"] = pd.to_numeric(edited_expenses["匯率"], errors='coerce').fillna(1)
        total_twd = (edited_expenses["金額"] * edited_expenses["匯率"]).sum()
        st.metric("總支出預估 (TWD)", f"${total_twd:,.0f}")

# --- Tab 3: 待辦清單 ---
with tab3:
    st.subheader("✅ 旅遊待辦清單")
    df_tasks = get_data("tasks")
    if not df_tasks.empty:
        # 確保狀態為布林值
        df_tasks["狀態"] = df_tasks["狀態"].astype(str).str.upper().isin(["TRUE", "1", "YES", "T"])
        df_tasks["狀態"] = df_tasks["狀態"].astype(bool)
        
        edited_tasks = st.data_editor(
            df_tasks,
            num_rows="dynamic",
            use_container_width=True,
            column_config={"狀態": st.column_config.CheckboxColumn("狀態", default=False)},
            key="tasks_editor"
        )
        if st.button("💾 儲存清單", key="save_tasks"):
            conn.update(worksheet="tasks", data=edited_tasks)
            st.success("待辦清單已同步！")
            st.rerun()

# --- Tab 4: 注意事項 ---
with tab4:
    st.subheader("📌 連結與筆記")
    df_notes = get_data("notes")
    if not df_notes.empty:
        edited_notes = st.data_editor(df_notes, num_rows="dynamic", use_container_width=True, key="notes_editor")
        if st.button("📌 儲存筆記", key="save_notes"):
            conn.update(worksheet="notes", data=edited_notes)
            st.success("筆記已同步！")
            st.rerun()
