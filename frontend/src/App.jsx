import { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

// ── Constants ─────────────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const FAST_POLL = 3_000;   // first 20s after mount
const SLOW_POLL = 30_000;  // thereafter
const FAST_DURATION = 20_000;

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt      = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const fmtDate  = (iso) => new Date(iso).toLocaleDateString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
const fmtMs    = (s)   => s < 1 ? `${Math.round(s * 1000)}ms` : `${s.toFixed(2)}s`;
const isHttp   = (s)   => { try { const u = new URL(s); return u.protocol === "http:" || u.protocol === "https:"; } catch { return false; } };

const uptimePct = (h) => {
  if (!h.length) return null;
  return ((h.filter(x => x.status === "UP").length / h.length) * 100).toFixed(1);
};
const avgLatency = (h) => {
  const up = h.filter(x => x.status === "UP");
  return up.length ? up.reduce((a, x) => a + x.latency, 0) / up.length : null;
};
const uptimeColor = (pct) =>
  pct == null ? null : pct >= 99 ? "var(--green)" : pct >= 95 ? "#f59e0b" : "var(--red)";

// ── API ───────────────────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" }, ...opts,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  if (res.status === 204) return null;
  return res.json();
}

// ── usePoller — shared polling logic ─────────────────────────────────────────
function usePoller(fn, { interval = SLOW_POLL } = {}) {
  useEffect(() => {
    let cancelled = false;
    const run = async () => { if (!cancelled) await fn(); };
    run();
    const id = setInterval(run, interval);
    return () => { cancelled = true; clearInterval(id); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

// ── Styles ────────────────────────────────────────────────────────────────────
const G = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:        #050810;
      --surface:   #0c0f1a;
      --surface2:  #111628;
      --border:    rgba(255,255,255,0.06);
      --text:      #e8eaf0;
      --muted:     #4b5470;
      --dim:       #2a2f45;
      --accent:    #6366f1;
      --aglow:     rgba(99,102,241,0.25);
      --green:     #10b981;
      --gglow:     rgba(16,185,129,0.2);
      --red:       #f43f5e;
      --rglow:     rgba(244,63,94,0.2);
      --mono:      'JetBrains Mono', monospace;
      --sans:      'Space Grotesk', system-ui, sans-serif;
      --r:         14px;
      --r-sm:      8px;
    }
    html, body { height: 100%; }
    body { background: var(--bg); color: var(--text); font-family: var(--sans); -webkit-font-smoothing: antialiased; }
    input, button { font-family: var(--sans); }
    input::placeholder { color: var(--dim); }
    input:focus { outline: none; border-color: rgba(99,102,241,0.6) !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-thumb { background: var(--surface2); border-radius: 4px; }

    .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); transition: border-color .2s, box-shadow .2s; }
    .card:hover { border-color: rgba(99,102,241,.25); box-shadow: 0 0 0 1px rgba(99,102,241,.08), 0 8px 32px rgba(0,0,0,.3); }

    .btn { display:inline-flex; align-items:center; gap:6px; border:none; border-radius:var(--r-sm); cursor:pointer; font-family:var(--sans); font-weight:500; transition:all .15s; white-space:nowrap; }
    .btn:disabled { opacity:.5; cursor:not-allowed; }
    .btn-primary { background:var(--accent); color:#fff; padding:10px 18px; font-size:14px; box-shadow:0 0 20px var(--aglow); }
    .btn-primary:hover:not(:disabled) { background:#4f46e5; box-shadow:0 0 28px var(--aglow); transform:translateY(-1px); }
    .btn-ghost { background:transparent; border:1px solid var(--border); color:var(--muted); padding:8px 14px; font-size:13px; }
    .btn-ghost:hover { border-color:rgba(255,255,255,.15); color:var(--text); }
    .btn-del { background:transparent; border:1px solid rgba(244,63,94,.25); color:var(--muted); padding:5px 10px; font-size:12px; border-radius:var(--r-sm); cursor:pointer; transition:all .15s; }
    .btn-del:hover { border-color:var(--red); color:var(--red); background:rgba(244,63,94,.06); }

    .tag { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }
    .tag-up   { background:var(--gglow); color:var(--green); border:1px solid rgba(16,185,129,.3); }
    .tag-down { background:var(--rglow); color:var(--red);   border:1px solid rgba(244,63,94,.3); }

    @keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.85)} }
    @keyframes spin       { to{transform:rotate(360deg)} }
    @keyframes slide-in   { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
    @keyframes fade-in    { from{opacity:0} to{opacity:1} }
    @keyframes expand     { from{opacity:0;transform:translateY(-6px)} to{opacity:1;transform:translateY(0)} }
  `}</style>
);

// ── Primitives ────────────────────────────────────────────────────────────────
const Dot = ({ status }) => (
  <span style={{
    display:"inline-block", width:7, height:7, borderRadius:"50%", flexShrink:0,
    background: status === "UP" ? "var(--green)" : "var(--red)",
    boxShadow: status === "UP" ? "0 0 8px var(--green)" : "0 0 8px var(--red)",
    animation: status === "UP" ? "pulse-dot 2s infinite" : "none",
  }} />
);

const Tag = ({ status }) => (
  <span className={`tag ${status === "UP" ? "tag-up" : "tag-down"}`}>
    <Dot status={status} />{status}
  </span>
);

const Spinner = ({ size = 14 }) => (
  <div style={{
    width:size, height:size, borderRadius:"50%", flexShrink:0,
    border:"2px solid rgba(255,255,255,.1)", borderTopColor:"var(--accent)",
    animation:"spin .7s linear infinite",
  }} />
);

const Label = ({ children }) => (
  <div style={{ fontSize:10, color:"var(--muted)", letterSpacing:".1em", textTransform:"uppercase", marginBottom:6 }}>
    {children}
  </div>
);

// ── StatTile ──────────────────────────────────────────────────────────────────
const StatTile = ({ label, value, accent }) => (
  <div style={{ background:"var(--surface2)", border:"1px solid var(--border)", borderRadius:10, padding:"14px 18px", flex:"1 1 110px", minWidth:110 }}>
    <Label>{label}</Label>
    <div style={{ fontSize:20, fontWeight:700, color:accent||"var(--text)", fontFamily:"var(--mono)", letterSpacing:"-.02em" }}>
      {value ?? "—"}
    </div>
  </div>
);

// ── UptimeBar ─────────────────────────────────────────────────────────────────
const UptimeBar = ({ history }) => {
  const blocks = [...history].slice(0, 30).reverse();
  if (!blocks.length) return <span style={{ fontSize:12, color:"var(--muted)" }}>No data yet</span>;
  return (
    <div style={{ display:"flex", gap:3, alignItems:"center" }}>
      {blocks.map((h, i) => (
        <div key={i} title={`${h.status} · ${fmtDate(h.checked_at)}`} style={{
          width:8, height:22, borderRadius:3, flexShrink:0,
          background: h.status === "UP" ? "var(--green)" : "var(--red)",
          opacity: 0.5 + (i / blocks.length) * 0.5,
        }} />
      ))}
    </div>
  );
};

// ── LatencyChart ──────────────────────────────────────────────────────────────
const LatencyChart = ({ history }) => {
  const data = [...history].reverse().slice(-40).map(h => ({
    time: fmt(h.checked_at),
    ms: h.status === "UP" ? +(h.latency * 1000).toFixed(1) : null,
  }));
  return (
    <ResponsiveContainer width="100%" height={120}>
      <AreaChart data={data} margin={{ top:4, right:4, left:0, bottom:0 }}>
        <defs>
          <linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.03)" vertical={false} />
        <XAxis dataKey="time" tick={{ fill:"#2a2f45", fontSize:9 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fill:"#2a2f45", fontSize:9 }} axisLine={false} tickLine={false} unit="ms" width={42} />
        <Tooltip
          contentStyle={{ background:"#0c0f1a", border:"1px solid rgba(255,255,255,.08)", borderRadius:8, fontSize:12, color:"#e8eaf0" }}
          formatter={v => v != null ? [`${v}ms`, "Latency"] : ["—", "Latency"]}
          labelStyle={{ color:"#4b5470", marginBottom:4 }}
        />
        <Area type="monotone" dataKey="ms" stroke="#6366f1" strokeWidth={2} fill="url(#lg)" dot={false} connectNulls={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
};

// ── DeletePopover ─────────────────────────────────────────────────────────────
const DeletePopover = ({ onConfirm, onCancel }) => {
  useEffect(() => {
    const h = (e) => { if (!e.target.closest("[data-pop]")) onCancel(); };
    const t = setTimeout(() => document.addEventListener("click", h), 10);
    return () => { clearTimeout(t); document.removeEventListener("click", h); };
  }, [onCancel]);

  return (
    <div data-pop onClick={e => e.stopPropagation()} style={{
      position:"absolute", right:0, top:"calc(100% + 8px)", zIndex:50,
      background:"#0c0f1a", border:"1px solid rgba(244,63,94,.3)",
      borderRadius:10, padding:"14px 16px", whiteSpace:"nowrap",
      boxShadow:"0 16px 40px rgba(0,0,0,.6)", animation:"expand .15s ease",
    }}>
      <p style={{ fontSize:13, color:"var(--text)", marginBottom:12, fontWeight:500 }}>Remove this service?</p>
      <div style={{ display:"flex", gap:8 }}>
        <button className="btn btn-ghost" style={{ fontSize:12, padding:"6px 12px" }} onClick={onCancel}>Cancel</button>
        <button className="btn" onClick={onConfirm}
          style={{ fontSize:12, padding:"6px 14px", background:"var(--red)", color:"#fff", borderRadius:7, fontWeight:600 }}>
          Delete
        </button>
      </div>
    </div>
  );
};

// ── ServiceCard ───────────────────────────────────────────────────────────────
function ServiceCard({ service, onDelete }) {
  const [history, setHistory]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [fetchErr, setFetchErr]   = useState("");
  const [expanded, setExpanded]   = useState(false);
  const [showDel, setShowDel]     = useState(false);
  const [deleting, setDeleting]   = useState(false);

  useEffect(() => {
    let cancelled = false;
    let slowId = null;

    const load = async () => {
      try {
        const data = await apiFetch(`/services/${service.id}/history?limit=50`);
        if (!cancelled) { setHistory(data); setFetchErr(""); setLoading(false); }
      } catch {
        if (!cancelled) { setFetchErr("Failed to load"); setLoading(false); }
      }
    };

    // Fast poll for first 20s so the immediate backend check shows up quickly,
    // then settle to 30s to reduce load.
    load();
    const fastId = setInterval(load, FAST_POLL);
    const switchId = setTimeout(() => {
      clearInterval(fastId);
      if (!cancelled) { load(); slowId = setInterval(load, SLOW_POLL); }
    }, FAST_DURATION);

    return () => {
      cancelled = true;
      clearInterval(fastId);
      clearTimeout(switchId);
      if (slowId) clearInterval(slowId);
    };
  }, [service.id]);

  const doDelete = async (e) => {
    e.stopPropagation();
    setShowDel(false);
    setDeleting(true);
    await onDelete(service.id);
  };

  const latest  = history[0];
  const uptime  = uptimePct(history);
  const latency = avgLatency(history);
  const uColor  = uptimeColor(Number(uptime));

  // The entire header row is one flex container.
  // Left side (name/url) gets onClick=toggle.
  // Right side stops propagation for status/delete, but chevron is OUTSIDE that stopper.
  return (
    <div className="card" style={{ animation:"slide-in .3s ease both" }}>

      {/* ── Header ── */}
      <div style={{ display:"flex", alignItems:"center", padding:"18px 20px", gap:12, userSelect:"none" }}>

        {/* Left — clickable to expand */}
        <div
          onClick={() => setExpanded(x => !x)}
          style={{ display:"flex", alignItems:"center", gap:14, flex:1, minWidth:0, cursor:"pointer" }}
        >
          <div style={{ flexShrink:0 }}>
            {loading ? <Spinner /> : <Dot status={latest?.status || "DOWN"} />}
          </div>
          <div style={{ minWidth:0 }}>
            <div style={{ fontWeight:600, fontSize:15, color:"var(--text)", marginBottom:2, whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>
              {service.name}
            </div>
            <div style={{ fontSize:12, color:"var(--muted)", fontFamily:"var(--mono)", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis", maxWidth:340 }}>
              {service.url}
            </div>
          </div>
        </div>

        {/* Right — actions (stopPropagation so clicks here don't toggle expand) */}
        <div style={{ display:"flex", alignItems:"center", gap:10, flexShrink:0 }} onClick={e => e.stopPropagation()}>
          {fetchErr
            ? <span style={{ fontSize:12, color:"var(--red)" }}>⚠ {fetchErr}</span>
            : latest
              ? <Tag status={latest.status} />
              : !loading && <span style={{ fontSize:12, color:"var(--muted)" }}>No data</span>
          }

          {uptime != null && (
            <span style={{ fontSize:12, fontFamily:"var(--mono)", color:uColor, fontWeight:600 }}>{uptime}%</span>
          )}

          <div style={{ position:"relative" }}>
            <button className="btn-del" disabled={deleting} onClick={e => { e.stopPropagation(); setShowDel(v => !v); }}>
              {deleting ? <Spinner size={11} /> : "✕"}
            </button>
            {showDel && <DeletePopover onConfirm={doDelete} onCancel={() => setShowDel(false)} />}
          </div>
        </div>

        {/* Chevron — OUTSIDE the stopPropagation wrapper, always toggles expand */}
        <div
          onClick={() => setExpanded(x => !x)}
          style={{
            color:"var(--muted)", fontSize:14, cursor:"pointer", flexShrink:0,
            transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
            transition:"transform .25s",
            padding:"4px 2px",
            lineHeight:1,
          }}
        >▾</div>

      </div>

      {/* ── Expanded panel ── */}
      {expanded && (
        <div style={{ borderTop:"1px solid var(--border)", padding:20, animation:"expand .2s ease" }}>
          <div style={{ display:"flex", gap:10, flexWrap:"wrap", marginBottom:20 }}>
            <StatTile label="Uptime"      value={uptime  != null ? `${uptime}%`  : null} accent={uColor} />
            <StatTile label="Avg Latency" value={latency != null ? fmtMs(latency): null} />
            <StatTile label="HTTP Status" value={latest?.status_code || null}
              accent={latest?.status === "UP" ? "var(--green)" : "var(--red)"} />
            <StatTile label="Checks"      value={history.length} />
          </div>

          <div style={{ marginBottom:18 }}>
            <Label>Last 30 checks</Label>
            <UptimeBar history={history} />
          </div>

          {history.length > 2 && (
            <div>
              <Label>Latency trend</Label>
              <LatencyChart history={history} />
            </div>
          )}

          {latest && (
            <div style={{ marginTop:14, fontSize:11, color:"var(--muted)", fontFamily:"var(--mono)" }}>
              Last checked {fmtDate(latest.checked_at)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── AddServiceModal ───────────────────────────────────────────────────────────
function AddServiceModal({ onAdd, onClose }) {
  const [name,    setName]    = useState("");
  const [url,     setUrl]     = useState("");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  useEffect(() => {
    const h = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  const submit = async () => {
    if (!name.trim())         { setError("Name is required"); return; }
    if (!isHttp(url.trim()))  { setError("Enter a valid URL starting with http:// or https://"); return; }
    setLoading(true); setError("");
    try {
      const svc = await apiFetch("/services", { method:"POST", body:JSON.stringify({ name:name.trim(), url:url.trim() }) });
      onAdd(svc); onClose();
    } catch (e) {
      setError(e.message); setLoading(false);
    }
  };

  const inp = { width:"100%", background:"var(--surface2)", border:"1px solid var(--border)", borderRadius:9, padding:"11px 14px", color:"var(--text)", fontSize:14, outline:"none" };

  return (
    <div onClick={onClose} style={{
      position:"fixed", inset:0, zIndex:200, background:"rgba(5,8,16,.85)",
      backdropFilter:"blur(6px)", display:"flex", alignItems:"center", justifyContent:"center",
      animation:"fade-in .15s ease", padding:"0 16px",
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background:"var(--surface)", border:"1px solid rgba(255,255,255,.09)",
        borderRadius:18, padding:32, width:"100%", maxWidth:460,
        boxShadow:"0 32px 80px rgba(0,0,0,.7)", animation:"slide-in .2s ease",
      }}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:24 }}>
          <div>
            <h2 style={{ fontSize:18, fontWeight:700, color:"var(--text)", marginBottom:4 }}>Add Service</h2>
            <p style={{ fontSize:13, color:"var(--muted)" }}>Monitor a URL every 2 minutes</p>
          </div>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding:"6px 10px", fontSize:16, lineHeight:1 }}>✕</button>
        </div>

        <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
          {[
            { label:"Service Name", val:name, set:setName, ph:"e.g. Production API" },
            { label:"URL",          val:url,  set:setUrl,  ph:"https://example.com" },
          ].map(({ label, val, set, ph }) => (
            <div key={label}>
              <Label>{label}</Label>
              <input style={inp} placeholder={ph} value={val}
                onChange={e => set(e.target.value)}
                onKeyDown={e => e.key === "Enter" && submit()}
                autoFocus={label === "Service Name"}
              />
            </div>
          ))}

          {error && (
            <div style={{ background:"rgba(244,63,94,.08)", border:"1px solid rgba(244,63,94,.2)", borderRadius:8, padding:"10px 14px", fontSize:13, color:"var(--red)" }}>
              {error}
            </div>
          )}

          <div style={{ display:"flex", gap:10, marginTop:4 }}>
            <button className="btn btn-ghost" onClick={onClose} style={{ flex:1, justifyContent:"center", padding:11 }}>Cancel</button>
            <button className="btn btn-primary" onClick={submit} disabled={loading}
              style={{ flex:2, justifyContent:"center", padding:11, borderRadius:9 }}>
              {loading ? <><Spinner /> Adding…</> : "Add Service"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [services, setServices] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [modal,    setModal]    = useState(false);

  usePoller(async () => {
    try {
      const data = await apiFetch("/services");
      setServices(data); setError(""); setLoading(false);
    } catch {
      setError("Cannot reach API — is Docker running?"); setLoading(false);
    }
  });

  const handleDelete = async (id) => {
    try {
      await apiFetch(`/services/${id}`, { method:"DELETE" });
      setServices(s => s.filter(x => x.id !== id));
    } catch (e) {
      setError(`Delete failed: ${e.message}`);
    }
  };

  return (
    <>
      <G />

      {/* Background */}
      <div style={{ position:"fixed", inset:0, zIndex:0, pointerEvents:"none", overflow:"hidden" }}>
        <div style={{ position:"absolute", inset:0, backgroundImage:"linear-gradient(rgba(99,102,241,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(99,102,241,.025) 1px,transparent 1px)", backgroundSize:"48px 48px" }} />
        <div style={{ position:"absolute", top:-300, left:"50%", transform:"translateX(-50%)", width:800, height:500, borderRadius:"50%", background:"radial-gradient(ellipse,rgba(99,102,241,.07) 0%,transparent 65%)" }} />
        <div style={{ position:"absolute", bottom:-200, right:-100, width:500, height:500, borderRadius:"50%", background:"radial-gradient(ellipse,rgba(16,185,129,.04) 0%,transparent 65%)" }} />
      </div>

      {/* Page */}
      <div style={{ position:"relative", zIndex:1, maxWidth:880, margin:"0 auto", padding:"48px 24px 100px" }}>

        {/* Header */}
        <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", marginBottom:40, gap:16 }}>
          <div>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:10 }}>
              <span style={{ width:7, height:7, borderRadius:"50%", background:"var(--accent)", boxShadow:"0 0 10px var(--accent)", display:"inline-block", animation:"pulse-dot 3s infinite" }} />
              <span style={{ fontSize:10, color:"var(--accent)", textTransform:"uppercase", letterSpacing:".18em", fontWeight:600 }}>Live Monitoring</span>
            </div>
            <h1 style={{ fontSize:38, fontWeight:700, color:"var(--text)", lineHeight:1.1, letterSpacing:"-.025em" }}>SLA Monitor</h1>
            <p style={{ marginTop:8, color:"var(--muted)", fontSize:14 }}>
              {services.length} service{services.length !== 1 ? "s" : ""} tracked · refreshes every 30s
            </p>
          </div>
          <button className="btn btn-primary" onClick={() => setModal(true)} style={{ marginTop:8, flexShrink:0 }}>
            <span style={{ fontSize:16, lineHeight:1 }}>+</span> Add Service
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={{ background:"rgba(244,63,94,.07)", border:"1px solid rgba(244,63,94,.2)", borderRadius:10, padding:"13px 18px", color:"var(--red)", fontSize:14, marginBottom:24, display:"flex", alignItems:"center", gap:10 }}>
            ⚠ {error}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div style={{ display:"flex", alignItems:"center", justifyContent:"center", gap:12, padding:"80px 0", color:"var(--muted)", fontSize:14 }}>
            <Spinner /> Loading services…
          </div>
        ) : services.length === 0 ? (
          <div style={{ textAlign:"center", padding:"90px 0", animation:"fade-in .4s ease" }}>
            <div style={{ fontSize:44, marginBottom:18 }}>📡</div>
            <p style={{ color:"var(--muted)", fontSize:16, fontWeight:500, marginBottom:6 }}>No services yet</p>
            <p style={{ color:"var(--dim)", fontSize:13 }}>Click "Add Service" to start monitoring a URL</p>
          </div>
        ) : (
          <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
            {services.map((svc, i) => (
              <div key={svc.id} style={{ animationDelay:`${i * 0.05}s` }}>
                <ServiceCard service={svc} onDelete={handleDelete} />
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop:72, textAlign:"center", color:"var(--dim)", fontSize:11, fontFamily:"var(--mono)", letterSpacing:".06em" }}>
          SLA MONITOR · FASTAPI + CELERY + REACT
        </div>
      </div>

      {modal && <AddServiceModal onAdd={svc => setServices(s => [...s, svc])} onClose={() => setModal(false)} />}
    </>
  );
}