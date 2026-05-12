# Guide Docker

Ce guide lance le studio de segmentation avec le backend Django, le frontend Vite et les volumes locaux pour conserver les images importees et les poids des modeles.

## Prerequis

- Docker Desktop installe et demarre.
- Les ports `5173` et `8000` disponibles.
- Les poids des modeles dans `backend/models/`. Ils ne sont pas versionnes dans Git.

## Telecharger les modeles

Depuis la racine du projet :

```bash
docker compose run --rm backend python scripts/download_models.py
```

Les fichiers sont sauvegardes dans `backend/models/` sur la machine locale grace au volume Docker.

## Lancer l'application

```bash
docker compose up --build
```

Ouvrir ensuite :

```text
http://127.0.0.1:5173
```

Le frontend appelle le backend sur `http://127.0.0.1:8000`. Le backend utilise le GPU si PyTorch detecte CUDA dans l'environnement Docker, sinon il bascule sur CPU.

## Voir les logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

Pour voir l'etat des conteneurs et des healthchecks :

```bash
docker compose ps
```

## Arreter

```bash
docker compose down
```

Les volumes montes gardent les donnees suivantes :

- `backend/models` : poids YOLO et MobileSAM.
- `backend/media` : images exemples, images importees et medias servis par Django.

## Relancer apres modification du code

```bash
docker compose up --build
```

Si un port est deja utilise, fermer l'ancien processus ou modifier les ports dans `docker-compose.yml`.
