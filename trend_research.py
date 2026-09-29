import datetime
import urllib.parse
import requests
from config import YOUTUBE_API_KEY

# 트렌드 조사용 검색어 (역사 미스터리 채널 기준)
# (현대 실제 범죄·실종 사건은 실존 피해자 문제로 제외 → 역사 소재 위주)
TREND_QUERIES = [
    "역사 미스터리",
    "역사 미스터리 shorts",
    "세계사 미스터리",
    "조선 미스터리",
    "고대 문명 미스터리",
    "역사 괴담",
]

# YouTube 검색 필터: 이번 달 업로드 + 조회수순
YT_SEARCH_SP = "CAMSAggE"


def _via_youtube_api(queries, per_query, days):
    """YouTube Data API v3 (YOUTUBE_API_KEY 필요)"""
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = []
    for q in queries:
        r = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "id", "q": q, "type": "video", "order": "viewCount",
            "publishedAfter": since, "regionCode": "KR", "relevanceLanguage": "ko",
            "maxResults": per_query, "key": YOUTUBE_API_KEY,
        }, timeout=15)
        r.raise_for_status()
        ids += [it["id"]["videoId"] for it in r.json().get("items", [])]

    ids = list(dict.fromkeys(ids))
    videos = []
    for i in range(0, len(ids), 50):
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
            "part": "snippet,statistics", "id": ",".join(ids[i:i+50]), "key": YOUTUBE_API_KEY,
        }, timeout=15)
        r.raise_for_status()
        for it in r.json().get("items", []):
            videos.append({
                "id": it["id"],
                "title": it["snippet"]["title"],
                "channel": it["snippet"].get("channelTitle", ""),
                "views": int(it["statistics"].get("viewCount", 0)),
            })
    return videos


def _via_ytdlp(queries, per_query):
    """yt-dlp 검색 결과 페이지 (키 불필요)"""
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True,
            "skip_download": True, "playlistend": per_query,
            # 제목 자동번역(영어) 방지 → 원문 한국어 제목 수집
            "extractor_args": {"youtube": {"lang": ["ko"]}},
            "http_headers": {"Accept-Language": "ko-KR,ko;q=0.9"}}
    videos = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        for q in queries:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}&sp={YT_SEARCH_SP}"
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                print(f"   ⚠️ 검색 실패 ({q}): {e}")
                continue
            # 검색 결과는 이미 조회수순 → 한국어 모드에서 조회수가 비어도 순위로 정렬
            for rank, e in enumerate(info.get("entries") or []):
                if not e or not e.get("id") or not e.get("title"): continue
                videos.append({
                    "rank": rank,
                    "id": e["id"],
                    "title": e["title"],
                    "channel": e.get("channel") or e.get("uploader") or "",
                    "views": int(e.get("view_count") or 0),
                })
    return videos


def get_trending_references(top_n=15, per_query=15, days=30):
    """최근 인기 역사/미스터리 영상 목록 (조회수 내림차순). 실패 시 빈 리스트."""
    print("📡 [트렌드] 최근 인기 역사·미스터리 영상 조사 중...")
    videos = []
    if YOUTUBE_API_KEY:
        try:
            videos = _via_youtube_api(TREND_QUERIES, per_query, days)
        except Exception as e:
            print(f"   ⚠️ YouTube API 실패 ({e}). yt-dlp로 대체.")
    if not videos:
        try:
            videos = _via_ytdlp(TREND_QUERIES, per_query)
        except Exception as e:
            print(f"   ⚠️ yt-dlp 실패: {e}")
            return []

    uniq = {}
    for v in videos: uniq.setdefault(v["id"], v)
    ranked = sorted(uniq.values(), key=lambda v: (-v["views"], v.get("rank", 0)))[:top_n]
    print(f"   ✅ 참고 영상 {len(ranked)}개 확보")
    return ranked


def format_references(refs):
    return "\n".join(
        (f"- [{v['views']:,}회] " if v["views"] else "- ") + f"{v['title']} ({v['channel']})"
        for v in refs)


if __name__ == "__main__":
    print(format_references(get_trending_references()))
