import os
import uuid
import requests
import base64
from django.conf import settings
from deep_translator import GoogleTranslator

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

# =====================================================
# IMAGE CAPTIONING
# =====================================================

def generate_caption(image_path):
    try:
        if not HF_API_TOKEN:
            print("HF_API_TOKEN missing")
            return "Caption service not configured"

        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}"
        }

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        response = requests.post(
            API_URL,
            headers=headers,
            data=image_bytes,
            timeout=60
        )

        print("HF Status Code:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            return "Caption service temporarily unavailable"

        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]

        return "No caption generated"

    except Exception as e:
        print("Caption error:", e)
        return "Error generating caption"


# =====================================================
# TRANSLATION
# =====================================================

def translate_text(text, language):
    try:
        translated = GoogleTranslator(source='auto', target=language).translate(text)
        return translated
    except Exception as e:
        print("Translation error:", e)
        return text


# =====================================================
# MULTILINGUAL TTS (Free Compatible Model)
# =====================================================

def text_to_speech(text, language='en'):
    try:
        if not HF_API_TOKEN:
            print("HF_API_TOKEN missing for TTS")
            return None

        lang_map = {
            "en": "eng",
            "hi": "hin",
            "te": "tel",
            "zh": "zho",
        }

        mms_lang = lang_map.get(language, "eng")

        API_URL = f"https://api-inference.huggingface.co/models/facebook/mms-tts-{mms_lang}"

        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}"
        }

        payload = {
            "inputs": text
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("TTS Status Code:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            return None

        audio_bytes = response.content

        filename = f"audio_{uuid.uuid4()}.wav"
        media_audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(media_audio_dir, exist_ok=True)

        filepath = os.path.join(media_audio_dir, filename)

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        return f"audio/{filename}"

    except Exception as e:
        print("TTS error:", e)
        return None
