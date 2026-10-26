import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowLeftRight,
  Check,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  CircleX,
  Clock3,
  Download,
  Expand,
  Files,
  ImageOff,
  LoaderCircle,
  Menu,
  Minus,
  Moon,
  PanelsTopLeft,
  Plus,
  RefreshCw,
  Replace,
  Search,
  Sun,
  Trash2,
  X,
} from "lucide-react";
import "./styles.css";

const STATUS = {
  complete: ["Complete", CircleCheck, "good"],
  failed: ["Failed", CircleX, "bad"],
  running: ["In progress", LoaderCircle, "warning"],
  not_run: ["Not run", Clock3, "muted"],
  outside_run: ["Outside run", Clock3, "muted"],
  unmapped: ["Unmapped", Files, "muted"],
  unknown: ["Unrecorded", Clock3, "warning"],
};

function IconButton({ label, children, ...props }) {
  return (
    <button className="icon-button" aria-label={label} title={label} {...props}>
      {children}
    </button>
  );
}

function Status({ value }) {
  const [text, Icon, tone] = STATUS[value] || STATUS.unknown;
  return (
    <span className={`status ${tone}`}>
      <Icon size={14} />
      {text}
    </span>
  );
}

function Change({ value, compact = false }) {
  if (value == null) return <span className="muted">Not compared</span>;
  const tone =
    value > 10 ? "bad" : value > 2 ? "warning" : value > 0 ? "good" : "muted";
  const label = value > 0 && value < 0.01 ? "<0.01%" : `${value.toFixed(2)}%`;
  return (
    <span
      className={`change ${tone}`}
      title="Structural change: 100 x (1 - max(0, SSIM)). Not a percentage of changed pixels."
    >
      <span>{label}</span>
      {!compact && (
        <span className="change-track">
          <span style={{ width: `${Math.max(value > 0 ? 3 : 0, value)}%` }} />
        </span>
      )}
    </span>
  );
}

function Dimensions({ item }) {
  const old = item.baseline,
    next = item.candidate;
  const size = (image) =>
    image.width ? `${image.width} x ${image.height}` : "--";
  return (
    <span
      className={`dimensions ${item.dimensions_changed ? "warning" : "muted"}`}
    >
      {size(old)}
      {item.expected && (
        <>
          <ArrowLeftRight size={12} />
          {size(next)}
        </>
      )}
    </span>
  );
}

function ImagePane({
  item,
  side,
  thumbnail = false,
  onOpen,
  zoom = "fit",
  paneRef,
}) {
  const info = item[side];
  const missing = !info.exists || info.error;
  const title = side === "baseline" ? "Repository" : "Replacement";
  const message = info.error
    ? "Unreadable image"
    : side === "baseline"
      ? "Missing repository image"
      : item.expected
        ? "Missing replacement"
        : "Not captured in this run";
  const url = `/api/images/${item.id}/${side}?sha=${info.sha256}${thumbnail ? "&thumbnail=1" : ""}`;
  const [loadError, setLoadError] = useState(false);
  useEffect(() => setLoadError(false), [url]);
  const image = (
    <>
      {missing || loadError ? (
        <span className="missing-image">
          <ImageOff size={thumbnail ? 25 : 36} />
          <span>{loadError ? "Image changed or unavailable" : message}</span>
        </span>
      ) : (
        <img
          src={url}
          loading={thumbnail ? "lazy" : "eager"}
          alt={`${title}: ${item.asset}`}
          onError={() => setLoadError(true)}
          style={
            !thumbnail && zoom !== "fit"
              ? {
                  width: `${info.width * zoom}px`,
                  maxWidth: "none",
                  maxHeight: "none",
                }
              : undefined
          }
        />
      )}
    </>
  );
  return (
    <figure className={`image-pane ${thumbnail ? "thumbnail" : "enlarged"}`}>
      <figcaption>
        <span>{title}</span>
        <span>{info.width ? `${info.width} x ${info.height}` : "--"}</span>
      </figcaption>
      {thumbnail ? (
        <button
          className="thumbnail-button"
          onClick={onOpen}
          aria-label={`Enlarge ${title.toLowerCase()} image`}
          title="Enlarge comparison"
        >
          {image}
        </button>
      ) : (
        <div
          className={`pane-body ${zoom === "fit" ? "fit" : "actual"}`}
          ref={paneRef}
        >
          {image}
        </div>
      )}
    </figure>
  );
}

function Substitute({ item, selected, pending, onToggle }) {
  const disabled = !item.can_substitute || pending;
  return (
    <button
      className={`substitute ${selected ? "selected" : ""}`}
      aria-pressed={selected}
      disabled={disabled}
      onClick={() => onToggle(item)}
      title={
        disabled && !pending
          ? "Both images must exist and be readable."
          : selected
            ? "Remove substitution intention"
            : "Nominate this replacement"
      }
    >
      {pending ? (
        <LoaderCircle size={15} className="spin" />
      ) : selected ? (
        <Check size={15} />
      ) : (
        <Replace size={15} />
      )}
      {selected ? "Substitute selected" : "Substitute"}
    </button>
  );
}

function ImageIndicators({ item }) {
  return (
    <div className="image-indicators">
      <span className="metric-label">Change</span>
      <Change value={item.change_percent} compact />
      <Dimensions item={item} />
      {item.dimensions_changed && (
        <span className="flag warning">
          <ArrowLeftRight size={12} />
          Dimensions changed
        </span>
      )}
      {!item.baseline.exists && (
        <span className="flag bad">Repository missing</span>
      )}
      {item.expected && !item.candidate.exists && (
        <span className="flag bad">Replacement missing</span>
      )}
      {item.comparison_error && (
        <span className="flag warning" title={item.comparison_error}>
          Comparison error
        </span>
      )}
    </div>
  );
}

function ComparisonModal({
  rows,
  position,
  setPosition,
  comparisons,
  selected,
  pending,
  onToggle,
  onClose,
  error,
  onRefresh,
  refreshing,
}) {
  const dialog = useRef(null),
    oldPane = useRef(null),
    newPane = useRef(null),
    scrolling = useRef(false);
  const [zoom, setZoom] = useState("fit");
  const [linked, setLinked] = useState(true);
  const row = rows[position],
    item = comparisons[row.id];
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    return () => element.close();
  }, []);
  useEffect(() => {
    const keydown = (event) => {
      if (event.target instanceof HTMLInputElement) return;
      if (event.key === "ArrowRight")
        setPosition((p) => Math.min(rows.length - 1, p + 1));
      if (event.key === "ArrowLeft") setPosition((p) => Math.max(0, p - 1));
    };
    window.addEventListener("keydown", keydown);
    return () => window.removeEventListener("keydown", keydown);
  }, [rows.length, setPosition]);
  useEffect(() => {
    const a = oldPane.current,
      b = newPane.current;
    if (!linked || !a || !b) return;
    const sync = (source, target) => {
      if (scrolling.current) return;
      scrolling.current = true;
      target.scrollLeft = source.scrollLeft;
      target.scrollTop = source.scrollTop;
      requestAnimationFrame(() => {
        scrolling.current = false;
      });
    };
    const fromA = () => sync(a, b),
      fromB = () => sync(b, a);
    a.addEventListener("scroll", fromA);
    b.addEventListener("scroll", fromB);
    return () => {
      a.removeEventListener("scroll", fromA);
      b.removeEventListener("scroll", fromB);
    };
  }, [linked, row.id]);
  return (
    <dialog
      className="comparison-dialog"
      aria-labelledby="comparison-title"
      ref={dialog}
      onCancel={onClose}
    >
      <header className="dialog-header">
        <div className="dialog-title">
          <span className="eyebrow">
            IMAGE {position + 1} OF {rows.length}
          </span>
          <h2 id="comparison-title">{row.title}</h2>
        </div>
        <div className="dialog-actions">
          <IconButton
            label="Previous image"
            disabled={position === 0}
            onClick={() => setPosition(position - 1)}
          >
            <ChevronLeft size={18} />
          </IconButton>
          <IconButton
            label="Next image"
            disabled={position === rows.length - 1}
            onClick={() => setPosition(position + 1)}
          >
            <ChevronRight size={18} />
          </IconButton>
          <Substitute
            item={item}
            selected={selected.includes(item.id)}
            pending={pending === item.id}
            onToggle={onToggle}
          />
          <IconButton
            label="Refresh comparison"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={16} className={refreshing ? "spin" : ""} />
          </IconButton>
          <IconButton label="Close comparison" onClick={onClose}>
            <X size={20} />
          </IconButton>
        </div>
      </header>
      {error && (
        <div className="notice bad" role="alert">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}
      <div className="dialog-toolbar">
        <ImageIndicators item={item} />
        <div className="zoom-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={linked}
              onChange={(event) => setLinked(event.target.checked)}
            />
            Link scrolling
          </label>
          <IconButton
            label="Fit images"
            aria-pressed={zoom === "fit"}
            onClick={() => setZoom("fit")}
          >
            <Expand size={16} />
          </IconButton>
          <IconButton
            label="Zoom out"
            disabled={zoom !== "fit" && zoom <= 0.25}
            onClick={() =>
              setZoom(Math.max(0.25, (zoom === "fit" ? 1 : zoom) - 0.25))
            }
          >
            <Minus size={16} />
          </IconButton>
          <button
            className="zoom-value"
            onClick={() => setZoom(1)}
            title="Actual size"
          >
            {zoom === "fit" ? "Fit" : `${zoom * 100}%`}
          </button>
          <IconButton
            label="Zoom in"
            disabled={zoom !== "fit" && zoom >= 2}
            onClick={() =>
              setZoom(Math.min(2, (zoom === "fit" ? 1 : zoom) + 0.25))
            }
          >
            <Plus size={16} />
          </IconButton>
        </div>
      </div>
      <div className="enlarged-pair">
        <ImagePane item={item} side="baseline" zoom={zoom} paneRef={oldPane} />
        <ImagePane item={item} side="candidate" zoom={zoom} paneRef={newPane} />
      </div>
      <footer className="dialog-footer">
        <span>{item.asset}</span>
        <span>
          {row.recipe ? `${row.recipe} #${row.capture}` : row.coverage}
        </span>
      </footer>
    </dialog>
  );
}

function DocumentView({
  document,
  data,
  pending,
  onToggle,
  error,
  onRefresh,
  refreshing,
}) {
  const [position, setPosition] = useState(null);
  useEffect(() => {
    setPosition(null);
  }, [document.id]);
  return (
    <>
      <a className="back-link" href="#/">
        <ArrowLeft size={15} />
        All documents
      </a>
      <section className="document-header">
        <div>
          <span className="eyebrow">{document.section || "DOCUMENT"}</span>
          <h1>{document.title}</h1>
          <p className="document-path">
            {document.path || "No local document path"}
          </p>
        </div>
        <Status value={document.status} />
      </section>
      <div className="document-summary">
        <span>{document.images.length} image variants</span>
        <span className={document.changed ? "good" : ""}>
          {document.changed} changed
        </span>
        <span className={document.dimensions ? "warning" : ""}>
          {document.dimensions} resized
        </span>
        <span
          className={
            document.missing_candidate + document.missing_baseline ? "bad" : ""
          }
        >
          {document.missing_candidate + document.missing_baseline} missing
        </span>
      </div>
      {!document.exists && (
        <div className="notice warning">
          <AlertTriangle size={17} />
          Markdown document missing from the repository.
        </div>
      )}
      {document.status === "failed" && (
        <div className="notice bad">
          <CircleX size={18} />
          <div>
            <strong>Workflow failed</strong>
            {document.failure && <pre>{document.failure}</pre>}
          </div>
        </div>
      )}
      {document.images.length === 0 && (
        <div className="empty-state">
          <Files size={34} />
          <h2>No image mappings</h2>
          <span>
            {document.manifests.length
              ? "No images were resolved for this document."
              : "No manifest has been assigned."}
          </span>
        </div>
      )}
      <div className="image-list">
        {document.images.map((row, index) => {
          const item = data.comparisons[row.id];
          return (
            <article className="image-row" key={`${row.id}:${index}`}>
              <header className="image-row-header">
                <div className="image-heading">
                  <span className="image-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <h2>{row.title}</h2>
                    <span className="asset-path">{item.asset}</span>
                  </div>
                </div>
                <div className="image-row-actions">
                  <span className="variant">
                    {row.variant === "dark" ? (
                      <Moon size={12} />
                    ) : (
                      <Sun size={12} />
                    )}
                    {row.variant}
                  </span>
                  <IconButton
                    label={`Enlarge ${row.title}`}
                    onClick={() => setPosition(index)}
                  >
                    <Expand size={16} />
                  </IconButton>
                  <Substitute
                    item={item}
                    selected={data.selected.includes(item.id)}
                    pending={pending === item.id}
                    onToggle={onToggle}
                  />
                </div>
              </header>
              <ImageIndicators item={item} />
              <div className="thumbnail-pair">
                <ImagePane
                  item={item}
                  side="baseline"
                  thumbnail
                  onOpen={() => setPosition(index)}
                />
                <ImagePane
                  item={item}
                  side="candidate"
                  thumbnail
                  onOpen={() => setPosition(index)}
                />
              </div>
              <div className="image-row-footer">
                <span>
                  {row.recipe ? `${row.recipe} #${row.capture}` : row.coverage}
                </span>
                {item.documents.length > 1 && (
                  <span>
                    {item.documents.length} documents share this asset
                  </span>
                )}
                {data.stale.includes(item.id) && (
                  <span className="warning">Selection out of date</span>
                )}
              </div>
            </article>
          );
        })}
      </div>
      {position !== null && position < document.images.length && (
        <ComparisonModal
          rows={document.images}
          position={position}
          setPosition={setPosition}
          comparisons={data.comparisons}
          selected={data.selected}
          pending={pending}
          onToggle={onToggle}
          onClose={() => setPosition(null)}
          error={error}
          onRefresh={onRefresh}
          refreshing={refreshing}
        />
      )}
    </>
  );
}

function App() {
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all"),
    [section, setSection] = useState("");
  const [sort, setSort] = useState("run"),
    [pending, setPending] = useState(null),
    [navOpen, setNavOpen] = useState(false);
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const change = () => {
      setHash(window.location.hash);
      setNavOpen(false);
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  const load = async (refresh = false) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(
        refresh ? "/api/refresh" : "/api/review",
        refresh
          ? {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Review-Token": data.csrf_token,
              },
              body: "{}",
            }
          : {},
      );
      const payload = await response.json();
      if (!response.ok)
        throw new Error(payload.error || "Review could not be loaded.");
      setData(payload);
    } catch (failure) {
      setError(failure.message);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);
  const mutate = async (path, body) => {
    const response = await fetch(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Review-Token": data.csrf_token,
      },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok)
      throw new Error(payload.error || "Selection could not be saved.");
    setData(payload);
    setError("");
  };
  const toggle = async (item) => {
    setPending(item.id);
    try {
      await mutate("/api/substitutions", {
        id: item.id,
        selected: !data.selected.includes(item.id),
        baseline_sha256: item.baseline.sha256,
        candidate_sha256: item.candidate.sha256,
      });
    } catch (failure) {
      setError(failure.message);
    } finally {
      setPending(null);
    }
  };
  const clear = async () => {
    if (!window.confirm("Clear all substitution intentions for this run?"))
      return;
    try {
      await mutate("/api/clear", {});
    } catch (failure) {
      setError(failure.message);
    }
  };
  const docId = hash.startsWith("#/document/")
    ? decodeURIComponent(hash.slice("#/document/".length))
    : null;
  const current = data?.documents.find((document) => document.id === docId);
  const sections = [
    ...new Set(
      data?.documents.map((document) => document.section || "Uncategorized") ||
        [],
    ),
  ];
  const selectedDocument = (document) =>
    document.images.some(
      (image) =>
        data.selected.includes(image.id) || data.stale.includes(image.id),
    );
  const visible = data?.documents
    .filter((document) => {
      const text =
        `${document.title} ${document.path || ""} ${document.section}`.toLowerCase();
      return (
        text.includes(query.toLowerCase()) &&
        (!section || (document.section || "Uncategorized") === section) &&
        (filter === "all" ||
          (filter === "changed" && document.changed > 0) ||
          (filter === "dimensions" && document.dimensions > 0) ||
          (filter === "missing" &&
            document.missing_baseline + document.missing_candidate > 0) ||
          (filter === "failed" && document.status === "failed") ||
          (filter === "selected" && selectedDocument(document)))
      );
    })
    .sort((a, b) =>
      sort === "title"
        ? a.title.localeCompare(b.title)
        : sort === "change"
          ? (b.max_change ?? -1) - (a.max_change ?? -1)
          : [
              "failed",
              "running",
              "complete",
              "unknown",
              "not_run",
              "outside_run",
              "unmapped",
            ].indexOf(a.status) -
            [
              "failed",
              "running",
              "complete",
              "unknown",
              "not_run",
              "outside_run",
              "unmapped",
            ].indexOf(b.status),
    );
  const goMaster = (nextFilter, nextSection = "") => {
    window.location.hash = "/";
    setFilter(nextFilter);
    setSection(nextSection);
    setNavOpen(false);
  };
  return (
    <div className="app-shell">
      {navOpen && (
        <button
          className="nav-scrim"
          aria-label="Close navigation"
          onClick={() => setNavOpen(false)}
        />
      )}
      <aside className={`sidebar ${navOpen ? "open" : ""}`}>
        <a className="brand" href="#/">
          <span className="brand-icon">
            <PanelsTopLeft size={22} />
          </span>
          <span>
            <strong>Sunstone</strong>
            <small>Screenshot Review</small>
          </span>
        </a>
        <div className="run-label">
          <span className="eyebrow">CURRENT RUN</span>
          <strong title={data?.run.name}>
            {data?.run.name || "Loading run"}
          </strong>
          <span className="local-indicator">
            <span />
            Local review
          </span>
        </div>
        <nav aria-label="Review navigation">
          <button
            className={filter !== "selected" ? "active" : ""}
            onClick={() => goMaster("all")}
          >
            <Files size={17} />
            Documents<span>{data?.summary.documents ?? "--"}</span>
          </button>
          <button
            className={filter === "selected" ? "active" : ""}
            onClick={() => goMaster("selected")}
          >
            <CheckCheck size={17} />
            Substitutions<span>{data?.summary.selected ?? 0}</span>
          </button>
        </nav>
        <div className="section-navigation">
          <span className="eyebrow">SECTIONS</span>
          <button
            className={!section ? "active" : ""}
            onClick={() => goMaster("all")}
          >
            All sections
          </button>
          {sections.map((name) => (
            <button
              key={name}
              className={section === name ? "active" : ""}
              onClick={() => goMaster("all", name)}
            >
              {name}
              <span>
                {
                  data.documents.filter(
                    (d) => (d.section || "Uncategorized") === name,
                  ).length
                }
              </span>
            </button>
          ))}
        </div>
        <div className="sidebar-footer">
          <span className="eyebrow">REVIEW FILE</span>
          <span>review/substitutions.json</span>
        </div>
      </aside>
      <div className="workspace">
        <header className="app-header">
          <div className="header-title">
            <IconButton
              label="Toggle navigation"
              onClick={() => setNavOpen(!navOpen)}
            >
              <Menu size={19} />
            </IconButton>
            <span>Screenshot Automation</span>
            <span className="header-divider">/</span>
            <strong>Review</strong>
          </div>
          <div className="header-actions">
            <span className="saved-state">
              <Check size={13} />
              {data?.summary.selected || 0} selected
            </span>
            <IconButton
              label="Refresh comparisons"
              disabled={loading || !data}
              onClick={() => load(true)}
            >
              <RefreshCw size={17} className={loading ? "spin" : ""} />
            </IconButton>
            <a
              className="button secondary"
              href="/api/substitutions"
              download="substitutions.json"
            >
              <Download size={15} />
              <span>Export selections</span>
            </a>
          </div>
        </header>
        <main>
          {error && (
            <div className="notice bad" role="alert">
              <AlertTriangle size={18} />
              <span>{error}</span>
              <IconButton label="Dismiss error" onClick={() => setError("")}>
                <X size={15} />
              </IconButton>
            </div>
          )}
          {!data ? (
            <div className="empty-state">
              {loading ? (
                <LoaderCircle className="spin" size={30} />
              ) : (
                <AlertTriangle size={30} />
              )}
              <h1>
                {loading ? "Loading screenshot review" : "Review unavailable"}
              </h1>
              {!loading && (
                <button className="button secondary" onClick={() => load()}>
                  Retry
                </button>
              )}
            </div>
          ) : current ? (
            <DocumentView
              document={current}
              data={data}
              pending={pending}
              onToggle={toggle}
              error={error}
              onRefresh={() => load(true)}
              refreshing={loading}
            />
          ) : docId ? (
            <div className="empty-state">
              <Files size={30} />
              <h1>Document not found</h1>
              <a href="#/">All documents</a>
            </div>
          ) : (
            <>
              <section className="page-heading">
                <div>
                  <span className="eyebrow">AUTOMATION RESULTS</span>
                  <h1>Documents</h1>
                  <p>
                    {data.summary.documents} documents{" "}
                    <span className="dot-separator">/</span>{" "}
                    {data.summary.images} image comparisons
                  </p>
                </div>
                {data.selected.length + data.stale.length > 0 && (
                  <IconButton label="Clear selections" onClick={clear}>
                    <Trash2 size={17} />
                  </IconButton>
                )}
              </section>
              <section className="summary-strip" aria-label="Run summary">
                {[
                  [
                    "Changed images",
                    data.summary.changed,
                    ArrowLeftRight,
                    "good",
                    "changed",
                  ],
                  [
                    "Dimensions changed",
                    data.summary.dimensions,
                    Expand,
                    "warning",
                    "dimensions",
                  ],
                  [
                    "Missing images",
                    data.summary.missing_baseline +
                      data.summary.missing_candidate,
                    ImageOff,
                    "bad",
                    "missing",
                  ],
                  [
                    "Failed workflows",
                    data.summary.failed,
                    CircleX,
                    "bad",
                    "failed",
                  ],
                  [
                    "Substitutions",
                    data.summary.selected,
                    CheckCheck,
                    "good",
                    "selected",
                  ],
                ].map(([label, value, Icon, tone, target]) => (
                  <button
                    className="summary-item"
                    key={label}
                    onClick={() => setFilter(target)}
                  >
                    <span>
                      <Icon size={16} />
                      {label}
                    </span>
                    <strong className={value ? tone : ""}>{value}</strong>
                  </button>
                ))}
              </section>
              {data.summary.stale > 0 && (
                <div className="notice warning">
                  <AlertTriangle size={16} />
                  {data.summary.stale} substitution selections are out of date.
                </div>
              )}
              {data.notes.map((note) => (
                <div className="notice warning" key={note}>
                  <AlertTriangle size={16} />
                  {note}
                </div>
              ))}
              <div className="list-toolbar">
                <label className="search-field">
                  <Search size={16} />
                  <input
                    aria-label="Search documents"
                    placeholder="Search documents..."
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                  {query && (
                    <IconButton
                      label="Clear search"
                      onClick={() => setQuery("")}
                    >
                      <X size={14} />
                    </IconButton>
                  )}
                </label>
                <div className="filter-tabs" aria-label="Document filters">
                  {[
                    ["all", "All"],
                    ["changed", "Changed"],
                    ["dimensions", "Resized"],
                    ["missing", "Missing"],
                    ["failed", "Failed"],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      aria-pressed={filter === value}
                      className={filter === value ? "active" : ""}
                      onClick={() => setFilter(value)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <select
                  aria-label="Sort documents"
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                >
                  <option value="run">Run status</option>
                  <option value="change">Largest change</option>
                  <option value="title">Document title</option>
                </select>
              </div>
              <div className="table-meta">
                <span>
                  {visible.length} documents{section && ` in ${section}`}
                  {filter === "selected" && " with substitution selections"}
                </span>
                <span>
                  Structural change <span className="ssim-label">SSIM</span>
                </span>
              </div>
              <div className="table-scroll">
                <table className="documents-table">
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>Workflow</th>
                      <th>Max. change</th>
                      <th>Dimensions</th>
                      <th>Missing</th>
                      <th>Selected</th>
                      <th>
                        <span className="sr-only">Open</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((document) => {
                      const picked = new Set(
                        document.images
                          .filter((image) => data.selected.includes(image.id))
                          .map((image) => image.id),
                      ).size;
                      const open = () => {
                        window.location.hash = `/document/${encodeURIComponent(document.id)}`;
                      };
                      return (
                        <tr key={document.id} onClick={open}>
                          <td>
                            <a
                              className="document-title"
                              href={`#/document/${encodeURIComponent(document.id)}`}
                              onClick={(event) => event.stopPropagation()}
                            >
                              {document.title}
                            </a>
                            <span className="table-path" title={document.path}>
                              {document.path ||
                                document.section ||
                                "Unresolved document"}
                              {!document.exists && document.path && (
                                <AlertTriangle size={12} />
                              )}
                            </span>
                          </td>
                          <td>
                            <Status value={document.status} />
                          </td>
                          <td>
                            <Change value={document.max_change} />
                            {document.changed > 0 && (
                              <span className="cell-note">
                                {document.changed} changed
                              </span>
                            )}
                          </td>
                          <td>
                            {document.dimensions ? (
                              <span className="count-indicator warning">
                                <Expand size={14} />
                                {document.dimensions}
                              </span>
                            ) : (
                              <span className="muted">--</span>
                            )}
                          </td>
                          <td>
                            <div className="missing-counts">
                              {document.missing_baseline > 0 && (
                                <span
                                  className="flag bad"
                                  title="Missing repository images"
                                >
                                  {document.missing_baseline} repo
                                </span>
                              )}
                              {document.missing_candidate > 0 && (
                                <span
                                  className="flag bad"
                                  title="Missing replacement images"
                                >
                                  {document.missing_candidate} new
                                </span>
                              )}
                              {document.missing_baseline +
                                document.missing_candidate ===
                                0 && <span className="muted">--</span>}
                            </div>
                          </td>
                          <td>
                            {picked ? (
                              <span className="count-indicator good">
                                <CheckCheck size={14} />
                                {picked}
                              </span>
                            ) : (
                              <span className="muted">--</span>
                            )}
                          </td>
                          <td>
                            <IconButton
                              label={`Open ${document.title}`}
                              onClick={(event) => {
                                event.stopPropagation();
                                open();
                              }}
                            >
                              <ChevronRight size={16} />
                            </IconButton>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {visible.length === 0 && (
                <div className="empty-state">
                  <Search size={28} />
                  <h2>No matching documents</h2>
                  <button
                    className="button secondary"
                    onClick={() => {
                      setQuery("");
                      setFilter("all");
                      setSection("");
                    }}
                  >
                    Clear filters
                  </button>
                </div>
              )}
              <footer className="list-footer">
                <span>
                  {data.catalogue_diagnostics.errors} catalogue errors{" "}
                  <span className="dot-separator">/</span>{" "}
                  {data.catalogue_diagnostics.warnings} coverage warnings
                </span>
                <span>{data.selection_file}</span>
              </footer>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
