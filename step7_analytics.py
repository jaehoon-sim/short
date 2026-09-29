import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import CLIENT_SECRET_FILE, TOKEN_FILE, HISTORY_FILE

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'youtube'; API_VERSION = 'v3'

def get_authenticated_service():
    if not os.path.exists(CLIENT_SECRET_FILE): return None
    creds = None
    if os.path.exists(TOKEN_FILE):
        try: creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except: return None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try: creds.refresh(Request())
            except: return None
        else: return None
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

def get_best_performing_topic():
    print("📈 [분석] 데이터 조회 중...")
    if not os.path.exists(HISTORY_FILE): return None
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: history = json.load(f)
        if not history: return None

        video_ids = [item['id'] for item in history][-50:] 
        youtube = get_authenticated_service()
        if not youtube: return None

        response = youtube.videos().list(part="statistics", id=','.join(video_ids)).execute()
        best_video = None; max_views = -1

        for item in response['items']:
            views = int(item['statistics'].get('viewCount', 0))
            if views > max_views:
                max_views = views
                best_video = item['id']
        
        if best_video:
            for record in history:
                if record['id'] == best_video:
                    print(f"🔥 최고 조회수 주제: '{record['topic']}' ({max_views}회)")
                    return record['topic']
        return None
    except: return None