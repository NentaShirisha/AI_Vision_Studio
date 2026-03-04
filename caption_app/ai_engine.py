import os
import uuid
import requests
from django.conf import settings
from deep_translator import GoogleTranslator

# =====================================================
# CONFIG
# =====================================================

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}"
}

HF_BASE_URL = "https://router.huggingface.co/hf-inference/models"

REQUEST_TIMEOUT = 60


# =====================================================
# IMAGE CAPTIONING
# =====================================================

def generate_caption(image_path):

    try:

        print("Step 1: Generating caption...")

        model = "Salesforce/blip-image-captioning-base"
        api_url = f"{HF_BASE_URL}/{model}"

        with open(image_path, "rb") as image_file:

            files = {
                "file": image_file
            }

            response = requests.post(
                api_url,
                headers=HF_HEADERS,
                files=files,
                timeout=REQUEST_TIMEOUT
            )

        print("Status Code:", response.status_code)

        if response.status_code != 200:
            print("HF Caption API Error:", response.text)
            return "Error generating caption"

        result = response.json()

        print("HF Caption Response:", result)

        if isinstance(result, list):
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
            source="auto",
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

def text_to_speech(text, language="en"):

    try:

        print("Step 3: Generating audio...")

        if not text or "Error" in text:
            print("Skipping TTS due to invalid text")
            return None

        lang_map = {
            "en": "eng",
            "hi": "hin",
            "te": "tel"
        }

        mms_lang = lang_map.get(language, "eng")

        model = f"facebook/mms-tts-{mms_lang}"

        api_url = f"{HF_BASE_URL}/{model}"

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

        filename = f"audio_{uuid.uuid4()}.wav"

        audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")

        os.makedirs(audio_dir, exist_ok=True)

        filepath = os.path.join(audio_dir, filename)

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        print("Audio saved:", filename)

        return f"audio/{filename}"

    except Exception as e:

        import traceback

        print("TTS error:", str(e))
        print(traceback.format_exc())

        return None
