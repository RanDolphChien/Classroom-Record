import os
import shutil
import whisper

# 全域變數，用於儲存模型狀態
HAS_WHISPER = False
ai_model = None
HAS_FFMPEG = False

def configure_ffmpeg(base_path):
    """
    Streamlit Cloud / Linux 環境適用：
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
        # 雲端記憶體有限，強烈建議使用 base 模型
        ai_model = whisper.load_model("base") 
        HAS_WHISPER = True
        print("✅ AI 模型載入完成！")
    except Exception as e:
        HAS_WHISPER = False
        print(f"⚠️ 模型載入失敗: {e}")

def process_speech_to_text(file_path):
    """執行語音轉文字的核心邏輯"""
    if HAS_WHISPER and ai_model:
        try:
            # fp16=False 避免在某些 CPU 上出現警告
            result = ai_model.transcribe(
                file_path, 
                fp16=False,
                language="zh", 
                initial_prompt="以下是繁體中文的句子。"
            )
            return result["text"], 0.95
        except Exception as e:
            return f"轉換失敗: {str(e)}", 0.0
    else:
        return f"[模擬模式] 系統檢測到 FFmpeg 或模型未載入。請確認 packages.txt 是否包含 ffmpeg。", 0.0

def get_status():
    """回傳目前系統狀態 (這是原本缺少的函式)"""
    return HAS_WHISPER