from openai import OpenAI
import requests
from PIL import Image, ImageDraw, ImageFont
import json
import os
import textwrap
from config import OPENAI_API_KEY, BOLD_FONT_PATH, DATA_FILE, THUMBNAIL_FILE, TEMP_BG_IMAGE

client = OpenAI(api_key=OPENAI_API_KEY)

def create_dalle_background(keywords):
    try:
        prompt = f"Dark, mysterious cinematic historical scene for a documentary thumbnail. Theme: {keywords}. Dramatic lighting, strong contrast, empty space in the center. No text, no letters."
        response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
        with open(TEMP_BG_IMAGE, 'wb') as f:
            f.write(requests.get(response.data[0].url, timeout=60).content)
        return True
    except:
        Image.new('RGB', (1024, 576), 'black').save(TEMP_BG_IMAGE)
        return True

def add_text_to_image(title):
    try:
        if not os.path.exists(TEMP_BG_IMAGE): return False
        img = Image.open(TEMP_BG_IMAGE)
        if img.size == (1024, 1024):
            w, h = img.size; new_h = int(w*9/16); top = (h-new_h)//2
            img = img.crop((0, top, w, top+new_h))
        
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype(BOLD_FONT_PATH, 80)
        except: font = ImageFont.load_default()

        wrapper = textwrap.TextWrapper(width=20)
        wrapped_text = wrapper.fill(text=title)
        bbox = draw.textbbox((0, 0), wrapped_text, font=font, align='center')
        x, y = (img.width - (bbox[2]-bbox[0])) // 2, (img.height - (bbox[3]-bbox[1])) // 2
        
        draw.text((x, y), wrapped_text, font=font, fill="yellow", stroke_width=5, stroke_fill="black", align='center')
        img.convert("RGB").save(THUMBNAIL_FILE, quality=95)
        if os.path.exists(TEMP_BG_IMAGE): os.remove(TEMP_BG_IMAGE)
        print(f"✅ 썸네일 완료")
        return True
    except: return False

def generate_thumbnail():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            title = data.get("title", "").replace('"', '').strip()
            keywords = title or data.get("keywords", "history mystery")
        create_dalle_background(keywords)
        add_text_to_image(title)
        return True
    except: return False