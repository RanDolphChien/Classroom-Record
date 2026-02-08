import os
import shutil
import whisper

# ... (全域變數保持不變)

def configure_ffmpeg(base_path):
    """
    Streamlit Cloud 會透過 packages.txt 安裝 ffmpeg。
    所以這裡只要檢查系統路徑中是否存在即可。
    """
    global HAS_FFMPEG
    
    # 檢查系統中是否有 ffmpeg 指令
    if shutil.which("ffmpeg"):
        HAS_FFMPEG = True
        return True
    
    HAS_FFMPEG = False
    return False

# ... (init_ai_model 與 process_speech_to_text 保持不變)
# 建議：在 Cloud 免費版上，模型建議改用 "base" 或 "small"，"medium" 可能會因為記憶體不足而當機。