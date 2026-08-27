import os
import uuid

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024

UPLOAD_DIR = os.path.join("static", "uploads")


def save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        return None, "지원하지 않는 이미지 형식입니다."

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size > MAX_IMAGE_SIZE:
        return None, "이미지 용량은 5MB 이하여야 합니다."

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    saved_name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_DIR, saved_name))

    return f"/static/uploads/{saved_name}", None


def delete_uploaded_image(image_path):
    if not image_path or not image_path.startswith("/static/uploads/"):
        return

    file_path = os.path.join(UPLOAD_DIR, os.path.basename(image_path))

    if os.path.isfile(file_path):
        os.remove(file_path)
