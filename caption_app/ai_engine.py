import requests
import os
import uuid
from django.conf import settings
from deep_translator import GoogleTranslator
from gtts import gTTS
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

# ──────────────────────────────────────────────────────────
# Local BLIP model for image captioning
# Model loaded lazily to avoid import issues
# ──────────────────────────────────────────────────────────

_processor = None
_model = None

def _load_model():
    global _processor, _model
    if _processor is None:
        _processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        _model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")


def generate_caption(image_path):
    """Generate an image caption using local BLIP model."""
    try:
        _load_model()
        print(f"Processing image: {image_path}")
        image = Image.open(image_path).convert('RGB')
        
        inputs = _processor(image, return_tensors="pt")
        out = _model.generate(**inputs)
        caption = _processor.decode(out[0], skip_special_tokens=True)
        
        print(f"Generated caption: {caption}")
        return caption

    except Exception as e:
        print(f"Error generating caption: {e}")
        return f"Error generating caption: {str(e)}"


def translate_text(text, language):
    """Translate text using deep-translator (Google backend)."""
    try:
        print(f"Translating '{text}' to {language}")
        result = GoogleTranslator(source='auto', target=language).translate(text)
        print(f"Translation result: {result}")
        return result
    except Exception as e:
        print(f"Error translating: {e}")
        return text  # Return original text if translation fails


def text_to_speech(text, language='en'):
    """Convert text to speech and save as MP3."""
    try:
        print(f"Generating speech for: '{text}' in {language}")
        filename = f"audio_{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang=language)
        
        # Use settings.MEDIA_ROOT for robust path handling
        media_audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        print(f"Ensuring directory exists: {media_audio_dir}")
        os.makedirs(media_audio_dir, exist_ok=True)
        
        filepath = os.path.join(media_audio_dir, filename)
        print(f"Saving audio to: {filepath}")
        tts.save(filepath)
        print(f"Audio saved successfully to: {filepath}")
        return f"audio/{filename}"
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None