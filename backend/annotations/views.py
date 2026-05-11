import json
import uuid
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

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
    threshold = _threshold(request.GET.get("threshold"))

    if task not in MODEL_REGISTRY:
        return JsonResponse({"error": "Tache inconnue."}, status=400)

    dataset = _load_dataset()
    item = next((sample for sample in dataset["items"] if sample["id"] == image_id), dataset["items"][0])
    return JsonResponse({"task": task, "image": item, "outputs": predictions_for_item(item, task, model_id, threshold)})


@csrf_exempt
def upload_prediction(request):
    if request.method != "POST":
        return JsonResponse({"error": "Methode non supportee."}, status=405)

    task = request.POST.get("task", "car_parts")
    model_id = request.POST.get("model")
    threshold = _threshold(request.POST.get("threshold"))
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

    seed = _uploaded_item(image.name, target, filename)
    return JsonResponse(
        {
            "task": task,
            "image": seed,
            "outputs": predictions_for_item(seed, task, model_id, threshold),
            "note": "Mode demo : predictions generees pour l'image importee.",
        }
    )


@csrf_exempt
def upload_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "Methode non supportee."}, status=405)

    image = request.FILES.get("image")
    if not image:
        return JsonResponse({"error": "Aucune image fournie."}, status=400)

    upload_root = Path(settings.MEDIA_ROOT) / "uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    suffix = Path(image.name).suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = upload_root / filename
    with target.open("wb") as destination:
        for chunk in image.chunks():
            destination.write(chunk)

    return JsonResponse({"image": _uploaded_item(image.name, target, filename)})


@csrf_exempt
def uploaded_predictions(request):
    if request.method != "POST":
        return JsonResponse({"error": "Methode non supportee."}, status=405)

    payload = json.loads(request.body.decode("utf-8"))
    task = payload.get("task", "car_parts")
    model_id = payload.get("model")
    threshold = _threshold(payload.get("threshold"))
    item = payload.get("image")
    if task not in MODEL_REGISTRY:
        return JsonResponse({"error": "Tache inconnue."}, status=400)
    if not item:
        return JsonResponse({"error": "Image manquante."}, status=400)

    item = {
        "id": item.get("id", 999),
        "image_id": item["image_id"],
        "image_url": item["image_url"],
        "width": int(item["width"]),
        "height": int(item["height"]),
        "annotations": [],
    }
    return JsonResponse({"task": task, "image": item, "outputs": predictions_for_item(item, task, model_id, threshold)})


def _load_dataset():
    fixture_path = Path(settings.MEDIA_ROOT) / "samples" / "annotations.json"
    with fixture_path.open("r", encoding="utf-8-sig") as fixture:
        return json.load(fixture)


def _threshold(raw_value):
    try:
        return max(0, min(1, float(raw_value or 0)))
    except ValueError:
        return 0


def _uploaded_item(original_name, image_path, filename):
    with Image.open(image_path) as image:
        width, height = image.size
    return {
        "id": uuid.uuid4().hex,
        "source": "upload",
        "image_id": original_name,
        "image_url": f"/media/uploads/{filename}",
        "width": width,
        "height": height,
        "annotations": [],
    }
