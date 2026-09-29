from openai import OpenAI
import requests
import os
import io
from PIL import Image
from config import OPENAI_API_KEY, TEMP_DIR

client = OpenAI(api_key=OPENAI_API_KEY)

def crop_center_to_vertical(pil_img):
    img_width, img_height = pil_img.size
    target_width = int(img_height * 9 / 16)
    left = (img_width - target_width) // 2
    right = left + target_width
    cropped_img = pil_img.crop((left, 0, right, img_height))
    return cropped_img

def generate_dalle_images(plan_data):
    print("🎨 [비주얼] 이미지 생성 단계 진입...")
    
    # 1. 프롬프트 가져오기
    prompts_dict = plan_data.get("image_prompts", {})
    video_topic = plan_data.get("title", "Historical mystery")
    
    # [핵심 수정] 프롬프트가 없거나 부족할 경우, 비상용 프롬프트 자동 생성
    if not prompts_dict or len(prompts_dict) < 4:
        print(f"⚠️ [경고] 기획안에 이미지 프롬프트가 부족합니다. (현재 {len(prompts_dict)}개)")
        print("🚑 [비상] 제목을 기반으로 즉석에서 프롬프트를 생성합니다...")
        
        prompts_dict = {
            "image_1": f"Atmospheric establishing shot of the historical setting of {video_topic}, cinematic period drama, dark moody lighting",
            "image_2": f"Key historical figures or event of {video_topic}, period-accurate clothing, cinematic period drama",
            "image_3": f"Close-up of a mysterious historical artifact or document related to {video_topic}, dramatic lighting",
            "image_4": f"Lingering ending shot leaving questions about {video_topic}, foggy, suspenseful atmosphere"
        }

    # 기존 이미지 파일 정리
    for i in range(4):
        img_path = os.path.join(TEMP_DIR, f"image_{i}.png")
        if os.path.exists(img_path): os.remove(img_path)

    # 딕셔너리 키 정렬 (순서 보장)
    # 키가 image_1, image_2... 가 아닐 수도 있으므로 강제로 4번 돌림
    prompt_values = list(prompts_dict.values())
    
    # 만약 리스트가 4개보다 적으면 마지막 걸로 채움
    while len(prompt_values) < 4:
        prompt_values.append(prompt_values[-1])

    for i in range(4):
        gpt_prompt = prompt_values[i]
        print(f"   Generating [{i+1}/4] (DALL-E 3)...")
        
        try:
            # 프롬프트 보정 (주제 일치성 강화)
            full_prompt = f"""
            Subject: {video_topic}.
            Scene Description: {gpt_prompt}.
            Style: Follow the art style stated in the scene description exactly. Historically accurate, cinematic, mysterious and dark mood. Vertical composition with the main subject centered.
            Note: No text, letters, captions or watermarks in the image.
            """
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            img_url = response.data[0].url
            img_bytes = requests.get(img_url, timeout=60).content
            pil_img = Image.open(io.BytesIO(img_bytes))
            vertical_img = crop_center_to_vertical(pil_img)

            filename = os.path.join(TEMP_DIR, f"image_{i}.png")
            vertical_img.save(filename, format="PNG")
                
        except Exception as e:
            print(f"⚠️ 이미지 {i+1} 생성 실패: {e}")
            # 실패 시 검은 화면 대신 제목이라도 박힌 이미지 생성 (추후 고려)
            filename = os.path.join(TEMP_DIR, f"image_{i}.png")
            Image.new('RGB', (1080, 1920), 'black').save(filename)

    print("✅ 삽화 4장 준비 완료.")
    return True