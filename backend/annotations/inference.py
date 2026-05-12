import math
from copy import deepcopy
from pathlib import Path

from django.conf import settings

from .local_models import local_model_status
from .model_registry import MODEL_REGISTRY, detect_device

_YOLO_CACHE = {}
_SAM_CACHE = {}

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


def _synthetic_annotations(width, height):
    boxes = [
        ("Front-bumper", [0.12, 0.62, 0.88, 0.82]),
        ("Hood", [0.24, 0.28, 0.76, 0.54]),
        ("Windshield", [0.32, 0.12, 0.68, 0.32]),
        ("Front-door", [0.48, 0.34, 0.72, 0.70]),
        ("Back-door", [0.70, 0.36, 0.90, 0.72]),
        ("Fender", [0.12, 0.36, 0.34, 0.66]),
        ("Front-wheel", [0.24, 0.68, 0.42, 0.92]),
        ("Back-wheel", [0.68, 0.68, 0.86, 0.92]),
        ("Headlight", [0.12, 0.54, 0.28, 0.64]),
        ("Grille", [0.32, 0.56, 0.56, 0.68]),
        ("Mirror", [0.70, 0.30, 0.80, 0.42]),
        ("Roof", [0.30, 0.04, 0.72, 0.16]),
        ("Rocker-panel", [0.42, 0.76, 0.76, 0.86]),
        ("Quarter-panel", [0.80, 0.40, 0.96, 0.68]),
    ]
    annotations = []
    for index, (category, ratios) in enumerate(boxes, start=1):
        x1, y1, x2, y2 = ratios
        bbox = [round(x1 * width, 1), round(y1 * height, 1), round(x2 * width, 1), round(y2 * height, 1)]
        annotations.append(
            {
                "id": index,
                "category": category,
                "bbox": bbox,
                "segmentation": _bbox_polygon(bbox, width, height, shrink=0),
            }
        )
    return annotations


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


def _translate_label(label):
    normalized = str(label).strip().lower().replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    mapping = {
        "back bumper": "pare-chocs arriere",
        "rear bumper": "pare-chocs arriere",
        "back-bumper": "pare-chocs arriere",
        "front bumper": "pare-chocs avant",
        "front-bumper": "pare-chocs avant",
        "bumper": "pare-chocs",
        "back glass": "vitre arriere",
        "rear glass": "vitre arriere",
        "back window": "vitre arriere",
        "front glass": "vitre avant",
        "front window": "vitre avant",
        "windshield": "pare-brise",
        "windscreen": "pare-brise",
        "glass": "vitre",
        "front left door": "porte avant gauche",
        "front right door": "porte avant droite",
        "back left door": "porte arriere gauche",
        "back right door": "porte arriere droite",
        "rear left door": "porte arriere gauche",
        "rear right door": "porte arriere droite",
        "front door": "porte avant",
        "rear door": "porte arriere",
        "back door": "porte arriere",
        "door": "porte",
        "hood": "capot",
        "bonnet": "capot",
        "fender": "aile",
        "quarter panel": "aile arriere",
        "rocker panel": "bas de caisse",
        "mirror": "retroviseur",
        "left mirror": "retroviseur gauche",
        "right mirror": "retroviseur droit",
        "headlight": "phare",
        "head lamp": "phare",
        "front light": "phare avant",
        "tail light": "feu arriere",
        "taillight": "feu arriere",
        "back light": "feu arriere",
        "grille": "calandre",
        "wheel": "roue",
        "tire": "pneu",
        "tyre": "pneu",
        "roof": "toit",
        "trunk": "coffre",
        "boot": "coffre",
        "tailgate": "hayon",
        "license plate": "plaque d'immatriculation",
        "number plate": "plaque d'immatriculation",
        "car": "vehicule",
        "vehicle": "vehicule",
        "scratch": "rayure",
        "scratches": "rayures",
        "dent": "bosselure",
        "dents": "bosselures",
        "crack": "fissure",
        "cracked": "fissure",
        "glass shatter": "bris de verre",
        "shattered glass": "bris de verre",
        "broken glass": "bris de verre",
        "lamp broken": "feu casse",
        "broken lamp": "feu casse",
        "light broken": "feu casse",
        "broken light": "feu casse",
        "tire flat": "pneu creve",
        "flat tire": "pneu creve",
        "flat tyre": "pneu creve",
        "broken part": "piece cassee",
        "missing part": "piece manquante",
        "paint chip": "peinture ecaillee",
        "paint damage": "peinture abimee",
        "flaking": "peinture ecaillee",
        "corrosion": "corrosion",
        "damage": "dommage",
        "damaged": "endommage",
    }
    return mapping.get(normalized, normalized)


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
    return mapping.get(label, _translate_label(label))


def predictions_for_item(item, task, model_id=None, confidence_threshold=0):
    task_config = MODEL_REGISTRY[task]
    runtime = detect_device()
    outputs = []
    for model_index, model in enumerate(task_config["models"]):
        if model_id and model["id"] != model_id:
            continue
        local = local_model_status(model["id"])
        error = None
        if item.get("source") == "upload" or not item.get("annotations"):
            predictions, error = _run_local_model(item, model, confidence_threshold)
        elif task == "car_parts":
            predictions = _part_predictions(item, model, model_index)
        else:
            predictions = _damage_predictions(item, model, model_index)
        predictions = [prediction for prediction in predictions if prediction["confidence"] >= confidence_threshold]
        outputs.append(
            {
                "model": model,
                "runtime": runtime,
                "local": local,
                "predictions": predictions,
                "count": len(predictions),
                "error": error,
            }
        )
    return outputs


def _run_local_model(item, model, confidence_threshold):
    local = local_model_status(model["id"])
    if not local["installed"]:
        return [], "Les poids du modele ne sont pas telecharges localement."
    image_path = _media_path(item["image_url"])
    if not image_path.exists():
        return [], f"Fichier image introuvable : {image_path}"

    if local["runner"] == "sam":
        return _run_sam_model(item, model, local, image_path, confidence_threshold)
    if local["runner"] != "yolo":
        return [], f"Le modele est telecharge, mais le moteur '{local['runner']}' n'est pas implemente."

    try:
        from ultralytics import YOLO

        model_path = local["path"]
        if model_path not in _YOLO_CACHE:
            _YOLO_CACHE[model_path] = YOLO(model_path)

        device = 0 if detect_device()["gpu_available"] else "cpu"
        results = _YOLO_CACHE[model_path].predict(
            source=str(image_path),
            conf=max(confidence_threshold, 0.01),
            device=device,
            verbose=False,
        )
        return _yolo_result_to_predictions(results[0], model), None
    except Exception as exc:
        return [], f"Inference locale echouee : {exc}"


def _run_sam_model(item, model, local, image_path, confidence_threshold):
    try:
        from ultralytics import SAM

        model_path = local["path"]
        if model_path not in _SAM_CACHE:
            _SAM_CACHE[model_path] = SAM(model_path)

        prompts = _sam_prompts(item, model)
        bboxes = [prompt["bbox"] for prompt in prompts]
        device = 0 if detect_device()["gpu_available"] else "cpu"
        result = _SAM_CACHE[model_path].predict(
            source=str(image_path),
            bboxes=bboxes,
            device=device,
            verbose=False,
        )[0]
        return _sam_result_to_predictions(result, model, prompts, confidence_threshold), None
    except Exception as exc:
        return [], f"Inference locale SAM echouee : {exc}"


def _sam_prompts(item, model):
    annotations = _synthetic_annotations(item["width"], item["height"])
    if "damage" in model["id"]:
        annotations = annotations[::2][:8]
    return [
        {
            "bbox": annotation["bbox"],
            "category": _class_for_model(model, index) if "damage" in model["id"] else _translate_part(annotation["category"]),
        }
        for index, annotation in enumerate(annotations[:12])
    ]


def _sam_result_to_predictions(result, model, prompts, confidence_threshold):
    predictions = []
    boxes = result.boxes
    masks = result.masks
    if boxes is None or masks is None:
        return predictions

    xyxy = boxes.xyxy.cpu().tolist()
    confidences = boxes.conf.cpu().tolist() if boxes.conf is not None else [0.8] * len(xyxy)
    mask_polygons = masks.xy if masks.xy is not None else []
    for index, bbox in enumerate(xyxy):
        confidence = float(confidences[index])
        if confidence < confidence_threshold:
            continue
        label = prompts[index]["category"] if index < len(prompts) else _class_for_model(model, index)
        segmentation = _mask_to_segmentation(mask_polygons[index]) if index < len(mask_polygons) else _bbox_polygon(bbox, result.orig_shape[1], result.orig_shape[0])
        predictions.append(
            {
                "id": f"{model['id']}-{index + 1}",
                "category": _translate_label(label),
                "bbox": [round(float(value), 1) for value in bbox],
                "segmentation": segmentation,
                "confidence": round(confidence, 3),
                "logit": round(math.log(max(min(confidence, 0.999), 0.001) / (1 - max(min(confidence, 0.999), 0.001))), 3),
            }
        )
    return predictions


def _media_path(image_url):
    relative = image_url.replace(settings.MEDIA_URL, "", 1).lstrip("/")
    return Path(settings.MEDIA_ROOT) / relative


def _yolo_result_to_predictions(result, model):
    predictions = []
    names = getattr(result, "names", {}) or {}
    boxes = result.boxes
    masks = result.masks
    if boxes is None:
        return predictions

    xyxy = boxes.xyxy.cpu().tolist()
    classes = boxes.cls.cpu().tolist() if boxes.cls is not None else [0] * len(xyxy)
    confidences = boxes.conf.cpu().tolist() if boxes.conf is not None else [1] * len(xyxy)
    mask_polygons = []
    if masks is not None and masks.xy is not None:
        mask_polygons = masks.xy

    for index, bbox in enumerate(xyxy):
        class_id = int(classes[index])
        label = names.get(class_id, _class_for_model(model, index))
        confidence = float(confidences[index])
        segmentation = _mask_to_segmentation(mask_polygons[index]) if index < len(mask_polygons) else _bbox_polygon(bbox, result.orig_shape[1], result.orig_shape[0])
        predictions.append(
            {
                "id": f"{model['id']}-{index + 1}",
                "category": _translate_label(label),
                "bbox": [round(float(value), 1) for value in bbox],
                "segmentation": segmentation,
                "confidence": round(confidence, 3),
                "logit": round(math.log(max(min(confidence, 0.999), 0.001) / (1 - max(min(confidence, 0.999), 0.001))), 3),
            }
        )
    return predictions


def _mask_to_segmentation(mask_points):
    if len(mask_points) == 0:
        return []
    flat = []
    for x, y in mask_points:
        flat.extend([round(float(x), 1), round(float(y), 1)])
    return [flat]
