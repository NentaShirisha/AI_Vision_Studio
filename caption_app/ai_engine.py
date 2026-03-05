import os
import uuid
import time
import requests

from django.conf import settings
from deep_translator import GoogleTranslator


# ============================================
# HUGGINGFACE CONFIGURATION
# ============================================

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

HF_HEADERS = {}

# Only add token if available
if HF_API_TOKEN:
    HF_HEADERS["Authorization"] = f"Bearer {HF_API_TOKEN}"

REQUEST_TIMEOUT = 90


# ============================================
# IMAGE CAPTION GENERATION
# ============================================

def generate_caption(image_path):

    try:

        print("Step 1: Generating caption...")

        api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        response = requests.post(
            api_url,
            headers=HF_HEADERS,
            data=image_bytes,
            timeout=REQUEST_TIMEOUT
        )

        print("Status Code:", response.status_code)

        # If model is loading (very common on HF)
        if response.status_code == 503:

            print("Model loading... retrying in 10 seconds")

            time.sleep(10)

            response = requests.post(
                api_url,
                headers=HF_HEADERS,
                data=image_bytes,
                timeout=REQUEST_TIMEOUT
            )

        if response.status_code != 200:

            print("HF Caption API Error:", response.text)

            return "Unable to generate caption"

        result = response.json()

        print("HF Caption Response:", result)

        if isinstance(result, list) and len(result) > 0:

            caption = result[0].get("generated_text", "")

            if caption.strip():
                return caption

        return "No caption generated"

    except Exception as e:

        print("Caption Error:", str(e))

        return "Unable to generate caption"


# ============================================
# TRANSLATION
# ============================================

def translate_text(text, language):

    try:

        print(f"Step 2: Translating to {language}...")

        if not text or text.strip() == "" or "Unable" in text:
            return text

        translated = GoogleTranslator(
            source="auto",
            target=language
        ).translate(text)

        print("Translated Text:", translated)

        return translated

    except Exception as e:

        print("Translation Error:", str(e))

        return text


# ============================================
# TEXT TO SPEECH
# ============================================

def text_to_speech(text, language="en"):

    try:

        print("Step 3: Generating audio...")

        if not text or text.strip() == "" or "Unable" in text:

            print("Skipping TTS")

            return None

        lang_map = {
            "en": "eng",
            "hi": "hin",
            "te": "tel"
        }

        mms_lang = lang_map.get(language, "eng")

        model = f"facebook/mms-tts-{mms_lang}"

        api_url = f"https://api-inference.huggingface.co/models/{model}"

        payload = {
            "inputs": text
        }

        response = requests.post(
            api_url,
            headers=HF_HEADERS,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        print("TTS Status:", response.status_code)

        # Retry if model loading
        if response.status_code == 503:

            print("TTS model loading... retrying")

            time.sleep(10)

            response = requests.post(
                api_url,
                headers=HF_HEADERS,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

        if response.status_code != 200:

            print("HF TTS Error:", response.text)

            return None

        audio_bytes = response.content

        # Ensure media folders exist
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")

        os.makedirs(audio_dir, exist_ok=True)

        filename = f"audio_{uuid.uuid4()}.wav"

        filepath = os.path.join(audio_dir, filename)

        with open(filepath, "wb") as f:

            f.write(audio_bytes)

        print("Audio saved:", filename)

        return f"audio/{filename}"

    except Exception as e:

        print("TTS Error:", str(e))

        return None
