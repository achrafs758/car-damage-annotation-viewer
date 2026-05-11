import json
import uuid
from copy import deepcopy
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

    seed = _scale_seed_item(_load_dataset()["items"][0], target)
    seed["id"] = 999
    seed["image_id"] = image.name
    seed["image_url"] = f"/media/uploads/{filename}"
    return JsonResponse(
        {
            "task": task,
            "image": seed,
            "outputs": predictions_for_item(seed, task, model_id, threshold),
            "note": "Mode demo : geometrie de prediction redimensionnee sur l'image importee.",
        }
    )


def _load_dataset():
    fixture_path = Path(settings.MEDIA_ROOT) / "samples" / "annotations.json"
    with fixture_path.open("r", encoding="utf-8-sig") as fixture:
        return json.load(fixture)


def _threshold(raw_value):
    try:
        return max(0, min(1, float(raw_value or 0)))
    except ValueError:
        return 0


def _scale_seed_item(seed_item, image_path):
    with Image.open(image_path) as image:
        width, height = image.size

    scaled = deepcopy(seed_item)
    x_scale = width / seed_item["width"]
    y_scale = height / seed_item["height"]
    scaled["width"] = width
    scaled["height"] = height
    for annotation in scaled["annotations"]:
        annotation["bbox"] = _scale_bbox(annotation["bbox"], x_scale, y_scale)
        annotation["segmentation"] = _scale_segmentation(annotation.get("segmentation", []), x_scale, y_scale)
    return scaled


def _scale_bbox(bbox, x_scale, y_scale):
    x1, y1, x2, y2 = bbox
    return [round(x1 * x_scale, 1), round(y1 * y_scale, 1), round(x2 * x_scale, 1), round(y2 * y_scale, 1)]


def _scale_segmentation(segmentation, x_scale, y_scale):
    scaled_polygons = []
    for polygon in segmentation:
        scaled = []
        for index, value in enumerate(polygon):
            scale = x_scale if index % 2 == 0 else y_scale
            scaled.append(round(value * scale, 1))
        scaled_polygons.append(scaled)
    return scaled_polygons
