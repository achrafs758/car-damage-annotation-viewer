import math
from copy import deepcopy

from .model_registry import MODEL_REGISTRY, detect_device

DAMAGE_SEQUENCE = [
    "rayure",
    "bosselure",
    "fissure",
    "bris de verre",
    "feu casse",
    "piece cassee",
    "peinture ecaillee",
    "piece manquante",
]


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _bbox_polygon(bbox, width, height, shrink=0.08, wobble=0):
    x1, y1, x2, y2 = bbox
    bw = x2 - x1
    bh = y2 - y1
    x1 = _clamp(x1 + bw * shrink + wobble, 0, width)
    y1 = _clamp(y1 + bh * shrink, 0, height)
    x2 = _clamp(x2 - bw * shrink, 0, width)
    y2 = _clamp(y2 - bh * shrink + wobble, 0, height)
    return [[round(x1, 1), round(y1, 1), round(x2, 1), round(y1, 1), round(x2, 1), round(y2, 1), round(x1, 1), round(y2, 1)]]


def _bbox_from_polygon(segmentation):
    points = segmentation[0]
    xs = points[0::2]
    ys = points[1::2]
    return [min(xs), min(ys), max(xs), max(ys)]


def _part_predictions(item, model, model_index):
    predictions = []
    for index, annotation in enumerate(item["annotations"][:14]):
        label = _translate_part(annotation["category"])
        polygon = deepcopy(annotation.get("segmentation")) or _bbox_polygon(annotation["bbox"], item["width"], item["height"])
        bbox = annotation.get("bbox") or _bbox_from_polygon(polygon)
        confidence = round(0.93 - index * 0.025 - model_index * 0.018, 3)
        predictions.append(
            {
                "id": f"{model['id']}-{index + 1}",
                "category": label,
                "bbox": bbox,
                "segmentation": polygon,
                "confidence": max(confidence, 0.41),
                "logit": round(math.log(max(confidence, 0.41) / (1 - max(confidence, 0.41))), 3),
            }
        )
    return predictions


def _damage_predictions(item, model, model_index):
    source = item["annotations"]
    stride = max(1, len(source) // 5)
    predictions = []
    for local_index, annotation in enumerate(source[model_index::stride][:6]):
        bbox = annotation["bbox"]
        shrink = 0.22 + model_index * 0.025
        wobble = (model_index - 1.5) * 3
        polygon = _bbox_polygon(bbox, item["width"], item["height"], shrink=shrink, wobble=wobble)
        out_bbox = _bbox_from_polygon(polygon)
        label = _class_for_model(model, local_index)
        confidence = round(0.88 - local_index * 0.055 - model_index * 0.021, 3)
        confidence = max(confidence, 0.36)
        predictions.append(
            {
                "id": f"{model['id']}-{local_index + 1}",
                "category": label,
                "bbox": out_bbox,
                "segmentation": polygon,
                "confidence": confidence,
                "logit": round(math.log(confidence / (1 - confidence)), 3),
                "related_part": _translate_part(annotation["category"]),
            }
        )
    return predictions


def _class_for_model(model, index):
    classes = model["classes"]
    return classes[index % len(classes)]


def _translate_part(label):
    mapping = {
        "Back-window": "vitre arriere",
        "Front-window": "vitre avant",
        "Windshield": "pare-brise",
        "Back-wheel": "roue arriere",
        "Front-wheel": "roue avant",
        "Rocker-panel": "bas de caisse",
        "Front-door": "porte avant",
        "Back-door": "porte arriere",
        "Quarter-panel": "aile arriere",
        "Front-bumper": "pare-chocs avant",
        "Back-bumper": "pare-chocs arriere",
        "Fender": "aile",
        "Hood": "capot",
        "Headlight": "phare",
        "Grille": "calandre",
        "Roof": "toit",
        "Mirror": "retroviseur",
        "License-plate": "plaque",
    }
    return mapping.get(label, label.lower())


def predictions_for_item(item, task, model_id=None):
    task_config = MODEL_REGISTRY[task]
    runtime = detect_device()
    outputs = []
    for model_index, model in enumerate(task_config["models"]):
        if model_id and model["id"] != model_id:
            continue
        if task == "car_parts":
            predictions = _part_predictions(item, model, model_index)
        else:
            predictions = _damage_predictions(item, model, model_index)
        outputs.append(
            {
                "model": model,
                "runtime": runtime,
                "predictions": predictions,
                "count": len(predictions),
            }
        )
    return outputs
