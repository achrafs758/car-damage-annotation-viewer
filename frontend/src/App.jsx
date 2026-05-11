import { useEffect, useMemo, useState } from "react";
import {
  Boxes,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Eye,
  EyeOff,
  Gauge,
  ImagePlus,
  Layers,
  Moon,
  Play,
  Search,
  Sun,
  Trash2,
  Upload
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const colors = ["#2dd4bf", "#f97316", "#60a5fa", "#e879f9", "#a3e635", "#f43f5e", "#facc15", "#38bdf8"];
const tasks = ["car_parts", "damage"];

function points(segmentation) {
  const polygon = segmentation?.[0];
  if (!Array.isArray(polygon)) return "";
  return polygon.reduce((pairs, value, index) => {
    if (index % 2 === 0) pairs.push(`${value},${polygon[index + 1]}`);
    return pairs;
  }, []).join(" ");
}

function decorate(output, modelIndex) {
  return {
    ...output,
    predictions: output.predictions.map((prediction, index) => ({
      ...prediction,
      color: colors[(index + modelIndex) % colors.length]
    }))
  };
}

export function App() {
  const [registry, setRegistry] = useState(null);
  const [images, setImages] = useState([]);
  const [task, setTask] = useState("car_parts");
  const [modelId, setModelId] = useState("all");
  const [activeIndex, setActiveIndex] = useState(0);
  const [predictionCache, setPredictionCache] = useState({});
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [query, setQuery] = useState("");
  const [showMasks, setShowMasks] = useState(true);
  const [showBoxes, setShowBoxes] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [opacity, setOpacity] = useState(45);
  const [threshold, setThreshold] = useState(50);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") ?? "dark");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    async function loadInitialWorkspace() {
      setBusy(true);
      setError("");
      try {
        const [samples, models] = await Promise.all([
          fetch(`${API_URL}/api/annotations/`).then((response) => response.json()),
          fetch(`${API_URL}/api/models/`).then((response) => response.json())
        ]);
        const sampleImages = samples.items.map((item) => ({ ...item, source: "sample", key: `sample-${item.id}` }));
        const predictionEntries = await Promise.all(sampleImages.map(async (image) => {
          const resultEntries = await Promise.all(tasks.map(async (nextTask) => {
            const params = new URLSearchParams({ task: nextTask, image_id: String(image.id) });
            const response = await fetch(`${API_URL}/api/predictions/?${params}`);
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.error ?? "Prediction impossible");
            return [nextTask, payload];
          }));
          return [image.key, Object.fromEntries(resultEntries)];
        }));

        setPredictionCache(Object.fromEntries(predictionEntries));
        setImages(sampleImages);
        setRegistry(models);
      } catch (caught) {
        setError(caught.message);
      } finally {
        setBusy(false);
      }
    }

    loadInitialWorkspace();
  }, []);

  const activeImage = images[activeIndex];
  const taskConfig = registry?.tasks?.[task];
  const currentModels = taskConfig?.models ?? [];
  const taskResult = activeImage ? predictionCache[activeImage.key]?.[task] : null;
  const hasSavedPredictions = activeImage ? tasks.every((nextTask) => predictionCache[activeImage.key]?.[nextTask]) : false;
  const canPredictActiveImage = activeImage?.source === "upload" && !hasSavedPredictions;
  const rawOutputs = useMemo(() => (taskResult?.outputs ?? []).map(decorate), [taskResult]);
  const outputs = modelId === "all" ? rawOutputs : rawOutputs.filter((output) => output.model.id === modelId);
  const activeOutput = outputs.find((output) => output.model.id === selectedModel) ?? outputs[0];

  const visiblePredictions = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!activeOutput) return [];
    return activeOutput.predictions.filter((prediction) => {
      if (prediction.confidence < threshold / 100) return false;
      if (!needle) return true;
      return prediction.category.toLowerCase().includes(needle) || String(prediction.id).toLowerCase().includes(needle);
    });
  }, [activeOutput, query, threshold]);

  const selectedPrediction = visiblePredictions.find((prediction) => prediction.id === selectedId) ?? visiblePredictions[0];

  useEffect(() => {
    setSelectedModel(null);
    setSelectedId(null);
  }, [task, modelId, activeIndex]);

  async function runAllPredictions(image = activeImage) {
    if (!image) return;
    if (image.source !== "upload" || tasks.every((nextTask) => predictionCache[image.key]?.[nextTask])) return;
    setBusy(true);
    setError("");
    try {
      const entries = [];
      for (const nextTask of tasks) {
        entries.push([nextTask, await predictTask(image, nextTask)]);
      }
      const nextResults = Object.fromEntries(entries);
      setPredictionCache((current) => ({
        ...current,
        [image.key]: {
          ...(current[image.key] ?? {}),
          ...nextResults
        }
      }));
      setSelectedModel(nextResults[task]?.outputs?.[0]?.model.id ?? null);
      setSelectedId(null);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function predictTask(image, nextTask) {
    if (image.source === "upload") {
      const response = await fetch(`${API_URL}/api/uploaded-predictions/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task: nextTask,
          image: {
            id: image.id,
            image_id: image.image_id,
            image_url: image.image_url,
            width: image.width,
            height: image.height
          }
        })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? "Prediction impossible");
      return payload;
    }

    const params = new URLSearchParams({ task: nextTask, image_id: String(image.id) });
    const response = await fetch(`${API_URL}/api/predictions/?${params}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error ?? "Prediction impossible");
    return payload;
  }

  async function uploadImage(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("image", file);
      const response = await fetch(`${API_URL}/api/uploads/`, { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? "Import impossible");
      const uploadedImage = payload.image;
      const uploaded = {
        ...uploadedImage,
        key: `upload-${uploadedImage.id}`,
        source: "upload",
      };
      setImages((current) => {
        setActiveIndex(current.length);
        return [...current, uploaded];
      });
      setSelectedId(null);
      setSelectedModel(null);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  function deleteActiveImage() {
    if (!activeImage || activeImage.source !== "upload") return;
    setPredictionCache((current) => {
      const next = { ...current };
      delete next[activeImage.key];
      return next;
    });
    setImages((current) => current.filter((image) => image.key !== activeImage.key));
    setActiveIndex((current) => Math.max(0, Math.min(current - 1, images.length - 2)));
    setSelectedId(null);
    setSelectedModel(null);
  }

  function moveImage(direction) {
    if (!images.length) return;
    const next = (activeIndex + direction + images.length) % images.length;
    setActiveIndex(next);
  }

  function imageSrc(image) {
    if (!image) return "";
    return `${API_URL}${image.image_url}`;
  }

  if (!registry || !images.length) {
    return <main className="loading">Chargement du studio IA...</main>;
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Layers size={22} /></div>
          <div>
            <strong>Studio Sinistre Auto</strong>
            <span>Segmentation IA assistee</span>
          </div>
        </div>

        <section className="panel">
          <div className="panel-title"><Boxes size={16} /> Tache</div>
          <div className="task-tabs">
            <button className={task === "car_parts" ? "active" : ""} onClick={() => setTask("car_parts")}>Pieces</button>
            <button className={task === "damage" ? "active" : ""} onClick={() => setTask("damage")}>Dommages</button>
          </div>
          <p className="hint">{taskConfig.description}</p>
        </section>

        <section className="panel">
          <div className="panel-title"><Cpu size={16} /> Modele</div>
          <select value={modelId} onChange={(event) => setModelId(event.target.value)}>
            <option value="all">Voir les {currentModels.length} modeles</option>
            {currentModels.map((model) => (
              <option key={model.id} value={model.id}>{model.name}</option>
            ))}
          </select>
          <div className="runtime">
            <Gauge size={15} />
            Execution par defaut : {registry.runtime.gpu_available ? "GPU cuda:0" : "CPU"}.
          </div>
        </section>

        <section className="panel">
          <div className="panel-title"><ImagePlus size={16} /> Image</div>
          <div className="image-nav">
            <button title="Image precedente" onClick={() => moveImage(-1)}><ChevronLeft size={17} /></button>
            <span>{activeIndex + 1} / {images.length}</span>
            <button title="Image suivante" onClick={() => moveImage(1)}><ChevronRight size={17} /></button>
          </div>
          <button className="primary" onClick={() => runAllPredictions()} disabled={busy || !canPredictActiveImage}>
            <Play size={16} /> {busy ? "Chargement..." : canPredictActiveImage ? `Predire ${registry.tasks.car_parts.models.length + registry.tasks.damage.models.length} modeles` : "Predictions sauvegardees"}
          </button>
          <p className="hint">{activeImage.source === "sample" ? "Predictions chargees depuis les preannotations." : hasSavedPredictions ? "Predictions deja calculees pour cette image." : "Nouvelle image : lancez la prediction une seule fois."}</p>
          <label className="upload-button">
            <Upload size={16} />
            Importer une image
            <input type="file" accept="image/*" onChange={uploadImage} />
          </label>
          {activeImage.source === "upload" && (
            <button className="danger" onClick={deleteActiveImage}><Trash2 size={16} /> Supprimer l'image</button>
          )}
          {error && <p className="error">{error}</p>}
        </section>

        <section className="panel">
          <div className="panel-title"><Search size={16} /> Filtre</div>
          <label className="search">
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Classe, id, piece..." />
          </label>
        </section>

        <section className="panel">
          <div className="panel-title"><Eye size={16} /> Affichage</div>
          <label><input type="checkbox" checked={showMasks} onChange={(event) => setShowMasks(event.target.checked)} /> Masques</label>
          <label><input type="checkbox" checked={showBoxes} onChange={(event) => setShowBoxes(event.target.checked)} /> Boites</label>
          <label><input type="checkbox" checked={showLabels} onChange={(event) => setShowLabels(event.target.checked)} /> Etiquettes</label>
          <label>Seuil confiance <strong>{threshold}%</strong><input type="range" min="0" max="95" step="5" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} /></label>
          <label>Opacite <input type="range" min="10" max="90" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /></label>
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">{taskConfig.label} - {activeImage.source === "upload" ? "image importee" : "echantillon preannote"}</span>
            <h1>{activeImage.image_id}</h1>
          </div>
          <div className="topbar-actions">
            <button title="Theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
              {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
            </button>
          </div>
        </header>

        <div className="model-strip">
          {outputs.length ? outputs.map((output) => (
            <button key={output.model.id} className={activeOutput?.model.id === output.model.id ? "model-card active" : "model-card"} onClick={() => setSelectedModel(output.model.id)}>
              <strong>{output.model.name}</strong>
              <span>{output.predictions.filter((prediction) => prediction.confidence >= threshold / 100).length} predictions - {output.local?.installed ? "local" : "non installe"} - {output.runtime.device}</span>
              {output.error && <small>{output.error}</small>}
            </button>
          )) : currentModels.map((model) => (
            <article key={model.id} className="model-card idle">
              <strong>{model.name}</strong>
              <span>{model.architecture} - en attente de prediction</span>
            </article>
          ))}
        </div>

        <div className="stage-wrap">
          <div className="stage" style={{ aspectRatio: `${activeImage.width} / ${activeImage.height}` }}>
            <img src={imageSrc(activeImage)} alt={activeImage.image_id} draggable="false" />
            <svg viewBox={`0 0 ${activeImage.width} ${activeImage.height}`} aria-label="Predictions IA">
              {visiblePredictions.map((prediction) => {
                const [x1, y1, x2, y2] = prediction.bbox;
                const isSelected = selectedPrediction?.id === prediction.id;
                return (
                  <g key={prediction.id} onClick={() => setSelectedId(prediction.id)} className={isSelected ? "selected-shape" : ""}>
                    {showMasks && <polygon points={points(prediction.segmentation)} fill={prediction.color} fillOpacity={opacity / 100} stroke={prediction.color} strokeWidth={isSelected ? 4 : 2} />}
                    {showBoxes && <rect x={x1} y={y1} width={x2 - x1} height={y2 - y1} fill="none" stroke={prediction.color} strokeWidth={isSelected ? 4 : 2} strokeDasharray={isSelected ? "0" : "8 5"} />}
                    {showLabels && <text x={x1 + 4} y={Math.max(18, y1 - 8)} fill={prediction.color}>{prediction.category} {Math.round(prediction.confidence * 100)}%</text>}
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        <footer className="details">
          <div>
            <span className="eyebrow">Modele actif</span>
            <strong>{activeOutput?.model.name ?? "Aucune prediction lancee"}</strong>
            <p>{activeOutput?.model.dataset ?? "Cliquez sur Predire les 2 taches pour generer les sorties des 8 modeles."}</p>
            {activeOutput?.local && <p>Poids locaux : {activeOutput.local.installed ? activeOutput.local.path : "non telecharges"}</p>}
          </div>
          <div>
            <span className="eyebrow">Classes du modele</span>
            <p>{activeOutput?.model.classes.join(", ") ?? currentModels[0]?.classes.join(", ")}</p>
          </div>
          <div>
            <span className="eyebrow">Prediction selectionnee</span>
            {selectedPrediction ? (
              <p>{selectedPrediction.category} - logit {selectedPrediction.logit} - confiance {Math.round(selectedPrediction.confidence * 100)}%</p>
            ) : (
              <p>Aucun masque selectionne.</p>
            )}
          </div>
          <button onClick={() => setShowMasks((value) => !value)}>{showMasks ? <EyeOff size={16} /> : <Eye size={16} />} Masques</button>
        </footer>
      </section>
    </main>
  );
}
