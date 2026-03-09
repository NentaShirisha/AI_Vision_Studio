import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import default_storage

from .models import CaptionHistory
from .ai_engine import generate_caption, translate_text, text_to_speech


# ======================================================
# HOME PAGE
# ======================================================

def index(request):
    return render(request, "index.html")


# ======================================================
# USER REGISTRATION
# ======================================================

def register(request):

    if request.method == "POST":

        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")

    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


# ======================================================
# DASHBOARD
# ======================================================

@login_required
def dashboard(request):
    return render(request, "dashboard.html")


# ======================================================
# IMAGE UPLOAD PAGE
# ======================================================

@login_required
def upload(request):
    return render(request, "upload.html")


# ======================================================
# HISTORY PAGE
# ======================================================

@login_required
def history(request):

    history = CaptionHistory.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(request, "history.html", {"history": history})


# ======================================================
# USER PROFILE
# ======================================================

@login_required
def profile(request):
    return render(request, "profile.html", {"user": request.user})


# ======================================================
# MAIN AI PROCESSING ENDPOINT
# ======================================================

@login_required
def generate_caption_view(request):

    print("generate_caption_view called")

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:

        image = request.FILES.get("image")
        language = request.POST.get("language", "en")

        print("Image:", image)
        print("Language:", language)

        if not image:
            return JsonResponse({"error": "No image uploaded"}, status=400)

        # ======================================================
        # SAVE IMAGE
        # ======================================================

        image_path = default_storage.save(f"uploads/{image.name}", image)

        full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)

        print("Saved image to:", full_image_path)

        # ======================================================
        # STEP 1 : CAPTION GENERATION
        # ======================================================

        print("Step 1: Generating caption...")

        caption = generate_caption(full_image_path)

        print("Generated Caption:", caption)

        # ======================================================
        # STEP 2 : TRANSLATION
        # ======================================================

        print("Step 2: Translating...")

        translated = translate_text(caption, language)

        print("Translated Text:", translated)

        # ======================================================
        # STEP 3 : TEXT TO SPEECH
        # ======================================================

        print("Step 3: Generating audio...")

        audio_path = text_to_speech(translated, language)

        print("Audio Path:", audio_path)

        # Construct audio URL safely
       audio_url = None

       if audio_path:

            full_audio_path = os.path.join(settings.MEDIA_ROOT, audio_path)

            print("Audio file exists:", os.path.exists(full_audio_path))

    # build absolute URL
            audio_url = request.build_absolute_uri(settings.MEDIA_URL + audio_path)
        # ======================================================
        # SAVE HISTORY
        # ======================================================

        if request.user.is_authenticated:

            history = CaptionHistory.objects.create(
                user=request.user,
                image=image_path,
                caption=caption,
                language=language,
                translated_text=translated,
                audio_file=audio_path if audio_path else ""
            )

            print("History saved:", history.id)

        # ======================================================
        # RETURN RESPONSE
        # ======================================================

        return JsonResponse({
            "caption": caption,
            "translation": translated,
            "image_url": settings.MEDIA_URL + image_path,
            "audio_url": audio_url
        })

    except Exception as e:

        import traceback

        print("Processing Error:", str(e))
        traceback.print_exc()

        return JsonResponse({
            "error": str(e)
        }, status=500)


# ======================================================
# DEBUG TEST ENDPOINT
# ======================================================

def debug_caption_test(request):

    try:

        from PIL import Image

        img = Image.new("RGB", (128, 128), color=(120, 180, 200))

        debug_dir = os.path.join(settings.MEDIA_ROOT, "debug")

        os.makedirs(debug_dir, exist_ok=True)

        path = os.path.join(debug_dir, "debug_test.jpg")

        img.save(path)

        caption = generate_caption(path)

        translated = translate_text(caption, "en")

        audio_path = text_to_speech(translated, "en")

        audio_url = None

        if audio_path:
            audio_url = settings.MEDIA_URL + audio_path

        return JsonResponse({
            "caption": caption,
            "translation": translated,
            "audio_url": audio_url,
            "image_url": settings.MEDIA_URL + "debug/debug_test.jpg"
        })

    except Exception as e:

        return JsonResponse({"error": str(e)}, status=500)



