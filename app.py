import streamlit as st
import pandas as pd

# 網頁基本設定
st.set_page_config(page_title="我們的旅遊手冊", layout="wide")

st.title("✈️ 專屬旅遊規劃手冊")

# 這裡儲存你的初始資料 (你可以直接在這裡改字)
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = pd.DataFrame([
        {"時間": "10:00", "活動": "桃園機場報到", "備註": "記得帶護照", "地圖": "https://google.com"},
        {"時間": "14:00", "活動": "抵達東京", "備註": "領取 JR Pass", "地圖": "https://google.com"}
    ])

# 側邊欄：匯率換算
st.sidebar.header("💱 匯率換算")
rate = st.sidebar.number_input("1 日幣換台幣", value=0.215)
jpy = st.sidebar.number_input("輸入日幣金額", min_value=0)
st.sidebar.write(f"等於台幣：{round(jpy * rate, 1)} 元")

# 分頁設計
tab1, tab2, tab3 = st.tabs(["📅 行程規劃", "💰 費用/願望", "📝 待辦清單"])

with tab1:
    st.subheader("💡 編輯行程 (直接點擊表格即可修改)")
    # 讓你可以像 Excel 一樣編輯
    st.session_state.itinerary = st.data_editor(st.session_state.itinerary, num_rows="dynamic", use_container_width=True)
    
    st.divider()
    st.subheader("📍 當下查閱模式")
    for index, row in st.session_state.itinerary.iterrows():
        col1, col2 = st.columns([1, 4])
        col1.info(row['時間'])
        with col2:
            st.write(f"**{row['活動']}**")
            st.caption(row['備註'])
            if row['地圖']:
                st.link_button("🗺️ 開啟導航", row['地圖'])

with tab2:
    st.subheader("🛍️ 費用與購物清單")
    st.write("可在下方記錄預計開支：")
    expense_df = pd.DataFrame([{"項目": "機票", "日幣": 50000}, {"項目": "住宿", "日幣": 30000}])
    st.data_editor(expense_df, num_rows="dynamic", use_container_width=True)

with tab3:
    st.subheader("✅ 出發前待辦")
    todo = st.checkbox("辦理旅平險")
    todo2 = st.checkbox("換外幣")
    st.text_input("新增其他待辦...")
