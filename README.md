# Car Damage Annotation Viewer

A full-stack React + Django app for reviewing vehicle damage and car-part annotations from public computer-vision datasets.

The demo is seeded from the Hugging Face dataset [`moondream/car_part_damage`](https://huggingface.co/datasets/moondream/car_part_damage), using a small local sample so the app starts quickly.

## Stack

- Django 5 API
- React 19 + Vite
- SVG annotation overlay with zoom, pan, filtering, selection, and style controls
- GitHub Actions CI for backend and frontend checks

## Run Locally

Backend:

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py runserver 127.0.0.1:8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open http://127.0.0.1:5173.

## Dataset

The sample fixture lives in `backend/media/samples/annotations.json`, with downloaded image assets in `backend/media/samples/images`.
