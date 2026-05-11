from pathlib import Path

MODELS_ROOT = Path(__file__).resolve().parent.parent / "models"

LOCAL_MODEL_FILES = {
    "parts-yolov11-majorburn": {
        "runner": "yolo",
        "repo": "Majorburn/yolov11-carparts-seg",
        "repo_type": "model",
        "filename": "best.pt",
        "local_path": MODELS_ROOT / "parts" / "majorburn_yolov11_carparts.pt",
    },
    "parts-yolo26-mitbersh": {
        "runner": "yolo",
        "repo": "mitbersh/car-parts-segmentation",
        "repo_type": "model",
        "filename": "parts_segmentation.pt",
        "local_path": MODELS_ROOT / "parts" / "mitbersh_yolo26_parts.pt",
    },
    "parts-yolo26-sliverwall": {
        "runner": "yolo",
        "repo": "Sliverwall/yolo26l_car_parts_seg",
        "repo_type": "model",
        "filename": "yolo26l_car_parts_seg.pt",
        "local_path": MODELS_ROOT / "parts" / "sliverwall_yolo26l_carparts_seg.pt",
    },
    "parts-yolo11-filoemad": {
        "runner": "yolo",
        "repo": "FiloEmad/car-parts-yolo11",
        "repo_type": "model",
        "filename": "best.pt",
        "local_path": MODELS_ROOT / "parts" / "filoemad_yolo11_carparts.pt",
    },
    "damage-yolov11-cardd": {
        "runner": "yolo",
        "repo": "harpreetsahota/car-dd-segmentation-yolov11",
        "repo_type": "model",
        "filename": "best.pt",
        "local_path": MODELS_ROOT / "damage" / "harpreetsahota_cardd_yolov11.pt",
    },
    "damage-yolo26-mitbersh": {
        "runner": "yolo",
        "repo": "mitbersh/car-damage-segmentation",
        "repo_type": "model",
        "filename": "damage_segmentation.pt",
        "local_path": MODELS_ROOT / "damage" / "mitbersh_yolo26_damage.pt",
    },
    "damage-cardd-yolov8s": {
        "runner": "yolo",
        "repo": "abdullahg7/cardd-yolov8s",
        "repo_type": "model",
        "filename": "v1.0/best.pt",
        "local_path": MODELS_ROOT / "damage" / "abdullah_cardd_yolov8s.pt",
    },
    "damage-yolov11-vineet": {
        "runner": "yolo",
        "repo": "vineetsarpal/yolov11n-car-damage",
        "repo_type": "model",
        "filename": "best.pt",
        "local_path": MODELS_ROOT / "damage" / "vineetsarpal_yolov11n_damage.pt",
    },
}


def local_model_status(model_id):
    config = LOCAL_MODEL_FILES.get(model_id)
    if not config:
        return {"installed": False, "runner": "unavailable", "path": None}

    path = config["local_path"]
    return {
        "installed": path.exists(),
        "runner": config["runner"],
        "path": str(path),
    }
