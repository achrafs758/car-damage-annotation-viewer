import json
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse


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
