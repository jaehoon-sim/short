import json
import random
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_shorts_plan(topic, genre="History"):
    print(f"🧠 [기획] 역사 다큐멘터리 '{topic}' 설계 중...")

    # [비주얼 스타일: 역사적 무게감]
    visual_styles = [
        "Vintage Archival Footage (Black & White, grainy 1920s film style)",
        "Renaissance Oil Painting (Da Vinci style, cracked paint texture, realistic)",
        "Faded Kodachrome Photograph (1970s retro vibe, slightly blurred, nostalgia)",
        "Detailed Historical Illustration (Etching style, old paper texture, ink lineart)",
        "Cinematic Period Drama (Dark moody lighting, movie screenshot style)"
    ]
    selected_style = random.choice(visual_styles)
    print(f"🎨 [화풍] {selected_style}")

    # 공통 지침
    visual_instruction = f"""
    [비주얼 프롬프트 작성 규칙]
    1. **고증 준수:** 현대적인 물건(스마트폰, 자동차 등)이 나오지 않도록 주의해. 시대적 배경에 맞는 옷과 배경을 묘사해.
    2. **분위기:** 미스터리하고 어둡고 무거운 분위기.
    3. **화풍 통일:** 모든 프롬프트 끝에 "{selected_style}"을 반드시 붙여.
    """

    prompt = f"""
    너는 '미스터리 역사 다큐멘터리' 전문 작가야.
    주제 '{topic}'에 대해 시청자가 몰입할 수 있는 스크립트와 이미지를 기획해.

    [스크립트 작성 규칙 - 분량 중요]
    1. **목표 시간:** 최종 영상은 1.3배속으로 재생되어 60초가 되어야 함.
    2. **글자 수:** 따라서 원본 스크립트는 **공백 포함 약 650자 ~ 700자** 분량으로 넉넉하게 작성해. (너무 짧으면 안 됨)
    3. **톤앤매너:** 진지하고 미스터리한 내레이션 (반말, 예: "1912년, 그날 밤은 유난히 추웠어...")
    4. **구조:**
       - 도입 (0~10초): 사건의 발단, 호기심 자극.
       - 전개 (10~40초): 구체적인 미스터리 내용, 증거, 의혹.
       - 절정/결말 (40~60초): 밝혀지지 않은 진실, 혹은 시청자에게 던지는 질문.

    {visual_instruction}

    [추가 요청]
    - **hashtags:** #Shorts #역사 #미스터리 #불가사의 포함해서 15개.

    [JSON 출력]
    {{
        "title": "호기심을 자극하는 다큐 제목",
        "script": "약 700자 분량의 긴 대본...",
        "hashtags": "#Shorts #History #Mystery ...",
        "image_prompts": {{
            "image_1": "Intro scene setting the atmosphere, {selected_style}",
            "image_2": "Main event or character description, {selected_style}",
            "image_3": "Crucial evidence or mysterious object, {selected_style}",
            "image_4": "Lingering ending shot leaving questions, {selected_style}"
        }},
        "keywords": "history, documentary, mystery"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a history documentary writer. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.85 # 너무 튀지 않게 약간 낮춤
        )
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"❌ 기획 단계 실패: {e}")
        return None