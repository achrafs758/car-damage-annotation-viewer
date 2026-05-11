from pathlib import Path
from shutil import copyfile
import os
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
backend_root = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(backend_root / "models" / "_hf_home"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

from huggingface_hub import hf_hub_download

from annotations.local_models import LOCAL_MODEL_FILES


def main():
    for model_id, config in LOCAL_MODEL_FILES.items():
        target = Path(config["local_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            print(f"ok existing {model_id}: {target}")
            continue

        print(f"downloading {model_id} from {config['repo']}::{config['filename']}")
        downloaded = hf_hub_download(
            repo_id=config["repo"],
            filename=config["filename"],
            repo_type=config["repo_type"],
            local_dir=target.parent / "_hf_cache",
        )
        copyfile(downloaded, target)
        print(f"ok downloaded {model_id}: {target}")


if __name__ == "__main__":
    main()
