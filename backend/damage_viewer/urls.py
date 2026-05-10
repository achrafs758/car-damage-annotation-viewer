from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from annotations.views import annotation_dataset, health

urlpatterns = [
    path("api/health/", health, name="health"),
    path("api/annotations/", annotation_dataset, name="annotation-dataset"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
