import os
import uuid
import requests
from django.conf import settings
from deep_translator import GoogleTranslator

# =====================================================
# CONFIGURATION
# =====================================================

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}"
} if HF_API_TOKEN else {}

# Correct HuggingFace Inference Endpoint
HF_BASE_URL = "https://api-inference.huggingface.co/models"

REQUEST_TIMEOUT = 60


# =====================================================
# IMAGE CAPTIONING
# =====================================================

def generate_caption(image_path):
    try:
        print("Step 1: Generating caption...")

        if not HF_API_TOKEN:
            print("HF_API_TOKEN missing")
            return "Caption service not configured"

        model_name = "Salesforce/blip-image-captioning-base"
        api_url = f"{HF_BASE_URL}/{model_name}"

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        response = requests.post(
            api_url,
            headers=HF_HEADERS,
            data=image_bytes,
            timeout=REQUEST_TIMEOUT
        )

        print("Status Code:", response.status_code)

        if response.status_code != 200:
            print("HF Caption API Error:", response.text)
            return "Error generating caption"

        result = response.json()
        print("HF Caption Response:", result)

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "No caption generated")

        return "No caption generated"

    except Exception as e:
        import traceback
        print("Caption error:", str(e))
        print(traceback.format_exc())
        return "Error generating caption"


# =====================================================
# TRANSLATION
# =====================================================

def translate_text(text, language):
    try:
        print(f"Step 2: Translating to {language}...")

        if not text or "Error" in text:
            return text

        translated = GoogleTranslator(
            source='auto',
            target=language
        ).translate(text)

        print("Translated Text:", translated)

        return translated

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
            print("HF_API_TOKEN missing for TTS")
            return None

        if not text or "Error" in text:
            print("Skipping TTS due to invalid text")
            return None

        # Language mapping for MMS TTS
        lang_map = {
            "en": "eng",
            "hi": "hin",
            "te": "tel",
            "zh": "zho",
        }

        mms_lang = lang_map.get(language, "eng")

        model_name = f"facebook/mms-tts-{mms_lang}"
        api_url = f"{HF_BASE_URL}/{model_name}"

        payload = {
            "inputs": text
        }

        response = requests.post(
            api_url,
            headers=HF_HEADERS,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        print("TTS Status Code:", response.status_code)

        if response.status_code != 200:
            print("HF TTS API Error:", response.text)
            return None

        audio_bytes = response.content

        if not audio_bytes:
            print("No audio generated")
            return None

        filename = f"audio_{uuid.uuid4()}.wav"

        media_audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")
        os.makedirs(media_audio_dir, exist_ok=True)

        filepath = os.path.join(media_audio_dir, filename)

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        print("Audio saved:", filename)

        return f"audio/{filename}"

    except Exception as e:
        import traceback
        print("TTS error:", str(e))
        print(traceback.format_exc())
        return None
