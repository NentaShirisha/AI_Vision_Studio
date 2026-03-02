from caption_app.ai_engine import generate_caption
from PIL import Image
import os

# Create a dummy image for testing
img = Image.new('RGB', (100, 100), color = 'red')
img.save('test_image.jpg')

caption = generate_caption('test_image.jpg')
print(f"Caption: {caption}")

os.remove('test_image.jpg')