import os
from PIL import Image

BASE_DIR = os.path.join("static", "uploads", "service_images")

# 🔥 ENSURE DIRECTORY EXISTS (THIS WAS MISSING)
os.makedirs(BASE_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def save_service_image(file, name):
    if not file or not file.filename:
        raise ValueError("No file received")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid image format")

    try:
        img = Image.open(file)
        img = img.convert("RGB")
    except Exception as e:
        raise ValueError("Invalid or corrupted image") from e

    # Resize large images
    if img.width > 1400:
        ratio = 1400 / img.width
        img = img.resize((1400, int(img.height * ratio)))

    full_path = f"uploads/service_images/{name}.jpg"
    thumb_path = f"uploads/service_images/{name}_thumb.jpg"

    img.save(os.path.join("static", full_path), "JPEG", quality=85)

    thumb = img.resize((400, int(img.height * (400 / img.width))))
    thumb.save(os.path.join("static", thumb_path), "JPEG", quality=70)

    return full_path, thumb_path
