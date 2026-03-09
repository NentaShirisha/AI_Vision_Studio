import os
import uuid
import time
import requests
from django.conf import settings
from deep_translator import GoogleTranslator

# =====================================================

# CONFIG

# =====================================================

HF_API_TOKEN = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")

HF_HEADERS = {
"Authorization": f"Bearer {HF_API_TOKEN}"
}

HF_INFERENCE_API_URL = "https://api-inference.huggingface.co/models"
HF_BASE_URL = "https://router.huggingface.co/hf-inference/models"
HF_INFERENCE_CHAT_URL = (os.environ.get("HF_INFERENCE_CHAT_URL") or "").strip() or None

REQUEST_TIMEOUT = 60
CAPTION_MODEL = "Salesforce/blip-image-captioning-base"

# =====================================================

# SAFE LOGGER

# =====================================================

def _safe_log(msg):
"""Print safely even if terminal encoding fails"""
try:
print(msg)
except UnicodeEncodeError:
print(msg.encode("utf-8", errors="replace").decode("ascii", errors="replace"))

# =====================================================

# LAZY LOAD BLIP MODEL

# =====================================================

_caption_processor = None
_caption_model = None

def _get_caption_model():
global _caption_processor, _caption_model

```
if _caption_model is None:
    from transformers import BlipProcessor, BlipForConditionalGeneration

    _caption_processor = BlipProcessor.from_pretrained(CAPTION_MODEL)
    _caption_model = BlipForConditionalGeneration.from_pretrained(CAPTION_MODEL)

return _caption_processor, _caption_model
```

# =====================================================

# CAPTION VIA HF TOKEN (OPTIONAL)

# =====================================================

def _caption_via_hf_token(image_path):
import base64

```
token = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")

if not token:
    return None

url = HF_INFERENCE_CHAT_URL
if not url:
    url = "https://api.openai.com/v1/chat/completions"

try:

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    ext = image_path.lower()

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
                    {"type": "text", "text": "Describe this image in one short caption."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
                ]
            }
        ]
    }

    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=REQUEST_TIMEOUT
    )

    if r.status_code != 200:
        return None

    data = r.json()
    choices = data.get("choices") or []

    if not choices:
        return None

    caption = (choices[0].get("message") or {}).get("content") or ""

    return caption.strip()

except Exception:
    return None
```

# =====================================================

# IMAGE CAPTION GENERATION

# =====================================================

def generate_caption(image_path):

```
try:

    _safe_log("Step 1: Generating caption...")

    caption = _caption_via_hf_token(image_path)

    if caption:
        return caption

    from PIL import Image

    processor, model = _get_caption_model()

    image = Image.open(image_path).convert("RGB")

    inputs = processor(image, return_tensors="pt")

    out = model.generate(**inputs)

    caption = processor.decode(out[0], skip_special_tokens=True).strip()

    return caption or "No caption generated"

except Exception as e:

    import traceback

    _safe_log("Caption error: " + str(e))
    _safe_log(traceback.format_exc())

    return "Error generating caption"
```

# =====================================================

# TRANSLATION

# =====================================================

def translate_text(text, language):

```
try:

    print(f"Step 2: Translating to {language}")

    if not text or "Error" in text:
        return text

    translated = GoogleTranslator(
        source="auto",
        target=language
    ).translate(text)

    return translated

except Exception as e:

    print("Translation error:", str(e))

    return text
```

# =====================================================

# TEXT TO SPEECH

# =====================================================

def text_to_speech(text, language="en"):

```
try:

    _safe_log("Step 3: Generating audio")

    if not text or "Error" in text:
        return None

    from gtts import gTTS

    lang_clean = (language or "en")[:2].lower()

    allowed_langs = (
        "en","hi","te","fr","es","ko","zh","ar",
        "de","it","ja","pt","ru","ta","bn","mr","ur"
    )

    if lang_clean not in allowed_langs:
        lang_clean = "en"

    text_clean = text[:500].strip()

    if not text_clean:
        return None

    audio_dir = os.path.join(settings.MEDIA_ROOT, "audio")

    os.makedirs(audio_dir, exist_ok=True)

    filename = f"audio_{uuid.uuid4()}.mp3"

    filepath = os.path.join(audio_dir, filename)

    try:

        tts = gTTS(text=text_clean, lang=lang_clean, slow=False)

        tts.save(filepath)

        time.sleep(0.3)

        if os.path.exists(filepath):

            _safe_log("Audio saved: " + filepath)

            return f"audio/{filename}"

        else:

            _safe_log("Audio file missing")

            return None

    except Exception as e:

        _safe_log("TTS error: " + str(e))

        return None

except Exception as e:

    import traceback

    _safe_log("TTS crash: " + str(e))
    _safe_log(traceback.format_exc())

    return None
```
