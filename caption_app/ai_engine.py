import os
import uuid
import requests
from django.conf import settings
from deep_translator import GoogleTranslator

# =====================================================
# CONFIG
# =====================================================

# Prefer HF_API_TOKEN; fall back to HF_TOKEN (used by huggingface_hub)
HF_API_TOKEN = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}"
}

# Classic serverless Inference API (binary image POST)
HF_INFERENCE_API_URL = "https://api-inference.huggingface.co/models"
# Router URL (different API shape) kept only if needed later
HF_BASE_URL = "https://router.huggingface.co/hf-inference/models"

REQUEST_TIMEOUT = 60
CAPTION_MODEL = "Salesforce/blip-image-captioning-base"


def _safe_log(msg):
    """Print without raising on Windows/console Unicode errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("utf-8", errors="replace").decode("ascii", errors="replace"))


# Lazy-loaded BLIP model and processor (avoids loading at import time)
_caption_processor = None
_caption_model = None


def _get_caption_model():
    global _caption_processor, _caption_model
    if _caption_model is None:
        from PIL import Image
        from transformers import BlipProcessor, BlipForConditionalGeneration
        _caption_processor = BlipProcessor.from_pretrained(CAPTION_MODEL)
        _caption_model = BlipForConditionalGeneration.from_pretrained(CAPTION_MODEL)
    return _caption_processor, _caption_model


# =====================================================
# IMAGE CAPTIONING
# =====================================================

def generate_caption(image_path):
    try:
        _safe_log("Step 1: Generating caption (local model)...")

        from PIL import Image
        processor, model = _get_caption_model()
        image = Image.open(image_path).convert("RGB")
        # Unconditional captioning: only image, no text prompt
        inputs = processor(image, return_tensors="pt")
        # Avoid .to(dtype=...) - use only device to prevent BatchEncoding bug
        out = model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True).strip()
        if caption:
            _safe_log("HF Caption Response: " + caption)
            return caption
        return "No caption generated"

    except Exception as e:
        import traceback
        _safe_log("Caption error (local): " + str(e))
        _safe_log(traceback.format_exc())
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
# TEXT TO SPEECH (gTTS – no API key, works for many languages)
# =====================================================

def text_to_speech(text, language="en"):
    try:
        _safe_log("Step 3: Generating audio...")

        if not text or "Error" in text:
            _safe_log("Skipping TTS due to invalid text")
            return None

        try:
            from gtts import gTTS
        except ImportError:
            _safe_log("TTS error: gTTS not installed (pip install gTTS)")
            return None

        # gTTS uses ISO 639-1 codes (en, hi, te, fr, es, etc.)
        lang_clean = (language or "en")[:2].lower()
        if lang_clean not in ("en", "hi", "te", "fr", "es", "ko", "zh", "ar", "de", "it", "ja", "pt", "ru"):
            lang_clean = "en"

        audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        filename = f"audio_{uuid.uuid4()}.mp3"
        filepath = os.path.join(audio_dir, filename)

        tts = gTTS(text=text, lang=lang_clean, slow=False)
        tts.save(filepath)

        _safe_log("Audio saved: " + filename)
        return f"audio/{filename}"

    except Exception as e:
        import traceback
        _safe_log("TTS error: " + str(e))
        _safe_log(traceback.format_exc())
        return None
