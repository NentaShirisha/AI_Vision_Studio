import os
import uuid
import requests
from django.conf import settings
from deep_translator import GoogleTranslator
from gtts import gTTS

# ==========================================
# HuggingFace Hosted BLIP Inference API
# ==========================================

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}"
}


def generate_caption(image_path):
    """Generate image caption using HuggingFace cloud model."""
    try:
        if not HF_API_TOKEN:
            return "HF_API_TOKEN not configured"

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        response = requests.post(API_URL, headers=headers, data=image_bytes)

        if response.status_code != 200:
            print("HuggingFace API Error:", response.text)
            return "Caption service temporarily unavailable"

        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]

        return "No caption generated"

    except Exception as e:
        print("Caption error:", e)
        return "Error generating caption"


# ==========================================
# Translation
# ==========================================

def translate_text(text, language):
    try:
        return GoogleTranslator(source='auto', target=language).translate(text)
    except Exception as e:
        print("Translation error:", e)
        return text


# ==========================================
# Text to Speech
# ==========================================

def text_to_speech(text, language='en'):
    try:
        filename = f"audio_{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang=language)

        media_audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(media_audio_dir, exist_ok=True)

        filepath = os.path.join(media_audio_dir, filename)
        tts.save(filepath)

        return f"audio/{filename}"

    except Exception as e:
        print("TTS error:", e)
        return None
