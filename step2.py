import requests
from config import OPENAI_API_KEY, NARRATION_FILE

def create_voice_narration_direct(script_text, output_filename=NARRATION_FILE):
    print(f"🎙️ AI 성우 녹음 중... -> {output_filename}")
    
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "tts-1",
        "input": script_text,
        "voice": "onyx"
    }

    try:
        with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
            if response.status_code == 200:
                with open(output_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
                print(f"✅ 오디오 저장 완료")
                return True
            else:
                print(f"❌ 요청 실패: {response.status_code} {response.text[:200]}")
                return False
    except Exception as e:
        print(f"❌ 연결 에러: {e}")
        return False