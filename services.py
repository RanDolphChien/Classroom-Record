import os
import shutil
import whisper

# 全域變數
HAS_WHISPER = False
ai_model = None
HAS_FFMPEG = False

def configure_ffmpeg(base_path):
    """
    Streamlit Cloud 版本：
    檢查系統路徑中是否有 ffmpeg (由 packages.txt 安裝)
    """
    global HAS_FFMPEG
    
    # shutil.which 會在系統 PATH 中尋找執行檔 (跨平台通用)
    if shutil.which("ffmpeg"):
        HAS_FFMPEG = True
        return True
    
    HAS_FFMPEG = False
    return False

def init_ai_model():
    """載入 Whisper 模型"""
    global ai_model, HAS_WHISPER
    
    print("--- 系統初始化中 ---")
    if not HAS_FFMPEG:
        print("⚠️ 找不到 FFmpeg，無法處理音訊。")
        HAS_WHISPER = False
        return

    try:
        print("正在載入 AI 模型...")
        # 雲端記憶體有限，強烈建議使用 base 模型，避免記憶體不足崩潰
        ai_model = whisper.load_model("base") 
        HAS_WHISPER = True
        print("✅ AI 模型載入完成！")
    except Exception as e:
        HAS_WHISPER = False
        print(f"⚠️ 模型載入失敗: {e}")

# ... (process_speech_to_text 維持不變)