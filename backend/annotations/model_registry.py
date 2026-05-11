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
                "id": "parts-yolov8-thanaphit",
                "name": "YOLOv8 Parts + Damage Seg",
                "provider": "Hugging Face Space",
                "architecture": "YOLOv8-seg",
                "source_url": "https://huggingface.co/spaces/Thanaphit/yolov8-car-parts-and-damage-segmentation",
                "dataset": "Car parts + damages, demo Space",
                "license": "a verifier sur le Space",
                "status": "demo open source",
                "device_preference": "cuda:0 -> cpu",
                "classes": CAR_PART_CLASSES,
            },
            {
                "id": "parts-yolov8-coco",
                "name": "YOLOv8x-seg COCO vehicule",
                "provider": "Ultralytics",
                "architecture": "YOLOv8x-seg",
                "source_url": "https://huggingface.co/Ultralytics/YOLOv8",
                "dataset": "COCO-Seg, baseline vehicule",
                "license": "AGPL-3.0",
                "status": "baseline telechargeable",
                "device_preference": "cuda:0 -> cpu",
                "classes": ["car", "truck", "bus", "motorcycle", "person"],
            },
            {
                "id": "parts-syndcar-yolo",
                "name": "SYNDCAR YOLO Seg",
                "provider": "Mendeley / YOLO",
                "architecture": "YOLO segmentation",
                "source_url": "https://data.mendeley.com/datasets/hzpj48krdt/1",
                "dataset": "SYNDCAR synthetic parts + damage",
                "license": "CC BY 4.0",
                "status": "dataset open, entrainement requis",
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
                "id": "damage-mask2former-carddd",
                "name": "Mask2Former Swin-L CardDD",
                "provider": "Hugging Face",
                "architecture": "Mask2Former + Swin-L",
                "source_url": "https://huggingface.co/benallaldev/carddd",
                "dataset": "Car damage polygon masks",
                "license": "MIT",
                "status": "poids publics",
                "device_preference": "cuda:0 -> cpu",
                "classes": ["rayure", "piece manquante", "phare casse", "trou", "peinture abimee", "bosselure", "verre casse"],
            },
            {
                "id": "damage-cardd-mmdet",
                "name": "CarDD MMDetection Baseline",
                "provider": "CarDD-USTC",
                "architecture": "Mask R-CNN / Cascade Mask R-CNN",
                "source_url": "https://github.com/CarDD-USTC/CarDD-USTC.github.io",
                "dataset": "CarDD",
                "license": "formulaire CarDD requis",
                "status": "code public, donnees sous formulaire",
                "device_preference": "cuda:0 -> cpu",
                "classes": DAMAGE_CLASSES_CARDD,
            },
            {
                "id": "damage-hitl-yolo",
                "name": "HITL Damage YOLO Seg",
                "provider": "Humans in the Loop",
                "architecture": "YOLO segmentation",
                "source_url": "https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/",
                "dataset": "Car Parts and Car Damages, CC0",
                "license": "CC0 1.0",
                "status": "dataset open, entrainement requis",
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
