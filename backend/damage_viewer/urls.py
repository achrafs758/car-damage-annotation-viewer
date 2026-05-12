from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from annotations.views import annotation_dataset, health, models, predictions, upload_image, upload_prediction, uploaded_predictions

urlpatterns = [
    path("api/health/", health, name="health"),
    path("api/annotations/", annotation_dataset, name="annotation-dataset"),
    path("api/models/", models, name="models"),
    path("api/predictions/", predictions, name="predictions"),
    path("api/uploads/", upload_image, name="upload-image"),
    path("api/uploaded-predictions/", uploaded_predictions, name="uploaded-predictions"),
    path("api/upload-predict/", upload_prediction, name="upload-prediction"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
