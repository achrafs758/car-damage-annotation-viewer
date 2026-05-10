import { useEffect, useMemo, useState } from "react";
import {
  Box,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  Layers,
  Maximize2,
  Moon,
  Move,
  RefreshCw,
  Search,
  Sun,
  Tags
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const palette = ["#2dd4bf", "#f97316", "#60a5fa", "#e879f9", "#a3e635", "#f43f5e", "#facc15", "#38bdf8"];

function toPoints(segmentation) {
  if (!segmentation?.length) return "";
  return segmentation[0].reduce((pairs, value, index) => {
    if (index % 2 === 0) pairs.push(`${value},${segmentation[0][index + 1]}`);
    return pairs;
  }, []).join(" ");
}

function normalizeItem(item) {
  return {
    ...item,
    annotations: item.annotations.map((annotation, index) => ({
      ...annotation,
      color: palette[index % palette.length],
      visible: true
    }))
  };
}

export function App() {
  const [dataset, setDataset] = useState(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [selectedId, setSelectedId] = useState(null);
  const [query, setQuery] = useState("");
  const [showBoxes, setShowBoxes] = useState(true);
  const [showPolygons, setShowPolygons] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [opacity, setOpacity] = useState(42);
  const [strokeWidth, setStrokeWidth] = useState(2);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") ?? "dark");
  const [hiddenCategories, setHiddenCategories] = useState(new Set());

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    fetch(`${API_URL}/api/annotations/`)
      .then((response) => {
        if (!response.ok) throw new Error("Unable to load annotations");
        return response.json();
      })
      .then((payload) => setDataset({ ...payload, items: payload.items.map(normalizeItem) }))
      .catch(() => setDataset({ source: "Unavailable", items: [] }));
  }, []);

  const active = dataset?.items[activeIndex];
  const categories = useMemo(() => {
    if (!dataset) return [];
    return [...new Set(dataset.items.flatMap((item) => item.annotations.map((annotation) => annotation.category)))].sort();
  }, [dataset]);

  const visibleAnnotations = useMemo(() => {
    if (!active) return [];
    const needle = query.trim().toLowerCase();
    return active.annotations.filter((annotation) => {
      const matchesText = !needle || annotation.category.toLowerCase().includes(needle) || String(annotation.id).includes(needle);
      return matchesText && !hiddenCategories.has(annotation.category);
    });
  }, [active, hiddenCategories, query]);

  const selected = visibleAnnotations.find((annotation) => annotation.id === selectedId) ?? visibleAnnotations[0];

  function moveImage(direction) {
    setActiveIndex((current) => {
      const next = (current + direction + dataset.items.length) % dataset.items.length;
      setSelectedId(null);
      setPan({ x: 0, y: 0 });
      setZoom(1);
      return next;
    });
  }

  function toggleCategory(category) {
    setHiddenCategories((current) => {
      const next = new Set(current);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }

  if (!dataset) {
    return <main className="loading">Loading annotation workspace...</main>;
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Layers size={22} /></div>
          <div>
            <strong>Damage Studio</strong>
            <span>Annotation review</span>
          </div>
        </div>

        <label className="search">
          <Search size={17} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find category or id" />
        </label>

        <section className="panel">
          <div className="panel-title"><Tags size={16} /> Classes</div>
          <div className="class-list">
            {categories.map((category) => (
              <button key={category} className={hiddenCategories.has(category) ? "muted class-chip" : "class-chip"} onClick={() => toggleCategory(category)}>
                {hiddenCategories.has(category) ? <EyeOff size={14} /> : <Eye size={14} />}
                {category}
              </button>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-title"><Box size={16} /> Selected</div>
          {selected ? (
            <dl className="metrics">
              <div><dt>Class</dt><dd>{selected.category}</dd></div>
              <div><dt>ID</dt><dd>{selected.id}</dd></div>
              <div><dt>Box</dt><dd>{selected.bbox.map(Math.round).join(", ")}</dd></div>
            </dl>
          ) : (
            <p className="empty">No visible annotation.</p>
          )}
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">{dataset.source}</span>
            <h1>{active?.image_id ?? "No sample loaded"}</h1>
          </div>
          <div className="topbar-actions">
            <button title="Previous image" onClick={() => moveImage(-1)}><ChevronLeft size={18} /></button>
            <span className="counter">{activeIndex + 1} / {dataset.items.length}</span>
            <button title="Next image" onClick={() => moveImage(1)}><ChevronRight size={18} /></button>
            <button title="Toggle theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        <div className="toolbar">
          <label><input type="checkbox" checked={showPolygons} onChange={(event) => setShowPolygons(event.target.checked)} /> Polygons</label>
          <label><input type="checkbox" checked={showBoxes} onChange={(event) => setShowBoxes(event.target.checked)} /> Boxes</label>
          <label><input type="checkbox" checked={showLabels} onChange={(event) => setShowLabels(event.target.checked)} /> Labels</label>
          <label>Opacity <input type="range" min="10" max="90" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /></label>
          <label>Stroke <input type="range" min="1" max="6" value={strokeWidth} onChange={(event) => setStrokeWidth(Number(event.target.value))} /></label>
          <button title="Reset view" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}><RefreshCw size={16} /> Reset</button>
          <button title="Fit image" onClick={() => setZoom(1)}><Maximize2 size={16} /> Fit</button>
        </div>

        <div className="stage-wrap">
          {active && (
            <div
              className="stage"
              style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
              onWheel={(event) => {
                event.preventDefault();
                setZoom((current) => Math.min(3, Math.max(0.45, current + (event.deltaY > 0 ? -0.08 : 0.08))));
              }}
            >
              <img src={`${API_URL}${active.image_url}`} alt={active.image_id} draggable="false" />
              <svg viewBox={`0 0 ${active.width} ${active.height}`} aria-label="Annotation overlay">
                {visibleAnnotations.map((annotation) => {
                  const [x1, y1, x2, y2] = annotation.bbox;
                  const isSelected = selected?.id === annotation.id;
                  return (
                    <g key={annotation.id} onClick={() => setSelectedId(annotation.id)} className={isSelected ? "selected-shape" : ""}>
                      {showPolygons && (
                        <polygon
                          points={toPoints(annotation.segmentation)}
                          fill={annotation.color}
                          fillOpacity={opacity / 100}
                          stroke={annotation.color}
                          strokeWidth={isSelected ? strokeWidth + 1.5 : strokeWidth}
                        />
                      )}
                      {showBoxes && (
                        <rect
                          x={x1}
                          y={y1}
                          width={x2 - x1}
                          height={y2 - y1}
                          fill="none"
                          stroke={annotation.color}
                          strokeDasharray={isSelected ? "0" : "8 5"}
                          strokeWidth={isSelected ? strokeWidth + 1 : strokeWidth}
                        />
                      )}
                      {showLabels && (
                        <text x={x1 + 4} y={Math.max(18, y1 - 8)} fill={annotation.color}>{annotation.category}</text>
                      )}
                    </g>
                  );
                })}
              </svg>
            </div>
          )}
        </div>

        <footer className="bottom-bar">
          <button onClick={() => setPan((current) => ({ ...current, x: current.x - 30 }))}><Move size={15} /> Left</button>
          <button onClick={() => setPan((current) => ({ ...current, x: current.x + 30 }))}><Move size={15} /> Right</button>
          <button onClick={() => setPan((current) => ({ ...current, y: current.y - 30 }))}><Move size={15} /> Up</button>
          <button onClick={() => setPan((current) => ({ ...current, y: current.y + 30 }))}><Move size={15} /> Down</button>
          <label>Zoom <input type="range" min="45" max="300" value={Math.round(zoom * 100)} onChange={(event) => setZoom(Number(event.target.value) / 100)} /></label>
        </footer>
      </section>
    </main>
  );
}
