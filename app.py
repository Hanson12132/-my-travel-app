import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 網頁基本設定
st.set_page_config(page_title="✈️ 我們的雲端旅遊手冊", layout="wide", page_icon="🌍")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    # 讀取資料並清除全空行
    return conn.read(worksheet=sheet_name).dropna(how="all")

st.title("🌍 專屬旅遊規劃 & 指引手冊")

# --- 分頁設定 ---
tab1, tab2, tab3, tab4 = st.tabs(["📅 每日行程", "💰 費用明細", "✅ 待辦清單", "📌 注意事項"])

# --- Tab 1: 每日行程 (含智慧收合) ---
with tab1:
    st.subheader("行程編輯器")
    df_itinerary = get_data("itinerary")
    # 確保日期欄位是日期型態
    df_itinerary["日期"] = pd.to_datetime(df_itinerary["日期"]).dt.date
    
    edited_itinerary = st.data_editor(
        df_itinerary, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={"地圖連結": st.column_config.LinkColumn("地圖連結")}
    )
    
    if st.button("💾 儲存行程更改", key="save_itinerary"):
        conn.update(worksheet="itinerary", data=edited_itinerary)
        st.success("行程已同步至雲端！")
        st.rerun()

    st.divider()
    st.subheader("🚩 行程導覽模式")
    
    today = date.today()
    # 依照日期分組顯示
    unique_dates = sorted(edited_itinerary["日期"].unique())
    
    for i, d in enumerate(unique_dates):
        # 智慧收合邏輯：過去的天數自動收起，今天與未來預設展開
        is_past = d < today
        status_icon = "⌛" if is_past else "🚩"
        expander_label = f"Day {i+1}：{d} {status_icon} {'(已結束)' if is_past else ''}"
        
        with st.expander(expander_label, expanded=not is_past):
            day_data = edited_itinerary[edited_itinerary["日期"] == d].sort_values("時間")
            for _, row in day_data.iterrows():
                col1, col2 = st.columns([1, 4])
                col1.info(f"**{row['時間']}**")
                with col2:
                    st.write(f"**{row['活動']}**")
                    if pd.notna(row['備註']): st.caption(f"備註：{row['備註']}")
                    if pd.notna(row['地圖連結']): st.link_button("🗺️ 導航", row['地圖連結'])

# --- Tab 2: 費用明細 (多幣別與備註) ---
with tab2:
    st.subheader("多幣別記帳本")
    df_expenses = get_data("expenses")
    
    # 編輯費用表格
    edited_expenses = st.data_editor(
        df_expenses, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "幣別": st.column_config.SelectboxColumn("幣別", options=["TWD", "JPY", "USD", "EUR", "KRW"]),
            "金額": st.column_config.NumberColumn("金額", min_value=0),
            "匯率": st.column_config.NumberColumn("匯率", format="%.4f")
        }
    )
    
    if st.button("💰 儲存費用更改", key="save_expenses"):
        conn.update(worksheet="expenses", data=edited_expenses)
        st.success("預算更新成功！")
        st.rerun()

    # 自動換算台幣總額
    if not edited_expenses.empty:
        total_twd = (edited_expenses["金額"] * edited_expenses["匯率"]).sum()
        st.metric("總支出估計 (TWD)", f"${total_twd:,.0f}")
        
        # 顯示計算後的即時清單
        calc_df = edited_expenses.copy()
        calc_df["台幣換算"] = calc_df["金額"] * calc_df["匯率"]
        st.dataframe(calc_df[["項目", "幣別", "金額", "台幣換算", "備註"]], use_container_width=True)

# --- Tab 3: 待辦清單 (簡化版) ---
with tab3:
    st.subheader("出發前待辦")
    st.checkbox("辦理保險")
    st.checkbox("確認護照")
    st.checkbox("領取外幣")
    st.text_input("新增其他...")

# --- Tab 4: 注意事項 (常用網站連結表格) ---
with tab4:
    st.subheader("📌 重要資訊與常用連結")
    df_notes = get_data("notes")
    
    # 使用表格呈現，連結欄位設定為可點擊
    edited_notes = st.data_editor(
        df_notes, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "網址連結": st.column_config.LinkColumn("網址連結", display_text="點擊開啟")
        }
    )
    
    if st.button("📌 儲存筆記更改", key="save_notes"):
        conn.update(worksheet="notes", data=edited_notes)
        st.success("筆記已存檔！")
        st.rerun()
        
    st.info("💡 這裡可以存放飯店官網、電子門票連結、或是當地的緊急聯絡電話。")
