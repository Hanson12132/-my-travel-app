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
        data = conn.read(worksheet=sheet_name).dropna(how="all")
        return data
    except Exception as e:
        st.error(f"找不到分頁【{sheet_name}】，請確認名稱是否正確。")
        return pd.DataFrame()

st.title("🌍 專屬旅遊規劃 & 指引手冊")

tab1, tab2, tab3, tab4 = st.tabs(["📅 每日行程", "💰 費用明細", "✅ 待辦清單", "📌 注意事項"])

# --- Tab 1 & 2 (保持之前的邏輯，省略不寫以節省篇幅，請保留你原本的程式碼) ---
# ... (這裡請維持你原本 Tab 1 和 Tab 2 的代碼)

# --- Tab 3: 待辦清單 (強化核取方塊功能) ---
with tab3:
    st.subheader("✅ 旅遊待辦清單")
    st.write("點擊【狀態】欄位的方塊即可勾選，完成後請點擊下方的儲存按鈕。")
    
    df_tasks = get_data("tasks")
    
    if not df_tasks.empty:
        # 【關鍵修正】確保狀態欄位是布林值 (True/False)，這樣才會顯示成勾選框
        # 我們將所有的 "TRUE", "True", 1 轉換為真正的布林值
        df_tasks["狀態"] = df_tasks["狀態"].apply(lambda x: True if str(x).upper() == "TRUE" else False)
        
        # 使用 data_editor 產生核取方塊
        edited_tasks = st.data_editor(
            df_tasks,
            num_rows="dynamic", # 允許你在網頁上直接新增或刪除任務
            use_container_width=True,
            column_config={
                "狀態": st.column_config.CheckboxColumn(
                    "狀態",
                    help="勾選代表已完成",
                    default=False,
                ),
                "事項": st.column_config.TextColumn("事項", width="large"),
                "備註": st.column_config.TextColumn("備註", width="medium")
            },
            key="tasks_editor"
        )
        
        if st.button("💾 儲存待辦清單狀態", key="btn_save_tasks"):
            conn.update(worksheet="tasks", data=edited_tasks)
            st.success("清單已成功同步至 Google Sheets！")
            st.rerun() # 重新整理網頁以確保顯示最新狀態
    else:
        st.info("請在 Google Sheets 的 tasks 分頁填入資料（標題：事項、狀態、備註）。")

# --- Tab 4: 注意事項 (保持原本邏輯) ---
with tab4:
    st.subheader("📌 連結與筆記")
    df_notes = get_data("notes")
    if not df_notes.empty:
        edited_notes = st.data_editor(df_notes, num_rows="dynamic", use_container_width=True, key="notes_editor")
        if st.button("📌 儲存筆記"):
            conn.update(worksheet="notes", data=edited_notes)
            st.success("筆記已同步！")
            st.rerun()
