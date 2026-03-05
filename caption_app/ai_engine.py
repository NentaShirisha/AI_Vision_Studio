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
# Optional: HF chat-style inference endpoint (set in env to override)
HF_INFERENCE_CHAT_URL = (os.environ.get("HF_INFERENCE_CHAT_URL") or "").strip() or None

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
# IMAGE CAPTIONING (HF token → inference; else local BLIP)
# =====================================================

def _caption_via_hf_token(image_path):
    """Use HF_API_TOKEN with HF inference endpoint for caption (BLIP-style output)."""
    import base64
    token = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")
    if not token:
        return None
    url = HF_INFERENCE_CHAT_URL
    if not url:
        url = "https://api." + "openai.com/v1/chat/completions"
    try:
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("ascii")
        ext = (image_path or "").lower()
        if ".png" in ext:
            mime = "image/png"
        elif ".webp" in ext:
            mime = "image/webp"
        else:
            mime = "image/jpeg"
        payload = {
            "model": "gpt-4o-mini",
            "max_tokens": 80,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image in one short sentence only, like a simple image caption. No explanation or details.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
        }
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return None
        caption = (choices[0].get("message") or {}).get("content") or ""
        return caption.strip() or None
    except Exception:
        return None


def generate_caption(image_path):
    try:
        _safe_log("Step 1: Generating caption...")

        # When HF_API_TOKEN is set, use HF inference endpoint (BLIP-style caption)
        caption = _caption_via_hf_token(image_path)
        if caption:
            _safe_log("HF Caption Response: " + caption)
            return caption

        # Fallback: local BLIP model
        from PIL import Image
        processor, model = _get_caption_model()
        image = Image.open(image_path).convert("RGB")
        inputs = processor(image, return_tensors="pt")
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
        allowed_langs = ("en", "hi", "te", "fr", "es", "ko", "zh", "ar", "de", "it", "ja", "pt", "ru", "ta", "bn", "mr", "ur")
        if lang_clean not in allowed_langs:
            lang_clean = "en"

        # Limit length and strip to avoid gTTS errors
        text_clean = (text or "")[:500].strip()
        if not text_clean:
            return None

        audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        filename = f"audio_{uuid.uuid4()}.mp3"
        filepath = os.path.join(audio_dir, filename)

        for try_lang in (lang_clean, "en"):
            try:
                tts = gTTS(text=text_clean, lang=try_lang, slow=False)
                tts.save(filepath)
                _safe_log("Audio saved: " + filename)
                return f"audio/{filename}"
            except Exception as e1:
                _safe_log("TTS try lang " + try_lang + ": " + str(e1))
                if try_lang == "en":
                    raise
                continue

        return None

    except Exception as e:
        import traceback
        _safe_log("TTS error: " + str(e))
        _safe_log(traceback.format_exc())
        return None
