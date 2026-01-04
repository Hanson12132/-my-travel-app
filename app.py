import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 1. 網頁基本設定
st.set_page_config(
    page_title="✈️ 我們的雲端旅遊手冊", 
    layout="wide", 
    page_icon="🌍"
)

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name, ttl=0)
        data = data.dropna(how="all")
        return data
    except Exception as e:
        return pd.DataFrame()

# --- 側邊欄工具箱 ---
with st.sidebar:
    st.header("🧳 旅遊工具箱")
    st.link_button("🌐 Visit Japan Web", "https://vjw-lp.digital.go.jp/zh-hant/")
    st.link_button("🏮 日本氣象查詢", "https://weather.yahoo.co.jp/weather/")
    st.link_button("🔤 Google 翻譯", "https://translate.google.com/")
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
        df_itinerary["日期"] = pd.to_datetime(df_itinerary["日期"], errors='coerce')
        df_itinerary = df_itinerary.dropna(subset=["日期"])
        df_itinerary["日期"] = df_itinerary["日期"].dt.date
        
        # 導覽模式
        st.subheader("🚩 旅遊導覽模式")
        today = date.today()
        unique_dates = sorted(df_itinerary["日期"].unique())
        for i, d in enumerate(unique_dates):
            is_past = d < today
            with st.expander(f"Day {i+1}：{d} {'⌛' if is_past else '🚩'}", expanded=not is_past):
                day_data = df_itinerary[df_itinerary["日期"] == d].sort_values("時間")
                for _, row in day_data.iterrows():
                    col_t, col_c = st.columns([1, 5])
                    col_t.info(f"**{row['時間']}**")
                    with col_c:
                        st.write(f"**{row['活動']}**")
                        if pd.notna(row['地圖連結']) and str(row['地圖連結']).startswith("http"):
                            st.link_button("📍 開啟導航", row['地圖連結'])
        
        st.divider()
        st.subheader("📝 行程編輯器")
        edited_itinerary = st.data_editor(
            df_itinerary, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
                "地圖連結": st.column_config.LinkColumn("地圖連結")
            }, key="itinerary_editor"
        )
        if st.button("💾 儲存行程", key="save_itinerary"):
            conn.update(worksheet="itinerary", data=edited_itinerary)
            st.rerun()

# --- Tab 2: 費用明細 (新增支付人與圖表) ---
with tab2:
    df_expenses = get_data("expenses")
    if not df_expenses.empty:
        # 強制數值轉換以解決「後台編輯無法加總」的問題
        df_expenses["金額"] = pd.to_numeric(df_expenses["金額"], errors='coerce').fillna(0)
        df_expenses["匯率"] = pd.to_numeric(df_expenses["匯率"], errors='coerce').fillna(1)
        df_expenses["台幣"] = df_expenses["金額"] * df_expenses["匯率"]
        
        # 視覺化圖表
        st.subheader("📊 支出統計")
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.write("各支付人佔比")
            st.bar_chart(df_expenses.groupby("支付人")["台幣"].sum())
        with col_chart2:
            st.write("各支付方式佔比")
            st.bar_chart(df_expenses.groupby("支付方式")["台幣"].sum())

        st.divider()
        st.subheader("📝 費用編輯器")
        edited_expenses = st.data_editor(
            df_expenses.drop(columns=["台幣"]), # 隱藏計算欄位
            num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "支付人": st.column_config.SelectboxColumn("支付人", options=["國", "陞", "現金"]),
                "支付方式": st.column_config.SelectboxColumn("支付方式", options=["星展", "台新", "國泰", "玉山", "現金"]),
                "幣別": st.column_config.SelectboxColumn("幣別", options=["TWD", "JPY", "USD"])
            }, key="expense_editor"
        )
        if st.button("💰 儲存費用", key="save_expenses"):
            conn.update(worksheet="expenses", data=edited_expenses)
            st.rerun()
        
        st.metric("預計花費總額 (TWD)", f"${df_expenses['台幣'].sum():,.0f}")
    else:
        st.info("請先在試算表填入費用欄位：項目, 金額, 幣別, 匯率, 支付人, 支付方式, 備註")

# --- Tab 3: 待辦清單 (非表格呈現) ---
with tab3:
    st.subheader("✅ 旅遊待辦清單")
    df_tasks = get_data("tasks")
    if not df_tasks.empty:
        df_tasks["狀態"] = df_tasks["狀態"].astype(str).str.upper().isin(["TRUE", "1", "YES", "T"]).astype(bool)
        
        # 顯示區：使用 Checkbox 呈現
        st.write("手機查看模式：")
        for idx, row in df_tasks.iterrows():
            st.checkbox(f"**{row['事項']}** ({row['備註'] if pd.notna(row['備註']) else ''})", value=row['狀態'], key=f"task_{idx}", disabled=True)
        
        st.divider()
        with st.expander("🛠️ 管理/更新清單內容"):
            edited_tasks = st.data_editor(df_tasks, num_rows="dynamic", use_container_width=True, hide_index=True, key="tasks_editor")
            if st.button("💾 更新同步清單", key="save_tasks"):
                conn.update(worksheet="tasks", data=edited_tasks)
                st.rerun()

# --- Tab 4: 注意事項 (連結方塊呈現) ---
with tab4:
    st.subheader("📌 注意事項 & 重要連結")
    df_notes = get_data("notes")
    if not df_notes.empty:
        # 連結方塊呈現 (每列 3 個按鈕)
        cols = st.columns(3)
        for idx, row in df_notes.iterrows():
            with cols[idx % 3]:
                if pd.notna(row['網址連結']):
                    st.link_button(f"🔗 {row['內容']}", row['網址連結'], use_container_width=True)
                else:
                    st.info(row['內容'])
        
        st.divider()
        with st.expander("📝 編輯連結與筆記"):
            edited_notes = st.data_editor(df_notes, num_rows="dynamic", use_container_width=True, hide_index=True,
                                         column_config={"網址連結": st.column_config.LinkColumn("網址連結")}, key="notes_editor")
            if st.button("💾 儲存筆記", key="save_notes"):
                conn.update(worksheet="notes", data=edited_notes)
                st.rerun()
