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
        
        # Try using InferenceClient first
        try:
            client = InferenceClient(token=HF_API_TOKEN)
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
            
            result = client.image_to_text(image=image_bytes, model=model_name)
            
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and "generated_text" in result[0]:
                    return result[0]["generated_text"]
                elif isinstance(result[0], str):
                    return result[0]
            
            if isinstance(result, str):
                return result
        except Exception as client_error:
            print(f"InferenceClient failed, trying direct API: {client_error}")
            # Fallback to direct API call
            API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
            
            response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=60)
            
            print(f"Direct API Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Direct API Error: {response.text}")
                return "Caption service temporarily unavailable"
            
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            
            return "No caption generated"

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

        # Try using InferenceClient first
        try:
            client = InferenceClient(token=HF_API_TOKEN)
            audio_bytes = client.text_to_speech(text=text, model=model_name)
            
            if not audio_bytes:
                raise ValueError("No audio generated from InferenceClient")
        except Exception as client_error:
            print(f"InferenceClient failed, trying direct API: {client_error}")
            # Fallback to direct API call
            API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            payload = {"inputs": text}
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            print(f"Direct API Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Direct API Error: {response.text}")
                return None
            
            audio_bytes = response.content

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
