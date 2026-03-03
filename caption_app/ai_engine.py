import os
import uuid
import requests
from django.conf import settings
from deep_translator import GoogleTranslator

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

HF_BASE_URL = "https://router.huggingface.co/hf-inference/models"
REQUEST_TIMEOUT = 60


# =====================================================
# IMAGE CAPTIONING
# =====================================================

def generate_caption(image_path):
    try:
        print("Step 1: Generating caption...")

        if not HF_API_TOKEN:
            return "Caption service not configured"

        model_name = "Salesforce/blip-image-captioning-base"
        api_url = f"{HF_BASE_URL}/{model_name}"

        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/octet-stream",
        }

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        response = requests.post(
            api_url,
            headers=headers,
            data=image_bytes,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            print("HF Caption API Error:", response.text)
            return "Error generating caption"

        result = response.json()
        print("HF Caption Response:", result)

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "No caption generated")

        return "No caption generated"

    except Exception as e:
        print("Caption error:", str(e))
        return "Error generating caption"


# =====================================================
# TRANSLATION
# =====================================================

def translate_text(text, language):
    try:
        print(f"Step 2: Translating to {language}...")

        if not text or "Error" in text:
            return text

        return GoogleTranslator(source='auto', target=language).translate(text)

    except Exception as e:
        print("Translation error:", str(e))
        return text


# =====================================================
# TEXT TO SPEECH
# =====================================================

def text_to_speech(text, language='en'):
    try:
        print("Step 3: Generating audio...")

        if not HF_API_TOKEN:
            return None

        if not text or "Error" in text:
            print("Skipping TTS due to invalid text")
            return None

        lang_map = {
            "en": "eng",
            "hi": "hin",
            "te": "tel",
            "zh": "zho",
        }

        mms_lang = lang_map.get(language, "eng")
        model_name = f"facebook/mms-tts-{mms_lang}"
        api_url = f"{HF_BASE_URL}/{model_name}"

        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {"inputs": text}

        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            print("HF TTS API Error:", response.text)
            return None

        audio_bytes = response.content

        if not audio_bytes:
            return None

        filename = f"audio_{uuid.uuid4()}.wav"
        media_audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(media_audio_dir, exist_ok=True)

        filepath = os.path.join(media_audio_dir, filename)

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        return f"audio/{filename}"

    except Exception as e:
        print("TTS error:", str(e))
        return None
