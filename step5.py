import os
import json
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from config import FINAL_VIDEO_FILE, DATA_FILE, THUMBNAIL_FILE, HISTORY_FILE, CLIENT_SECRET_FILE, TOKEN_FILE

# 유튜브 API 권한 범위 (youtube.upload 로 영상 + 썸네일 업로드 모두 가능)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    elif os.environ.get("YOUTUBE_TOKEN_JSON"):
        # 클라우드: token.json 내용을 환경변수로 주입
        creds = Credentials.from_authorized_user_info(json.loads(os.environ["YOUTUBE_TOKEN_JSON"]), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.environ.get("HEADLESS"):
            raise RuntimeError("유효한 YouTube 토큰 없음 (HEADLESS 모드라 브라우저 인증 불가). 로컬에서 token.json 재발급 후 YOUTUBE_TOKEN_JSON 갱신 필요")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def build_tags(hashtags, limit=450):
    """해시태그 문자열 → 태그 리스트 (유튜브 태그 총 500자 제한 대비)"""
    tags, total = [], 0
    for t in hashtags.replace("#", " ").split():
        if t in tags: continue
        if total + len(t) + 1 > limit: break
        tags.append(t); total += len(t) + 1
    return tags

def set_thumbnail(youtube, video_id):
    if not os.path.exists(THUMBNAIL_FILE):
        print("   ⚠️ 썸네일 파일 없음 → 건너뜀")
        return
    try:
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(THUMBNAIL_FILE)).execute()
        print("   🖼️ 썸네일 적용 완료")
    except Exception as e:
        # 채널 미인증(전화번호 인증) 시 403 발생 → 영상 업로드 자체는 성공 처리
        print(f"   ⚠️ 썸네일 적용 실패 (채널 인증 필요 여부 확인): {e}")

def record_history(video_id, title):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f: history = json.load(f)
        except Exception: history = []
    history.append({"id": video_id, "topic": title, "timestamp": time.time()})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def upload_video():
    print("🚀 [업로드] 유튜브 서버로 전송 준비 중...")

    if not os.path.exists(FINAL_VIDEO_FILE) or not os.path.exists(DATA_FILE):
        print("❌ 업로드할 파일이 없습니다.")
        return False

    # 데이터 로드
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "역사 미스터리").strip()[:100]  # 유튜브 제목 100자 제한
    script = data.get("script", "")
    hashtags = data.get("hashtags", "#Shorts #역사 #미스터리")
    if "#Shorts" not in hashtags: hashtags = "#Shorts " + hashtags

    # 설명(Description): 제목 + 대본 앞부분 + 구독 유도 + 해시태그
    description = f"""{title}

{script[:200]}...

📜 매일 새로운 역사 속 미스터리를 전해드립니다.
재밌게 보셨다면 구독과 좋아요 부탁드려요! 🔔

※ 본 영상의 이미지는 AI로 생성된 재현 이미지이며, 실제 사료와 다를 수 있습니다.

{hashtags}
"""

    try:
        youtube = get_authenticated_service()

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": build_tags(hashtags),
                "categoryId": "27",  # 27: Education (교육)
                "defaultLanguage": "ko",
                "defaultAudioLanguage": "ko"
            },
            "status": {
                "privacyStatus": os.environ.get("PRIVACY_STATUS", "public"),  # 테스트: PRIVACY_STATUS=private
                "selfDeclaredMadeForKids": False,  # 아동용 아님 (댓글 막히는거 방지)
                "containsSyntheticMedia": True  # AI 생성 콘텐츠 고지
            }
        }

        media = MediaFileUpload(FINAL_VIDEO_FILE, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   Uploading... {int(status.progress() * 100)}%")

        video_id = response.get("id")
        print(f"✅ 업로드 성공! Video ID: {video_id}")

        set_thumbnail(youtube, video_id)
        record_history(video_id, title)
        return True

    except Exception as e:
        print(f"❌ 업로드 실패: {e}")
        return False

if __name__ == "__main__":
    upload_video()
