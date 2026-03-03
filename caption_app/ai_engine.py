import os
import uuid
import requests
import base64
from django.conf import settings
from deep_translator import GoogleTranslator
from huggingface_hub import InferenceClient

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

# =====================================================
# IMAGE CAPTIONING
# =====================================================

def generate_caption(image_path):
    try:
        if not HF_API_TOKEN:
            print("HF_API_TOKEN missing")
            return "Caption service not configured"

        # Use huggingface_hub InferenceClient which handles endpoint routing automatically
        client = InferenceClient(
            model="Salesforce/blip-image-captioning-base",
            token=HF_API_TOKEN
        )

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        # Use image_to_text method for image captioning
        result = client.image_to_text(image_bytes)

        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif isinstance(result[0], str):
                return result[0]
        
        if isinstance(result, str):
            return result

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
        model_name = f"facebook/mms-tts-{mms_lang}"

        # Use huggingface_hub InferenceClient which handles endpoint routing automatically
        client = InferenceClient(
            model=model_name,
            token=HF_API_TOKEN
        )

        # Use text_to_speech method for TTS
        audio_bytes = client.text_to_speech(text)

        if not audio_bytes:
            print("TTS: No audio generated")
            return None

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
