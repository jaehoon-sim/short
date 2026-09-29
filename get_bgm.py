import os
import yt_dlp
from config import BGM_DIR

# BGM 저장 폴더
if not os.path.exists(BGM_DIR):
    os.makedirs(BGM_DIR)

# 역사 미스터리 다큐 톤 BGM 검색 키워드 리스트
# [주의] 'No Copyright' 키워드를 포함하여 저작권 경고 위험을 최소화합니다.
# 받은 곡은 직접 들어보고 분위기에 안 맞으면 bgm/_unused 로 옮기세요.
SEARCH_KEYWORDS = [
    "dark mystery documentary background music no copyright",  # 미스터리 도입부
    "suspense investigation background music no copyright",    # 추리/전개
    "dark ambient cinematic music no copyright",               # 무거운 분위기
    "epic historical orchestral music no copyright",           # 전쟁/왕조
    "eerie horror ambient music no copyright"                  # 저주/괴담
]

# 키워드당 다운로드할 개수
DOWNLOAD_COUNT_PER_KEYWORD = 3 

def download_bgm():
    print("🎵 [음악 보급관] BGM 자동 수집을 시작합니다...")
    print(f"📂 저장 경로: {BGM_DIR}")

    # yt-dlp 설정
    ydl_opts = {
        'format': 'bestaudio/best', # 최고의 오디오 음질
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3', # MP3로 변환
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(BGM_DIR, '%(title)s.%(ext)s'), # 파일명 저장 규칙
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        # 1분 ~ 3분 사이의 영상만 다운로드 (너무 긴 믹스셋 방지)
        'match_filter': yt_dlp.utils.match_filter_func("duration > 60 & duration < 300"),
    }

    total_downloaded = 0

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for keyword in SEARCH_KEYWORDS:
            print(f"\n🔍 검색 중: '{keyword}'...")
            try:
                # ytsearch{N}: 키워드로 N개 검색
                search_query = f"ytsearch{DOWNLOAD_COUNT_PER_KEYWORD}:{keyword}"
                ydl.download([search_query])
                total_downloaded += DOWNLOAD_COUNT_PER_KEYWORD
            except Exception as e:
                print(f"❌ 다운로드 실패 ({keyword}): {e}")

    print("\n" + "="*50)
    print(f"🎉 BGM 보급 완료! 총 {total_downloaded}개 시도함.")
    print(f"📂 'bgm' 폴더를 확인하세요. 이제 랜덤으로 사용됩니다.")
    print("="*50)

if __name__ == "__main__":
    download_bgm()