import time
import os
import sys
import json
import random
from config import DATA_FILE, FINAL_VIDEO_FILE, TEMP_DIR, TOPIC_HISTORY_FILE
import trend_research

try:
    import step1, step2, step3, step4, step5
    import step6_thumbnail as step6
    import step7_analytics as step7
except ImportError as e:
    print(f"❌ 파일 누락: {e.name}.py")
    exit()

HISTORY_FILE = TOPIC_HISTORY_FILE

def cleanup_files():
    print("🧹 [청소] 임시 파일 정리")
    try:
        if os.path.exists(FINAL_VIDEO_FILE): os.remove(FINAL_VIDEO_FILE)
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        for f in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, f)
            if os.path.isfile(file_path): os.remove(file_path)
    except: pass

def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]

def save_history(topic):
    history = load_history()
    history.append(topic)
    if len(history) > 20: history = history[-20:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(history))
    return history

# -----------------------------------------------------------
# 🧠 AI 브레인: 유튜브 인기 콘텐츠 기반 주제 선정
# -----------------------------------------------------------
# [역사 미스터리 카테고리] 트렌드 조사 실패 시 백업용
HISTORY_CATEGORIES = {
    "Lost Civilizations": "사라진 아틀란티스, 잉카의 황금 도시 파이티티, 폼페이 최후의 날",
    "Cursed Objects": "투탕카멘의 저주, 호프 다이아몬드, 애나벨 인형의 실제 이야기",
    "Unsolved Crimes": "잭 더 리퍼, 조디악 킬러, 디아틀로프 실종 사건",
    "War Mysteries": "2차대전 중 사라진 나치 황금 열차, 크리스마스 정전의 기적",
    "Ancient Tech": "안티키테라 기계, 피라미드 건축의 비밀, 바그다드 전지",
    "Dark History": "중세 마녀사냥, 731부대, MK울트라 프로젝트",
    "Royal Secrets": "사도세자의 뒤주, 헨리 8세의 여인들, 아나스타샤 공주의 생존설"
}

def _ask_topic(prompt):
    response = step1.client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a YouTube history documentary PD. Output JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.9
    )
    result = json.loads(response.choices[0].message.content)
    topic = (result.get("topic") or "").strip().replace('"', '')
    if not topic: raise Exception("Empty topic")
    return topic, result

def brain_storming():
    print("\n🧠 [AI] 요즘 뜨는 역사 미스터리를 조사합니다...")

    recent_topics = load_history()
    print(f"🚫 [금지 목록] 최근 {len(recent_topics)}개 주제 제외")
    banned = ', '.join(recent_topics) if recent_topics else "없음"

    refs = trend_research.get_trending_references()

    try:
        if refs:
            prompt = f"""
            너는 '역사 미스터리 & 다큐멘터리' 쇼츠 채널의 PD야.
            아래는 최근 한 달간 유튜브에서 조회수가 높았던 역사/미스터리 영상 목록이야.

            [인기 영상 (조회수순)]
            {trend_research.format_references(refs)}

            [지시사항]
            1. 목록에서 시청자 반응이 좋은 **소재·시대·키워드·후킹 방식**의 공통 패턴을 파악해.
            2. 그 패턴에 올라탈 수 있는 **구체적인 역사적 사건이나 인물 하나**를 60초 쇼츠 주제로 골라.
            3. 인기 영상의 제목이나 내용을 그대로 베끼지 말고, 같은 관심사를 다른 사건/각도로 풀어.
            4. 위키백과에 문서가 있을 만큼 잘 알려지고 검증 가능한 실제 사건·인물만 선택해 (지어낸 인물·사건, 음모론 단정 금지).
            5. 최근 수십 년 내 실제 범죄·실종 사건처럼 실존 피해자·유족이 있는 사건은 제외해.
            6. **이미 다룬 주제 금지:** {banned}
            7. 제목은 다큐멘터리처럼 무게감 있으면서도 미스터리하게, 40자 이내 한국어.

            [JSON 출력]
            {{
                "topic": "한국어 제목 한 줄",
                "category": "영문 카테고리 (예: Unsolved Crimes, Royal Secrets)",
                "trend_pattern": "참고한 인기 패턴 요약 한 줄",
                "reference_titles": ["가장 많이 참고한 인기 영상 제목 1~3개"]
            }}
            """
            topic, result = _ask_topic(prompt)
            genre = result.get("category") or "History"
            print(f"📈 [트렌드 패턴] {result.get('trend_pattern', '')}")
            for t in result.get("reference_titles", [])[:3]:
                print(f"   ↳ 참고: {t}")
        else:
            print("⚠️ 트렌드 데이터 없음 → 카테고리 랜덤 모드")
            genre = random.choice(list(HISTORY_CATEGORIES.keys()))
            print(f"📜 [카테고리] '{genre}' 모드")
            prompt = f"""
            너는 '역사 미스터리 & 다큐멘터리' 전문 PD야.

            [카테고리: {genre}]
            - 설명: {HISTORY_CATEGORIES[genre]}

            [지시사항]
            1. 위 카테고리에서 대중들이 가장 흥미로워할 만한 **구체적인 사건이나 인물**을 선정해.
            2. 너무 뻔한 주제보다는 '이면의 숨겨진 이야기'에 초점을 맞춰.
            3. **이미 다룬 주제 금지:** {banned}
            4. 제목은 다큐멘터리처럼 무게감 있으면서도 미스터리하게, 40자 이내 한국어.

            [JSON 출력]
            {{ "topic": "한국어 제목 한 줄" }}
            """
            topic, _ = _ask_topic(prompt)

        print(f"🕯️ [선정된 주제] {topic}")
        save_history(topic)
        return topic, genre

    except Exception as e:
        print(f"⚠️ 주제 선정 실패 ({e}). 백업 주제 사용.")
        backup = "타이타닉호 침몰 1시간 전의 진실"
        save_history(backup)
        return backup, "History"

# -----------------------------------------------------------
# 🏭 메인 파이프라인
# -----------------------------------------------------------
def run_automation_pipeline():
    if os.path.exists(FINAL_VIDEO_FILE) and os.path.exists(DATA_FILE):
        print("\n♻️ [재시도] 영상 복구 중...")
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: title = json.load(f).get("title", "Unknown")
        except: title = "Unknown"
        if step5.upload_video():
            print(f"✨ 재업로드 성공! '{title}'"); cleanup_files(); return True
        else: return False

    topic, genre = brain_storming()
    print("\n" + "="*50 + f"\n🎥 역사 다큐 제작: '{topic}'")
    
    plan_data = step1.generate_shorts_plan(topic, genre)
    if not plan_data: return False
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(plan_data, f, ensure_ascii=False, indent=4)
    time.sleep(1)

    if not step2.create_voice_narration_direct(plan_data['script']): return False
    time.sleep(1)

    if not step3.generate_dalle_images(plan_data): return False
    # step4는 이미 1.3배속 기능이 있으므로 그대로 사용
    if not step4.create_final_video_documentary(): return False

    step6.generate_thumbnail()
    time.sleep(1)

    if step5.upload_video():
        print(f"\n✨ '{topic}' 업로드 완료!"); cleanup_files(); return True
    else: return False

if __name__ == "__main__":
    # --once : 1편만 만들고 종료 (클라우드 스케줄러용, 실패 시 exit 1)
    if "--once" in sys.argv:
        print(f"\n🎬 [단발 실행] 트렌드 기반 역사 미스터리 1편")
        sys.exit(0 if run_automation_pipeline() else 1)

    print(f"\n♾️ [무한 역사 공장] 2시간 간격 / 트렌드 기반 미스터리")

    cycle_count = 1
    while True:
        print(f"\n📢 [{cycle_count}번째 에피소드]")
        
        if run_automation_pipeline():
            print(f"\n✅ 성공! 다음 방송까지 2시간 대기.")
        else:
            print(f"\n⚠️ 실패. 2시간 대기 후 재시도.")
        
        cycle_count += 1
        wait_seconds = 7200 + random.randint(-600, 600)
        next_time = time.strftime('%H:%M', time.localtime(time.time() + wait_seconds))
        print(f"💤 {wait_seconds//60}분간 휴식... (다음 예정: {next_time})")
        time.sleep(wait_seconds)