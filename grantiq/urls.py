import os

from django.contrib import admin
from django.http import Http404
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve


def _safe_static_roots():
    roots = []
    for item in getattr(settings, "STATICFILES_DIRS", []):
        roots.append(item[1] if isinstance(item, (list, tuple)) else item)
    if getattr(settings, "STATIC_ROOT", None):
        roots.append(settings.STATIC_ROOT)
    return [os.path.normpath(root) for root in roots if root]


def serve_static(request, path):
    for root in _safe_static_roots():
        full = os.path.normpath(os.path.join(root, path))
        if full == root or full.startswith(root + os.sep):
            if os.path.isfile(full):
                return static_serve(request, path, document_root=root)
    raise Http404("Static file not found")


urlpatterns = [
    path("staff/", admin.site.urls),
    path("", include("pages.urls")),
    path("grants/", include("grants.urls")),
    path("accounts/", include("accounts.urls")),
    path("applications/", include("applications.urls")),
    path("contacts/", include("contacts.urls")),
    re_path(r"^static/(?P<path>.*)$", serve_static),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
