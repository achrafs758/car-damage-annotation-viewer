import json
import uuid
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .inference import predictions_for_item
from .model_registry import MODEL_REGISTRY, detect_device


def health(_request):
    return JsonResponse({"status": "ok"})


def annotation_dataset(_request):
    fixture_path = Path(settings.MEDIA_ROOT) / "samples" / "annotations.json"
    if not fixture_path.exists():
        return JsonResponse(
            {
                "source": "moondream/car_part_damage",
                "items": [],
                "error": "Sample fixture has not been downloaded yet.",
            },
            status=503,
        )

    with fixture_path.open("r", encoding="utf-8-sig") as fixture:
        return JsonResponse(json.load(fixture))


def models(_request):
    return JsonResponse({"tasks": MODEL_REGISTRY, "runtime": detect_device()})


def predictions(request):
    task = request.GET.get("task", "car_parts")
    model_id = request.GET.get("model")
    image_id = int(request.GET.get("image_id", "1"))

    if task not in MODEL_REGISTRY:
        return JsonResponse({"error": "Tache inconnue."}, status=400)

    dataset = _load_dataset()
    item = next((sample for sample in dataset["items"] if sample["id"] == image_id), dataset["items"][0])
    return JsonResponse({"task": task, "image": item, "outputs": predictions_for_item(item, task, model_id)})


@csrf_exempt
def upload_prediction(request):
    if request.method != "POST":
        return JsonResponse({"error": "Methode non supportee."}, status=405)

    task = request.POST.get("task", "car_parts")
    model_id = request.POST.get("model")
    image = request.FILES.get("image")
    if not image:
        return JsonResponse({"error": "Aucune image fournie."}, status=400)
    if task not in MODEL_REGISTRY:
        return JsonResponse({"error": "Tache inconnue."}, status=400)

    upload_root = Path(settings.MEDIA_ROOT) / "uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    suffix = Path(image.name).suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = upload_root / filename
    with target.open("wb") as destination:
        for chunk in image.chunks():
            destination.write(chunk)

    seed = _load_dataset()["items"][0].copy()
    seed["id"] = 999
    seed["image_id"] = image.name
    seed["image_url"] = f"/media/uploads/{filename}"
    return JsonResponse(
        {
            "task": task,
            "image": seed,
            "outputs": predictions_for_item(seed, task, model_id),
            "note": "Mode demo : geometrie de prediction issue du jeu d'exemples, image utilisateur conservee.",
        }
    )


def _load_dataset():
    fixture_path = Path(settings.MEDIA_ROOT) / "samples" / "annotations.json"
    with fixture_path.open("r", encoding="utf-8-sig") as fixture:
        return json.load(fixture)
