from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, ImageClip, CompositeVideoClip, vfx
from moviepy.audio.fx.all import audio_loop
from openai import OpenAI
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import os
import glob
import random
import textwrap 
from config import OPENAI_API_KEY, FONT_PATH, TEMP_DIR, RESULT_DIR, NARRATION_FILE, FINAL_VIDEO_FILE, TEMP_AUDIO_FILE, BGM_DIR

client = OpenAI(api_key=OPENAI_API_KEY)

def random_motion_effect(clip):
    """
    줌인/줌아웃/좌우이동 중 랜덤 적용 (도파민 무빙)
    """
    duration = clip.duration
    w, h = clip.size
    
    mode = random.choice(['zoom_in', 'zoom_out', 'pan_left', 'pan_right'])
    
    def effect(get_frame, t):
        img = Image.fromarray(get_frame(t))
        base_size = img.size
        progress = t / duration
        
        if mode == 'zoom_in':
            scale = 1 + (0.2 * progress)
        elif mode == 'zoom_out':
            scale = 1.2 - (0.2 * progress)
        else:
            scale = 1.15 

        new_size = [int(dim * scale) for dim in base_size]
        img = img.resize(new_size, Image.LANCZOS)
        
        curr_w, curr_h = img.size
        center_x, center_y = curr_w // 2, curr_h // 2
        crop_w, crop_h = w, h
        
        if mode == 'pan_left':
            offset_x = int((curr_w - crop_w) * progress)
            left = offset_x
        elif mode == 'pan_right':
            offset_x = int((curr_w - crop_w) * (1 - progress))
            left = offset_x
        else:
            left = center_x - (crop_w // 2)

        top = center_y - (crop_h // 2)
        left = max(0, min(left, curr_w - crop_w))
        top = max(0, min(top, curr_h - crop_h))
        
        img = img.crop((left, top, left + crop_w, top + crop_h))
        return np.array(img)

    return clip.fl(effect)

def create_text_clip_pil(text, duration, font_path=FONT_PATH, fontsize=75, color='white', stroke_width=6):
    W, H = 1080, 500 
    wrapped_lines = textwrap.wrap(text, width=12) 
    
    try: font = ImageFont.truetype(font_path, fontsize)
    except: font = ImageFont.load_default()

    pil_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(pil_img)
    line_height = fontsize * 1.3
    total_text_height = len(wrapped_lines) * line_height
    current_y = (H - total_text_height) // 2

    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        for off_x in range(-stroke_width, stroke_width+1):
            for off_y in range(-stroke_width, stroke_width+1):
                draw.text((x+off_x, current_y+off_y), line, font=font, fill='black')
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height

    return ImageClip(np.array(pil_img)).set_duration(duration)

def create_final_video_documentary(narration_path=NARRATION_FILE, output_path=FINAL_VIDEO_FILE, bgm_folder=BGM_DIR):
    print(f"🎬 [편집] 도파민 모드 (1.3배속 + 동적 무빙)...")

    if not os.path.exists(narration_path): return False
    
    image_files = [os.path.join(TEMP_DIR, f"image_{i}.png") for i in range(4)]
    valid_images = [f for f in image_files if os.path.exists(f)]
    if not valid_images: return False

    narration_clip = None
    final_video = None
    
    try:
        # 1. 오디오 배속 (1.3배)
        original_audio = AudioFileClip(narration_path)
        fast_audio = original_audio.fx(vfx.speedx, 1.3)
        
        fast_audio_path = os.path.join(TEMP_DIR, "fast_narration.mp3")
        fast_audio.write_audiofile(fast_audio_path, logger=None)
        
        total_duration = fast_audio.duration + 0.5
        clip_duration = total_duration / 4

        # 2. 영상 클립 생성 (무빙 효과)
        processed_clips = []
        for i in range(4):
            img_path = os.path.join(TEMP_DIR, f"image_{i}.png")
            if not os.path.exists(img_path): img_path = valid_images[0] 

            pil_img = Image.open(img_path)
            w, h = pil_img.size
            target_w = int(h * 9 / 16)
            left = (w - target_w) // 2
            pil_img = pil_img.crop((left, 0, left + target_w, h)).resize((1080, 1920), Image.LANCZOS)
            
            img_clip = ImageClip(np.array(pil_img)).set_duration(clip_duration)
            processed_clips.append(random_motion_effect(img_clip))

        base_video = concatenate_videoclips(processed_clips, method="compose").subclip(0, total_duration)
        
        # 3. 자막 생성 (Whisper)
        print("📝 [자막] 배속된 오디오 분석 중...")
        with open(fast_audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=f, 
                response_format="verbose_json"
            )
        
        # [수정된 부분] 객체 접근법(dot notation)으로 에러 방지
        segments = transcript.segments
        
        subtitle_clips = []
        for s in segments:
            # 안전한 데이터 추출 (객체든 딕셔너리든 처리)
            if isinstance(s, dict):
                start, end, text = s['start'], s['end'], s['text']
            else:
                start, end, text = s.start, s.end, s.text
                
            text = text.strip()
            # 자막 스타일: 노랑, 크게
            txt_clip = create_text_clip_pil(text, end-start, color='yellow', fontsize=80).set_position(('center', 1400)).set_start(start)
            subtitle_clips.append(txt_clip)

        final_video_track = CompositeVideoClip([base_video] + subtitle_clips) if subtitle_clips else base_video

        # 4. BGM 합성
        bgm_files = glob.glob(os.path.join(bgm_folder, "*.mp3"))
        if bgm_files:
            # 랜덤 BGM 선택 및 볼륨 조절
            bgm_path = random.choice(bgm_files)
            print(f"🎵 [BGM] {os.path.basename(bgm_path)} 적용")
            bgm = AudioFileClip(bgm_path).volumex(0.15)
            final_audio_track = CompositeAudioClip([fast_audio, audio_loop(bgm, duration=total_duration)])
        else:
            final_audio_track = fast_audio

        final_video = final_video_track.set_audio(final_audio_track)
        
        final_video.write_videofile(
            output_path, fps=24, codec="libx264", audio_codec="aac", threads=4, 
            preset='medium', temp_audiofile=TEMP_AUDIO_FILE, remove_temp=True, logger="bar"
        )
        return True

    except Exception as e:
        print(f"❌ 편집 에러: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if narration_clip: narration_clip.close()
        if final_video: final_video.close()