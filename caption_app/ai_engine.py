import os
import uuid
import time
import requests
from django.conf import settings
from deep_translator import GoogleTranslator
from gtts import gTTS

# =====================================================
# HuggingFace Free Inference API (Correct Endpoint)
# =====================================================

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"


import base64

def generate_caption(image_path):
    try:
        if not HF_API_TOKEN:
            print("HF_API_TOKEN missing")
            return "Caption service not configured"

        API_URL = "https://router.huggingface.co/hf-inference/models/Salesforce/blip-image-captioning-base"

        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json"
        }

        # Convert image to base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        payload = {
            "inputs": encoded_string
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("HF Status Code:", response.status_code)
        print("HF Raw Response:", response.text)

        if response.status_code != 200:
            return "Caption service temporarily unavailable"

        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]

        return "No caption generated"

    except Exception as e:
        print("Caption error:", e)
        return "Error generating caption"


# =====================================================
# Translation
# =====================================================

def translate_text(text, language):
    try:
        translated = GoogleTranslator(source='auto', target=language).translate(text)
        print("Translated Text:", translated)
        return translated
    except Exception as e:
        print("Translation error:", e)
        return text


# =====================================================
# Text to Speech (Rate-limit Safe)
# =====================================================

def text_to_speech(text, language='en'):
    try:
        if not HF_API_TOKEN:
            print("HF_API_TOKEN missing for TTS")
            return None

        # Map frontend language codes to MMS codes
        lang_map = {
            "en": "eng",
            "hi": "hin",
            "te": "tel",
            "zh": "zho",
            "fr": "fra",
            "de": "deu",
            "es": "spa",
            "ja": "jpn",
            "ko": "kor"
        }

        mms_lang = lang_map.get(language, "eng")

        TTS_API_URL = f"https://router.huggingface.co/hf-inference/models/facebook/mms-tts-{mms_lang}"

        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": text
        }

        response = requests.post(
            TTS_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        print("TTS Status Code:", response.status_code)

        if response.status_code != 200:
            print("TTS Error:", response.text)
            return None

        audio_bytes = response.content

        filename = f"audio_{uuid.uuid4()}.wav"
        media_audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(media_audio_dir, exist_ok=True)

        filepath = os.path.join(media_audio_dir, filename)

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        print("TTS audio saved:", filepath)

        return f"audio/{filename}"

    except Exception as e:
        print("TTS error:", e)
        return None


