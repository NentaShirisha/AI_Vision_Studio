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

        model_name = "Salesforce/blip-image-captioning-base"
        
        # Use InferenceClient - don't specify model in init, pass it to the method
        client = InferenceClient(token=HF_API_TOKEN)
        
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        
        # Use image_to_text method with model parameter
        result = client.image_to_text(image=image_bytes, model=model_name)
        
        print(f"Caption result type: {type(result)}, value: {result}")
        
        # Handle different response formats
        if isinstance(result, list) and len(result) > 0:
            item = result[0]
            if isinstance(item, dict) and "generated_text" in item:
                return item["generated_text"]
            elif isinstance(item, str):
                return item
        
        if isinstance(result, dict):
            if "generated_text" in result:
                return result["generated_text"]
            # Some models return the text directly in a dict
            for key in ["text", "caption", "label"]:
                if key in result:
                    return result[key]
        
        if isinstance(result, str):
            return result

        return "No caption generated"

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Caption error: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
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

        # Use InferenceClient - don't specify model in init, pass it to the method
        client = InferenceClient(token=HF_API_TOKEN)
        
        # Use text_to_speech method with model parameter
        audio_bytes = client.text_to_speech(text=text, model=model_name)
        
        print(f"TTS result type: {type(audio_bytes)}, length: {len(audio_bytes) if audio_bytes else 0}")

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
        import traceback
        error_msg = str(e)
        print(f"TTS error: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        return None
