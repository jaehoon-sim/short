import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# [비밀 설정] .env 파일 또는 환경변수에서 로드
# ==========================================
def _load_env_file(path):
    if not os.path.exists(path): return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env_file(os.path.join(BASE_DIR, ".env"))

# 1. OpenAI API Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# 2. Google API Key (이미지 생성용, 현재 미사용)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# 3. YouTube Data API Key (트렌드 조회용, 선택. 없으면 yt-dlp로 대체)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# 4. 폰트 설정 (루트 폴더에 파일이 있어야 함)
FONT_PATH = os.path.join(BASE_DIR, "SCDREAM5.OTF")
BOLD_FONT_PATH = os.path.join(BASE_DIR, "SCDREAM6.OTF")

# 5. 유튜브 인증 파일 경로
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# ==========================================
# [폴더 자동 생성 및 경로 설정]
# ==========================================
# 임시 폴더 (이미지, 오디오, 데이터)
TEMP_DIR = os.path.join(BASE_DIR, "temp")
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

# 결과 폴더 (최종 영상)
RESULT_DIR = os.path.join(BASE_DIR, "results")
if not os.path.exists(RESULT_DIR): os.makedirs(RESULT_DIR)

# 로그 폴더 (히스토리)
LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

# BGM 폴더 (하위 폴더는 사용 안 함 → bgm/_unused 에 빼둔 곡은 제외됨)
BGM_DIR = os.path.join(BASE_DIR, "bgm")

# ==========================================
# 상세 파일 경로 정의
# ==========================================
DATA_FILE = os.path.join(TEMP_DIR, "shorts_data.json")
NARRATION_FILE = os.path.join(TEMP_DIR, "narration.mp3")
THUMBNAIL_FILE = os.path.join(TEMP_DIR, "thumbnail.jpg")
TEMP_BG_IMAGE = os.path.join(TEMP_DIR, "temp_thumb_bg.png")
TEMP_AUDIO_FILE = os.path.join(TEMP_DIR, "temp-audio.m4a")

FINAL_VIDEO_FILE = os.path.join(RESULT_DIR, "final_shorts.mp4")
HISTORY_FILE = os.path.join(LOG_DIR, "video_history.json")
TOPIC_HISTORY_FILE = os.path.join(BASE_DIR, "topic_history.txt")
