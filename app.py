import streamlit as st
import os
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import services
from streamlit_mic_recorder import mic_recorder

# --- 1. 頁面與狀態設定 ---
st.set_page_config(page_title="語音評語系統", layout="wide", page_icon="🎙️")

# 設定上傳暫存區 (Streamlit Cloud 檔案是暫時的)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- 2. 初始化功能 ---

@st.cache_resource
def init_app_modules():
    """初始化 AI 模型，並快取結果避免重複載入"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    services.configure_ffmpeg(base_path)
    services.init_ai_model()
    return services.get_status()

# 建立資料庫連線
conn = st.connection("postgresql", type="sql")

def init_db():
    with conn.session as s:
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                accuracy FLOAT DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        s.commit()

init_db()

# 初始化 AI
has_whisper = init_app_modules()

# --- 3. 輔助函式 ---

def save_transcript_to_db(filename, content, accuracy):
    """將結果寫入資料庫"""
    # 使用參數化查詢防止 SQL Injection
    query = text("""
        INSERT INTO transcripts (filename, content, accuracy, created_at)
        VALUES (:f, :c, :a, :d)
    """)
    with conn.session as s:
        s.execute(query, {
            "f": filename, 
            "c": content, 
            "a": accuracy, 
            "d": datetime.now()
        })
        s.commit()

def delete_transcript(t_id):
    """刪除紀錄"""
    with conn.session as s:
        s.execute(text("DELETE FROM transcripts WHERE id = :id"), {"id": t_id})
        s.commit()
    st.rerun() # 重新整理頁面

# --- 4. 側邊欄：控制面板 ---
with st.sidebar:
    st.title("🎙️ 語音評語系統")
    
    # 狀態指示燈
    if has_whisper:
        st.success("🟢 AI 引擎就緒")
    else:
        st.warning("🟠 模擬模式 (無 FFmpeg/Model)")
        
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🎤 線上錄音", "📂 檔案上傳"])
    
    with tab1:
        st.write("點擊按鈕開始/停止錄音：")
        # 使用第三方元件錄音
        audio_bytes = mic_recorder(
            start_prompt="開始錄音",
            stop_prompt="停止錄音",
            key='recorder',
            format="wav"
        )
        
        if audio_bytes:
            # st.audio(audio_bytes['bytes'], format="audio/wav")
            st.audio(audio_bytes['bytes'], format="audio/webm")
            if st.button("辨識錄音", key="transcribe_mic"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # filename = f"mic_record_{timestamp}.wav"
                filename = f"mic_record_{timestamp}.webm"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                
                with open(file_path, "wb") as f:
                    f.write(audio_bytes['bytes'])
                
                with st.spinner("AI 正在聽寫中..."):
                    txt, acc = services.process_speech_to_text(file_path)
                    save_transcript_to_db(filename, txt, acc)
                    st.success("✅ 完成！")
                    st.rerun()

    with tab2:
        uploaded_file = st.file_uploader("選擇音檔", type=['mp3', 'wav', 'm4a'])
        if uploaded_file and st.button("上傳並辨識"):
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner("AI 正在分析..."):
                txt, acc = services.process_speech_to_text(file_path)
                save_transcript_to_db(uploaded_file.name, txt, acc)
                st.success("✅ 完成！")
                st.rerun()

# --- 5. 主畫面：資料列表 ---
st.header("歷史紀錄")

# 搜尋框
# search_term = st.text_input("搜尋內容關鍵字", prefix="🔍")
search_term = st.text_input("🔍 搜尋內容關鍵字", placeholder="輸入關鍵字...")

# 查詢資料庫
if search_term:
    sql = "SELECT * FROM transcripts WHERE content ILIKE :q ORDER BY created_at DESC"
    # df = conn.query(sql, params={"q": f"%{search_term}%"})
    df = conn.query(sql, params={"q": f"%{search_term}%"}, ttl=0)
else:
    sql = "SELECT * FROM transcripts ORDER BY created_at DESC"
    # df = conn.query(sql)
    df = conn.query(sql, ttl=0)

# 顯示列表
if not df.empty:
    for idx, row in df.iterrows():
        with st.container():
            # 卡片式佈局
            c1, c2 = st.columns([0.85, 0.15])
            
            with c1:
                st.subheader(f"📄 {row['filename']}")
                st.caption(f"建立時間: {row['created_at']} | 準確度: {row['accuracy']}")
                
                # 編輯模式切換 (使用 Session State)
                edit_key = f"edit_{row['id']}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                if st.session_state[edit_key]:
                    new_content = st.text_area("編輯內容", value=row['content'], height=150, key=f"area_{row['id']}")
                    col_save, col_cancel = st.columns(2)
                    if col_save.button("儲存", key=f"save_{row['id']}"):
                        with conn.session as s:
                            s.execute(
                                text("UPDATE transcripts SET content = :c WHERE id = :id"),
                                {"c": new_content, "id": row['id']}
                            )
                            s.commit()
                        st.session_state[edit_key] = False
                        st.rerun()
                    
                    if col_cancel.button("取消", key=f"cancel_{row['id']}"):
                        st.session_state[edit_key] = False
                        st.rerun()
                else:
                    st.info(row['content'])

            with c2:
                # 操作按鈕區
                if st.button("✏️", key=f"btn_edit_{row['id']}", help="編輯"):
                    st.session_state[edit_key] = True
                    st.rerun()
                
                if st.button("🗑️", key=f"btn_del_{row['id']}", help="刪除"):
                    delete_transcript(row['id'])
            
            st.markdown("---")
else:
    st.info("目前沒有任何紀錄，請從側邊欄新增。")