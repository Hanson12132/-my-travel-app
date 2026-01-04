import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import plotly.express as px  # 用於繪製圓餅圖

# 1. 網頁基本設定
st.set_page_config(
    page_title="🍵 202602日本關西", 
    layout="wide", 
    page_icon="🍵"
)

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    try:
        # ttl=0 確保抓取即時資料
        data = conn.read(worksheet=sheet_name, ttl=0)
        data = data.dropna(how="all")
        # 清除欄位名稱前後空白
        data.columns = [c.strip() for c in data.columns]
        return data
    except Exception as e:
        return pd.DataFrame()

# --- 側邊欄：旅遊工具箱 (隱藏分頁清單，僅顯示工具) ---
with st.sidebar:
    st.header("🧳 旅遊工具箱")
    st.link_button("🌐 Visit Japan Web", "https://vjw-lp.digital.go.jp/zh-hant/")
    st.link_button("🏮 日本氣象查詢 (Yahoo)", "https://weather.yahoo.co.jp/weather/")
    st.link_button("🔤 Google 翻譯", "https://translate.google.com/")
    
    st.divider()
    
    st.subheader("💱 快速匯率換算")
    rate_tool = st.number_input("1 JPY 換 TWD", value=0.2150, format="%.4f")
    jpy_tool = st.number_input("輸入日幣", min_value=0)
    st.metric("等於台幣", f"${round(jpy_tool * rate_tool, 2)}")
    
    st.divider()
    if st.button("🔄 強制刷新雲端資料"):
        st.cache_data.clear()
        st.rerun()

# --- 主畫面標題 ---
st.title("🍵 202602 日本關西")

tab1, tab2, tab3, tab4 = st.tabs(["📅 每日行程", "💰 費用明細", "✅ 待辦清單", "📌 注意事項"])

# --- Tab 1: 每日行程 ---
with tab1:
    df_itinerary = get_data("itinerary")
    if not df_itinerary.empty:
        # 資料轉換與排序
        df_itinerary["日期"] = pd.to_datetime(df_itinerary["日期"], errors='coerce')
        df_itinerary = df_itinerary.dropna(subset=["日期"])
        df_itinerary["日期"] = df_itinerary["日期"].dt.date
        
        # A. 導覽模式 (優先顯示)
        st.subheader("🚩 旅遊導覽模式")
        today = date.today()
        unique_dates = sorted(df_itinerary["日期"].unique())
        for i, d in enumerate(unique_dates):
            is_past = d < today
            with st.expander(f"Day {i+1}：{d} {'⌛' if is_past else '🚩'}", expanded=not is_past):
                day_data = df_itinerary[df_itinerary["日期"] == d].sort_values("時間")
                for _, row in day_data.iterrows():
                    col_t, col_c = st.columns([1, 5])
                    col_t.info(f"**{row.get('時間', '')}**")
                    with col_c:
                        st.write(f"**{row.get('活動', '')}**")
                        if pd.notna(row.get('備註')): st.caption(f"📝 {row['備註']}")
                        # 串連地圖連結按鈕
                        map_url = row.get('地圖連結', '')
                        if pd.notna(map_url) and str(map_url).startswith("http"):
                            st.link_button("📍 開啟導航", map_url)
        
        st.divider()
        # B. 行程編輯器 (放在導覽下方)
        st.subheader("📝 行程編輯器")
        edited_itinerary = st.data_editor(
            df_itinerary, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
                "地圖連結": st.column_config.LinkColumn("地圖連結")
            }, key="itinerary_editor"
        )
        if st.button("💾 儲存行程更改", key="save_itinerary"):
            conn.update(worksheet="itinerary", data=edited_itinerary)
            st.rerun()
    else:
        st.info("行程表目前無資料。標題需包含：日期, 時間, 活動, 備註, 地圖連結")

# --- Tab 2: 費用明細 (圓餅圖與下拉選單) ---
with tab2:
    df_expenses = get_data("expenses")
    if not df_expenses.empty:
        # 強制轉換數值，解決後台編輯無法計算問題
        df_expenses["金額"] = pd.to_numeric(df_expenses["金額"], errors='coerce').fillna(0)
        df_expenses["匯率"] = pd.to_numeric(df_expenses["匯率"], errors='coerce').fillna(1)
        df_expenses["台幣總計"] = df_expenses["金額"] * df_expenses["匯率"]
        
        st.subheader("📊 支出圓餅圖統計")
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            if '支付人' in df_expenses.columns:
                fig1 = px.pie(df_expenses, values='台幣總計', names='支付人', title='支付人佔比')
                st.plotly_chart(fig1, use_container_width=True)
        
        with col_pie2:
            if '支付方式' in df_expenses.columns:
                fig2 = px.pie(df_expenses, values='台幣總計', names='支付方式', title='支付方式佔比')
                st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.subheader("📝 費用編輯器")
        # 編輯時暫時移除計算欄位
        edit_df_exp = df_expenses.drop(columns=["台幣總計"]) if "台幣總計" in df_expenses.columns else df_expenses
        edited_expenses = st.data_editor(
            edit_df_exp, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "支付人": st.column_config.SelectboxColumn("支付人", options=["國", "陞", "現金"]),
                "支付方式": st.column_config.SelectboxColumn("支付方式", options=["星展", "台新", "國泰", "玉山", "現金"]),
                "幣別": st.column_config.SelectboxColumn("幣別", options=["TWD", "JPY", "USD"])
            }, key="expense_editor"
        )
        if st.button("💰 儲存費用", key="save_expenses"):
            conn.update(worksheet="expenses", data=edited_expenses)
            st.rerun()
        
        st.metric("總花費預估 (TWD)", f"${df_expenses['台幣總計'].sum():,.0f}")
    else:
        st.info("費用表目前無資料。標題需包含：項目, 金額, 幣別, 匯率, 支付人, 支付方式, 備註")

# --- Tab 3: 待辦清單 (非表格呈現) ---
with tab3:
    st.subheader("✅ 待辦事項檢查")
    df_tasks = get_data("tasks")
    if not df_tasks.empty:
        # 顯示區：列表形式
        if '狀態' in df_tasks.columns:
            df_tasks["狀態"] = df_tasks["狀態"].astype(str).str.upper().isin(["TRUE", "1", "YES", "T"]).astype(bool)
        
        for idx, row in df_tasks.iterrows():
            st.checkbox(f"**{row.get('事項', '未命名')}**", value=row.get('狀態', False), key=f"t_view_{idx}", disabled=True)
            if pd.notna(row.get('備註', '')):
                st.caption(f"└ {row['備註']}")
        
        st.divider()
        with st.expander("🛠️ 管理待辦清單"):
            edited_tasks = st.data_editor(df_tasks, num_rows="dynamic", use_container_width=True, hide_index=True, key="tasks_editor")
            if st.button("💾 更新清單內容", key="save_tasks"):
                conn.update(worksheet="tasks", data=edited_tasks)
                st.rerun()
    else:
        st.info("請在 tasks 分頁填入資料（事項, 狀態, 備註）。")

# --- Tab 4: 注意事項 (連結方塊呈現) ---
with tab4:
    st.subheader("📌 重要連結")
    df_notes = get_data("notes")
    if not df_notes.empty:
        # 連結方塊呈現
        n_cols = 3
        cols = st.columns(n_cols)
        for idx, row in df_notes.iterrows():
            with cols[idx % n_cols]:
                content = row.get('內容', f'連結 {idx+1}')
                url = row.get('網址連結', '')
                if pd.notna(url) and str(url).startswith("http"):
                    st.link_button(f"🔗 {content}", url, use_container_width=True)
                else:
                    st.info(content)
        
        st.divider()
        with st.expander("📝 編輯筆記連結"):
            edited_notes = st.data_editor(
                df_notes, num_rows="dynamic", use_container_width=True, hide_index=True,
                column_config={"網址連結": st.column_config.LinkColumn("網址連結")}, 
                key="notes_editor"
            )
            if st.button("💾 儲存筆記", key="save_notes"):
                conn.update(worksheet="notes", data=edited_notes)
                st.rerun()
