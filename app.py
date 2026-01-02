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
        # 讀取資料並清除全空行
        data = conn.read(worksheet=sheet_name).dropna(how="all")
        return data
    except Exception as e:
        st.error(f"讀取分頁【{sheet_name}】失敗，請確認 Google Sheets 中是否有此分頁名稱。")
        return pd.DataFrame()

st.title("🌍 專屬旅遊規劃 & 指引手冊")

# --- 分頁設定 ---
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
        if st.button("💾 儲存行程更改"):
            conn.update(worksheet="itinerary", data=edited_itinerary)
            st.success("行程已同步！")
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
                    st.write(f"**{row['活動']}**")
                    if pd.notna(row['地圖連結']): st.link_button("🗺️ 導航", row['地圖連結'])
    else:
        st.warning("請確認 Google Sheets 的 itinerary 分頁已有資料。")

# --- Tab 2: 費用明細 ---
with tab2:
    st.subheader("多幣別記帳本")
    df_expenses = get_data("expenses")
    if not df_expenses.empty:
        edited_expenses = st.data_editor(df_expenses, num_rows="dynamic", use_container_width=True, key="expense_editor")
        if st.button("💰 儲存費用更改"):
            conn.update(worksheet="expenses", data=edited_expenses)
            st.success("費用已同步！")
            st.rerun()
        total_twd = (edited_expenses["金額"] * edited_expenses["匯率"]).sum()
        st.metric("總支出預估 (TWD)", f"${total_twd:,.0f}")
    else:
        st.write("請在 Google Sheets 的 expenses 分頁填入資料。")

# --- Tab 3: 待辦清單 (已修正：現在可以連動 Google Sheets) ---
with tab3:
    st.subheader("✅ 旅遊待辦清單")
    st.write("提示：在『狀態』欄位點擊即可勾選。編輯完畢請記得按下方儲存。")
    
    # 從 Google Sheets 抓取任務資料
    df_tasks = get_data("tasks")
    
    if not df_tasks.empty:
        # 這裡使用 column_config 把「狀態」變成勾選框 (Checkbox)
        edited_tasks = st.data_editor(
            df_tasks,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "狀態": st.column_config.CheckboxColumn("狀態", help="勾選代表已完成", default=False)
            },
            key="tasks_editor"
        )
        
        if st.button("💾 儲存待辦清單"):
            conn.update(worksheet="tasks", data=edited_tasks)
            st.success("待辦清單已同步到雲端！")
            st.rerun()
    else:
        st.warning("請在 Google Sheets 中建立名為 tasks 的分頁，並填入標題：事項、狀態、備註。")

# --- Tab 4: 注意事項 ---
with tab4:
    st.subheader("📌 連結與筆記")
    df_notes = get_data("notes")
    if not df_notes.empty:
        edited_notes = st.data_editor(df_notes, num_rows="dynamic", use_container_width=True, key="notes_editor")
        if st.button("📌 儲存筆記"):
            conn.update(worksheet="notes", data=edited_notes)
            st.success("筆記已同步！")
            st.rerun()
    else:
        st.write("請在 Google Sheets 的 notes 分頁填入資料。")
