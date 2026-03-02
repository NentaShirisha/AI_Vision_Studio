from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from .models import CaptionHistory
from .serializers import CaptionHistorySerializer
from .ai_engine import generate_caption, translate_text, text_to_speech
import os

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def upload(request):
    return render(request, 'upload.html')

@login_required
def history(request):
    history = CaptionHistory.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'history': history})

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@csrf_exempt
def generate_caption_view(request):
    print("generate_caption_view called")
    
    if request.method == 'POST':
        print("POST request")
        image = request.FILES.get('image')
        language = request.POST.get('language', 'en')
        print(f"Image: {image}, Language: {language}")
        
        if image:
            # Save image
            image_path = default_storage.save(f'uploads/{image.name}', image)
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            print(f"Saved image to: {full_path}")
            
            try:
                # Process synchronously for now (can be made async with Celery)
                print("Step 1: Generating caption...")
                caption = generate_caption(full_path)
                print(f"Generated Caption: {caption}")
                
                print(f"Step 2: Translating to {language}...")
                translated = translate_text(caption, language)
                print(f"Translated Text: {translated}")
                
                print("Step 3: Generating audio...")
                audio_path = text_to_speech(translated, language)
                print(f"Audio Path: {audio_path}")
                
                if not audio_path:
                    print("Warning: Audio generation failed.")
                
                # Save to DB only if user is authenticated
                if request.user.is_authenticated:
                    print(f"Saving history for user: {request.user.username}")
                    history = CaptionHistory.objects.create(
                        user=request.user,
                        image=image_path,
                        caption=caption,
                        language=language,
                        translated_text=translated,
                        audio_file=audio_path
                    )
                    print(f"History saved with ID: {history.id}")
                
                print("Request successful, returning JSON response.")
                return JsonResponse({
                    'caption': caption,
                    'translation': translated,
                    'audio_url': f'/media/{audio_path}' if audio_path else None,
                    'image_url': f'/media/{image_path}'
                })
            except Exception as e:
                import traceback
                print(f"Processing Error: {str(e)}")
                traceback.print_exc()
                return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'})

def debug_caption_test(request):
    """Debug endpoint: generate caption from a temporary image without auth/upload."""
    try:
        from PIL import Image
        img = Image.new('RGB', (128, 128), color=(120, 180, 200))
        debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        path = os.path.join(debug_dir, 'debug_test.jpg')
        img.save(path)

        caption = generate_caption(path)
        translated = translate_text(caption, 'en')
        audio_path = text_to_speech(translated, 'en') or ''

        return JsonResponse({
            'caption': caption,
            'translation': translated,
            'audio_url': f'/media/{audio_path}',
            'image_url': f'/media/debug/debug_test.jpg'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# class CaptionAPI(APIView):
#     permission_classes = [IsAuthenticated]
#     
#     def post(self, request):
#         image = request.FILES.get('image')
#         language = request.data.get('language', 'en')
#         
#         if image:
#             image_path = default_storage.save(f'uploads/{image.name}', image)
#             full_path = os.path.join(settings.MEDIA_ROOT, image_path)
#             
#             caption = generate_caption(full_path)
#             translated = translate_text(caption, language)
#             audio_path = text_to_speech(translated, language)
#             
#             history = CaptionHistory.objects.create(
#                 user=request.user,
#                 image=image_path,
#                 caption=caption,
#                 language=language,
#                 translated_text=translated,
#                 audio_file=audio_path
#             )
#             
#             serializer = CaptionHistorySerializer(history)
#             return Response(serializer.data)
#         
#         return Response({'error': 'No image provided'}, status=400)