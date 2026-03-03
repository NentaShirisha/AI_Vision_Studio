import os
import uuid
import torch
import requests
from PIL import Image
from django.conf import settings
from deep_translator import GoogleTranslator
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer

# =====================================================
# DEVICE CONFIG
# =====================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================================================
# LOAD IMAGE CAPTION MODEL (LOAD ONLY ONCE)
# =====================================================

print("Loading image captioning model...")

model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

model.to(device)

print("Model loaded successfully.")

# =====================================================
# IMAGE CAPTIONING (LOCAL)
# =====================================================

def generate_caption(image_path):
    try:
        print("Step 1: Generating caption locally...")

        image = Image.open(image_path).convert("RGB")

        pixel_values = feature_extractor(images=image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)

        output_ids = model.generate(
            pixel_values,
            max_length=20,
            num_beams=4
        )

        caption = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        print("Generated Caption:", caption)

        return caption

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
# OPTIONAL TTS (HF ROUTER - MAY REQUIRE TOKEN)
# =====================================================

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
HF_BASE_URL = "https://router.huggingface.co/hf-inference/models"
REQUEST_TIMEOUT = 60


def text_to_speech(text, language='en'):
    try:
        print("Step 3: Generating audio...")

        if not HF_API_TOKEN:
            print("No HF token, skipping TTS.")
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
            print("TTS API Error:", response.text)
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

        print("Audio saved:", filename)

        return f"audio/{filename}"

    except Exception as e:
        print("TTS error:", str(e))
        return None
