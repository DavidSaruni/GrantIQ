import os
from django.utils.text import slugify

ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def unique_slug_for_grant(title, instance=None):
    base = slugify(title)[:80] or "grant"
    slug = base
    from grants.models import Grant

    n = 2
    while True:
        qs = Grant.objects.filter(slug=slug)
        if instance is not None and instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if not qs.exists():
            return slug
        slug = f"{base}-{n}"
        n += 1


def file_extension(filename):
    return os.path.splitext(filename or "")[1].lower()


def is_allowed_attachment(filename):
    return file_extension(filename) in ALLOWED_ATTACHMENT_EXTENSIONS


def is_allowed_image(filename):
    return file_extension(filename) in ALLOWED_IMAGE_EXTENSIONS


def inline_file_response(file_field, filename, content_type=None):
    from django.http import HttpResponse

    safe_name = os.path.basename(filename or "document").replace('"', "")
    if not content_type and safe_name.lower().endswith(".pdf"):
        content_type = "application/pdf"
    with file_field.open("rb") as handle:
        data = handle.read()
    response = HttpResponse(data, content_type=content_type or "application/octet-stream")
    response["Content-Disposition"] = f'inline; filename="{safe_name}"'
    response["Content-Length"] = str(len(data))
    return response
