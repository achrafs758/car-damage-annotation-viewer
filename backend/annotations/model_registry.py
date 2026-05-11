from .local_models import local_model_status

CAR_PART_CLASSES = [
    "pare-chocs avant",
    "pare-chocs arriere",
    "capot",
    "aile",
    "porte avant",
    "porte arriere",
    "retroviseur",
    "phare",
    "calandre",
    "roue",
    "toit",
    "pare-brise",
    "vitre",
    "bas de caisse",
]

DAMAGE_CLASSES_CARDD = [
    "rayure",
    "bosselure",
    "fissure",
    "bris de verre",
    "feu casse",
    "pneu creve",
]

DAMAGE_CLASSES_EXTENDED = [
    "rayure",
    "bosselure",
    "fissure",
    "peinture ecaillee",
    "piece cassee",
    "piece manquante",
    "corrosion",
    "bris de verre",
]

MODEL_REGISTRY = {
    "car_parts": {
        "label": "Segmentation des pieces",
        "description": "Identifier les pieces visibles pour relier chaque dommage a une zone du vehicule.",
        "models": [
            {
                "id": "parts-yolov11-majorburn",
                "name": "YOLOv11 Carparts Seg",
                "provider": "Hugging Face",
                "architecture": "YOLOv11-seg",
                "source_url": "https://huggingface.co/Majorburn/yolov11-carparts-seg",
                "dataset": "Car parts segmentation, 23 classes",
                "license": "AGPL-3.0",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": CAR_PART_CLASSES,
            },
            {
                "id": "parts-yolo26-mitbersh",
                "name": "YOLO26 Car Parts Seg",
                "provider": "Hugging Face",
                "architecture": "YOLO26-seg",
                "source_url": "https://huggingface.co/mitbersh/car-parts-segmentation",
                "dataset": "mitbersh/car-parts-segmentation-yolo",
                "license": "a verifier",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": CAR_PART_CLASSES,
            },
            {
                "id": "parts-yolo26-sliverwall",
                "name": "YOLO26L Car Parts Seg",
                "provider": "Hugging Face",
                "architecture": "YOLO26L-seg",
                "source_url": "https://huggingface.co/Sliverwall/yolo26l_car_parts_seg",
                "dataset": "car parts segmentation",
                "license": "a verifier",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": CAR_PART_CLASSES,
            },
            {
                "id": "parts-yolo11-filoemad",
                "name": "YOLO11 Car Parts",
                "provider": "Hugging Face",
                "architecture": "YOLO11",
                "source_url": "https://huggingface.co/FiloEmad/car-parts-yolo11",
                "dataset": "car parts segmentation",
                "license": "a verifier",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": CAR_PART_CLASSES,
            },
        ],
    },
    "damage": {
        "label": "Segmentation des dommages",
        "description": "Localiser les dommages visibles avec un score exploitable par un expert.",
        "models": [
            {
                "id": "damage-yolov11-cardd",
                "name": "YOLOv11-seg CarDD",
                "provider": "Hugging Face",
                "architecture": "YOLOv11-seg",
                "source_url": "https://huggingface.co/harpreetsahota/car-dd-segmentation-yolov11",
                "dataset": "CarDD",
                "license": "a verifier avec CarDD",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": DAMAGE_CLASSES_CARDD,
            },
            {
                "id": "damage-yolo26-mitbersh",
                "name": "YOLO26 Damage Seg",
                "provider": "Hugging Face",
                "architecture": "YOLO26-seg",
                "source_url": "https://huggingface.co/mitbersh/car-damage-segmentation",
                "dataset": "mitbersh/car-damage-segmentation-yolo",
                "license": "a verifier",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": DAMAGE_CLASSES_EXTENDED,
            },
            {
                "id": "damage-cardd-yolov8s",
                "name": "YOLOv8s CarDD",
                "provider": "Hugging Face",
                "architecture": "YOLOv8s",
                "source_url": "https://huggingface.co/abdullahg7/cardd-yolov8s",
                "dataset": "CarDD",
                "license": "a verifier",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": DAMAGE_CLASSES_CARDD,
            },
            {
                "id": "damage-yolov11-vineet",
                "name": "YOLOv11n Car Damage",
                "provider": "Hugging Face",
                "architecture": "YOLOv11n",
                "source_url": "https://huggingface.co/vineetsarpal/yolov11n-car-damage",
                "dataset": "car damage",
                "license": "a verifier",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": DAMAGE_CLASSES_EXTENDED,
            },
        ],
    },
}


def detect_device():
    try:
        import torch

        if torch.cuda.is_available():
            return {"device": "cuda:0", "gpu_available": True}
    except Exception:
        pass

    return {"device": "cpu", "gpu_available": False}


def registry_with_local_status():
    registry = {}
    for task_id, task in MODEL_REGISTRY.items():
        registry[task_id] = {**task, "models": []}
        for model in task["models"]:
            registry[task_id]["models"].append({**model, "local": local_model_status(model["id"])})
    return registry
