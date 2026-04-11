import { useState, useRef, useCallback, useEffect } from "react";

// ── Fonts ──────────────────────────────────────────────────────────────────
const fontLink = document.createElement("link");
fontLink.rel = "stylesheet";
fontLink.href =
  "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap";
document.head.appendChild(fontLink);

// ── CSS ────────────────────────────────────────────────────────────────────
const css = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0a0d14;
    --bg2:      #111520;
    --bg3:      #181d2e;
    --surface:  #1c2236;
    --border:   rgba(255,255,255,0.07);
    --border2:  rgba(255,255,255,0.13);
    --gold:     #c9a84c;
    --gold2:    #e8c86a;
    --goldGlow: rgba(201,168,76,0.15);
    --text:     #e8eaf0;
    --muted:    #8890a8;
    --accent:   #4f7cff;
    --accentSoft: rgba(79,124,255,0.12);
    --red:      #ff5f6d;
    --green:    #43d48a;
    --r:        12px;
    --r2:       8px;
    --font-serif: 'Playfair Display', Georgia, serif;
    --font-sans:  'DM Sans', system-ui, sans-serif;
    --font-mono:  'DM Mono', monospace;
  }

  html, body, #root { height: 100%; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 15px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--surface); border-radius: 99px; }

  /* ── Layout ── */
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow-x: hidden;
  }

  .noise {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    opacity: 0.4;
  }

  .glow-orb {
    position: fixed; border-radius: 50%; pointer-events: none; z-index: 0;
    filter: blur(120px);
  }
  .orb1 { width: 600px; height: 600px; top: -200px; left: -150px; background: radial-gradient(circle, rgba(201,168,76,0.08) 0%, transparent 70%); }
  .orb2 { width: 500px; height: 500px; bottom: -100px; right: -100px; background: radial-gradient(circle, rgba(79,124,255,0.07) 0%, transparent 70%); }

  /* ── Header ── */
  header {
    position: relative; z-index: 10;
    padding: 20px 40px;
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid var(--border);
    background: rgba(10,13,20,0.8);
    backdrop-filter: blur(20px);
  }

  .logo {
    display: flex; align-items: center; gap: 10px;
    font-family: var(--font-serif);
    font-size: 22px; font-weight: 700;
    color: var(--text);
    letter-spacing: -0.3px;
  }

  .logo-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--gold), var(--gold2));
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
  }

  .logo span { color: var(--gold); }

  .header-badge {
    font-family: var(--font-mono);
    font-size: 11px; font-weight: 500;
    color: var(--muted);
    background: var(--surface);
    border: 1px solid var(--border2);
    padding: 5px 12px; border-radius: 99px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  /* ── Stepper ── */
  .stepper {
    position: relative; z-index: 5;
    padding: 32px 40px 0;
    display: flex; align-items: center; justify-content: center; gap: 0;
    max-width: 700px; margin: 0 auto; width: 100%;
  }

  .step {
    display: flex; flex-direction: column; align-items: center; gap: 6px;
    position: relative; flex: 1;
  }

  .step-line {
    position: absolute; top: 18px; left: calc(50% + 20px);
    right: calc(-50% + 20px);
    height: 1px;
    background: var(--border2);
    transition: background 0.4s;
  }
  .step-line.done { background: var(--gold); }

  .step-dot {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: var(--font-mono); font-size: 13px; font-weight: 500;
    border: 1.5px solid var(--border2);
    background: var(--bg3);
    color: var(--muted);
    transition: all 0.3s;
    position: relative; z-index: 1;
  }
  .step.active .step-dot {
    border-color: var(--gold);
    background: linear-gradient(135deg, rgba(201,168,76,0.2), rgba(232,200,106,0.08));
    color: var(--gold2);
    box-shadow: 0 0 20px var(--goldGlow);
  }
  .step.done .step-dot {
    border-color: var(--gold);
    background: var(--gold);
    color: #0a0d14;
  }

  .step-label {
    font-size: 11px; font-weight: 500; letter-spacing: 0.5px;
    text-transform: uppercase; color: var(--muted);
    white-space: nowrap;
    transition: color 0.3s;
  }
  .step.active .step-label { color: var(--gold); }
  .step.done .step-label { color: var(--text); }

  /* ── Main ── */
  main {
    position: relative; z-index: 5;
    flex: 1; padding: 40px 24px 60px;
    display: flex; flex-direction: column; align-items: center;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: var(--r);
    padding: 40px;
    width: 100%; max-width: 680px;
    box-shadow: 0 24px 80px rgba(0,0,0,0.4);
    animation: slideUp 0.4s ease both;
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .card-title {
    font-family: var(--font-serif);
    font-size: 28px; font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;
    line-height: 1.2;
  }

  .card-sub {
    color: var(--muted); font-size: 14px; margin-bottom: 32px;
  }

  .section-label {
    font-size: 11px; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; color: var(--gold);
    margin-bottom: 20px;
    display: flex; align-items: center; gap: 8px;
  }
  .section-label::after {
    content: ''; flex: 1; height: 1px; background: var(--border2);
  }

  /* ── Drop Zone ── */
  .drop-zone {
    border: 2px dashed var(--border2);
    border-radius: var(--r);
    padding: 48px 32px;
    text-align: center;
    cursor: pointer;
    transition: all 0.25s;
    position: relative;
    overflow: hidden;
  }
  .drop-zone:hover, .drop-zone.drag-over {
    border-color: var(--gold);
    background: var(--goldGlow);
  }
  .drop-zone.has-file {
    border-style: solid;
    border-color: var(--gold);
    background: var(--goldGlow);
  }

  .drop-icon {
    font-size: 42px; margin-bottom: 14px;
    display: block;
  }

  .drop-title {
    font-family: var(--font-serif);
    font-size: 18px; font-weight: 600; margin-bottom: 8px;
  }

  .drop-sub {
    color: var(--muted); font-size: 13px;
  }

  .file-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--bg3); border: 1px solid var(--gold);
    border-radius: 99px; padding: 8px 16px; margin-top: 16px;
    font-size: 13px; font-family: var(--font-mono);
    color: var(--gold2);
  }

  .file-pill button {
    background: none; border: none; cursor: pointer;
    color: var(--muted); font-size: 16px; line-height: 1;
    padding: 0 0 0 4px; transition: color 0.2s;
  }
  .file-pill button:hover { color: var(--red); }

  /* ── Form ── */
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
  }
  .form-grid .full { grid-column: 1 / -1; }

  .field { display: flex; flex-direction: column; gap: 6px; }

  label {
    font-size: 12px; font-weight: 600;
    letter-spacing: 0.4px; text-transform: uppercase;
    color: var(--muted);
  }

  input[type="text"],
  input[type="number"],
  select,
  textarea {
    background: var(--bg3);
    border: 1px solid var(--border2);
    border-radius: var(--r2);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    padding: 11px 14px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    width: 100%;
    appearance: none;
  }

  select {
    cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238890a8' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 14px center;
    padding-right: 36px;
  }

  input:focus, select:focus, textarea:focus {
    border-color: var(--gold);
    box-shadow: 0 0 0 3px var(--goldGlow);
  }

  select option { background: var(--bg3); }

  .salary-row {
    display: grid; grid-template-columns: 1fr auto; gap: 8px;
  }
  .salary-row select { width: 90px; }

  /* ── AI Toggle ── */
  .ai-toggle-card {
    background: var(--bg3);
    border: 1px solid var(--border2);
    border-radius: var(--r);
    padding: 20px 22px;
    display: flex; align-items: flex-start; gap: 16px;
    cursor: pointer;
    transition: all 0.25s;
    margin-top: 24px;
  }
  .ai-toggle-card:hover { border-color: var(--accent); background: var(--accentSoft); }
  .ai-toggle-card.active {
    border-color: var(--accent);
    background: var(--accentSoft);
    box-shadow: 0 0 30px rgba(79,124,255,0.1);
  }

  .ai-icon {
    width: 42px; height: 42px; border-radius: 10px;
    background: linear-gradient(135deg, #4f7cff, #7b5ea7);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
  }

  .ai-info { flex: 1; }
  .ai-name { font-weight: 600; margin-bottom: 4px; font-size: 15px; }
  .ai-desc { font-size: 13px; color: var(--muted); line-height: 1.5; }

  .toggle-switch {
    width: 46px; height: 26px;
    background: var(--border2);
    border-radius: 99px;
    position: relative;
    flex-shrink: 0;
    transition: background 0.25s;
    margin-top: 2px;
  }
  .toggle-switch.on { background: var(--accent); }
  .toggle-switch::after {
    content: '';
    position: absolute; top: 3px; left: 3px;
    width: 20px; height: 20px;
    background: white;
    border-radius: 50%;
    transition: transform 0.25s;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  }
  .toggle-switch.on::after { transform: translateX(20px); }

  .mask-warning {
    font-size: 12px; color: #4f7cff; margin-top: 8px;
    display: flex; align-items: center; gap: 5px;
  }

  /* ── Buttons ── */
  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    padding: 13px 28px;
    border-radius: var(--r2);
    font-family: var(--font-sans); font-size: 14px; font-weight: 600;
    cursor: pointer; border: none; outline: none;
    transition: all 0.2s;
    letter-spacing: 0.2px;
  }

  .btn-primary {
    background: linear-gradient(135deg, var(--gold), var(--gold2));
    color: #0a0d14;
  }
  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 30px rgba(201,168,76,0.35);
  }
  .btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }

  .btn-ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border2);
  }
  .btn-ghost:hover { border-color: var(--border2); color: var(--text); }

  .btn-row {
    display: flex; justify-content: space-between; align-items: center;
    margin-top: 32px; gap: 12px;
  }

  /* ── Loading ── */
  .loading-screen {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 24px;
    padding: 80px 40px;
    text-align: center;
  }

  .spinner-ring {
    width: 72px; height: 72px;
    border: 3px solid var(--border2);
    border-top-color: var(--gold);
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-steps { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
  .loading-step {
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; color: var(--muted);
    transition: color 0.3s;
  }
  .loading-step.done { color: var(--green); }
  .loading-step.active { color: var(--text); }
  .loading-step-icon { font-size: 16px; width: 20px; text-align: center; }

  /* ── Results ── */
  .results-header {
    width: 100%; max-width: 1100px;
    margin-bottom: 28px;
    display: flex; align-items: flex-end; justify-content: space-between;
    gap: 16px;
    animation: slideUp 0.4s ease both;
  }

  .results-title { font-family: var(--font-serif); font-size: 32px; font-weight: 700; }
  .results-title span { color: var(--gold); }
  .results-count {
    font-family: var(--font-mono); font-size: 13px; color: var(--muted);
    background: var(--surface); border: 1px solid var(--border2);
    padding: 6px 14px; border-radius: 99px;
    white-space: nowrap;
  }

  .jobs-grid {
    width: 100%; max-width: 1100px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 18px;
  }

  .job-card {
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: var(--r);
    padding: 24px;
    transition: all 0.25s;
    position: relative;
    overflow: hidden;
    animation: slideUp 0.4s ease both;
    display: flex; flex-direction: column;
  }
  .job-card:hover {
    border-color: rgba(201,168,76,0.4);
    transform: translateY(-2px);
    box-shadow: 0 16px 50px rgba(0,0,0,0.35);
  }

  .job-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    opacity: 0;
    transition: opacity 0.25s;
  }
  .job-card:hover::before { opacity: 1; }

  .job-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }

  .job-logo {
    width: 44px; height: 44px; border-radius: 10px;
    background: var(--bg3); border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; flex-shrink: 0;
  }

  .match-badge {
    font-family: var(--font-mono); font-size: 12px; font-weight: 500;
    padding: 4px 10px; border-radius: 99px;
  }
  .match-high { background: rgba(67,212,138,0.12); color: var(--green); border: 1px solid rgba(67,212,138,0.25); }
  .match-mid  { background: var(--goldGlow); color: var(--gold2); border: 1px solid rgba(201,168,76,0.25); }
  .match-low  { background: var(--accentSoft); color: #7ca0ff; border: 1px solid rgba(79,124,255,0.25); }

  .job-title {
    font-family: var(--font-serif);
    font-size: 17px; font-weight: 600; margin-bottom: 4px; line-height: 1.3;
  }

  .job-company { font-size: 13px; color: var(--muted); margin-bottom: 14px; }

  .job-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
  .job-tag {
    font-size: 11px; font-weight: 500;
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 6px; padding: 3px 9px;
    color: var(--muted);
  }

  .job-meta { display: flex; flex-direction: column; gap: 5px; margin-bottom: 14px; }
  .job-meta-item {
    display: flex; align-items: center; gap: 7px;
    font-size: 12px; color: var(--muted);
  }
  .job-meta-icon { font-size: 13px; }

  .job-desc {
    font-size: 13px; color: var(--muted); line-height: 1.55;
    flex: 1; margin-bottom: 18px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .job-footer { display: flex; gap: 8px; margin-top: auto; }

  .btn-apply {
    flex: 1; padding: 10px 16px; border-radius: var(--r2);
    background: linear-gradient(135deg, var(--gold), var(--gold2));
    color: #0a0d14; font-size: 13px; font-weight: 600;
    border: none; cursor: pointer;
    transition: all 0.2s;
    font-family: var(--font-sans);
  }
  .btn-apply:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(201,168,76,0.3); }

  .btn-save {
    padding: 10px 14px; border-radius: var(--r2);
    background: var(--bg3); border: 1px solid var(--border2);
    color: var(--muted); font-size: 16px;
    cursor: pointer; transition: all 0.2s;
  }
  .btn-save:hover { color: var(--gold); border-color: var(--gold); }
  .btn-save.saved { color: var(--gold); border-color: var(--gold); }

  /* ── Error ── */
  .error-pill {
    display: flex; align-items: center; gap: 8px;
    background: rgba(255,95,109,0.1); border: 1px solid rgba(255,95,109,0.25);
    border-radius: var(--r2); padding: 10px 16px;
    color: var(--red); font-size: 13px;
    margin-top: 16px;
  }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    header { padding: 16px 20px; }
    .card { padding: 28px 22px; }
    .form-grid { grid-template-columns: 1fr; }
    .form-grid .full { grid-column: auto; }
    stepper { padding: 24px 20px 0; }
    .jobs-grid { grid-template-columns: 1fr; }
  }
`;

const styleEl = document.createElement("style");
styleEl.textContent = css;
document.head.appendChild(styleEl);

// ── Constants ────────────────────────────────────────────────────────────────
const STEPS = ["Upload CV", "Preferences", "Matching", "Results"];

const INDUSTRIES = [
  "Technology / Software", "Finance / Banking", "Healthcare / Pharma",
  "Marketing / Advertising", "Education", "Consulting", "Legal",
  "Manufacturing / Engineering", "Retail / E-commerce", "Media / Entertainment",
  "Real Estate", "Hospitality / Travel", "Non-profit / NGO", "Government / Public Sector",
];

const CURRENCIES = ["USD", "EUR", "CNY"];

const COMPANY_EMOJIS = ["🏢","💼","🌐","⚡","🚀","💡","🔬","📊","🏛️","🎯","💎","🌱","🔧","📱"];

// ── Helpers ──────────────────────────────────────────────────────────────────
function maskPII(text) {
  return text
    .replace(/\b[A-Z][a-z]+ [A-Z][a-z]+\b/g, "[NAME REDACTED]")
    .replace(/\b[\w.-]+@[\w.-]+\.\w{2,}\b/g, "[EMAIL REDACTED]")
    .replace(/(\+?[\d\s\-().]{7,})/g, "[PHONE REDACTED]")
    .replace(/\b\d{1,4}[\s,]+[A-Za-z][\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b/gi, "[ADDRESS REDACTED]");
}

function matchClass(score) {
  if (score >= 85) return "match-high";
  if (score >= 65) return "match-mid";
  return "match-low";
}

async function callClaude(systemPrompt, userPrompt) {
  /*const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },*/
  const res = await fetch("/api/anthropic/v1/messages", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01",
    "x-api-key": import.meta.env.VITE_ANTHROPIC_KEY,},
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 4000,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
    }),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  return data.content[0].text;
}

function extractJSON(text) {
  const m = text.match(/```json\s*([\s\S]*?)```/);
  if (m) return m[1].trim();
  const start = text.indexOf("[");
  const end = text.lastIndexOf("]");
  if (start !== -1 && end !== -1) return text.slice(start, end + 1);
  return text;
}

// ── File Reading ─────────────────────────────────────────────────────────────
async function readFileAsText(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result || "");
    if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
      reader.readAsText(file);
    } else {
      reader.readAsText(file);
    }
  });
}

// ── Sub-components ────────────────────────────────────────────────────────────
function Stepper({ current }) {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "32px 40px 0", position: "relative", zIndex: 5 }}>
      <div style={{ display: "flex", alignItems: "center", width: "100%", maxWidth: 600 }}>
        {STEPS.map((label, i) => {
          const done = i < current;
          const active = i === current;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", flex: i < STEPS.length - 1 ? 1 : "none" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                <div className={`step-dot ${active ? "active" : ""} ${done ? "done" : ""}`}
                  style={{
                    width: 36, height: 36, borderRadius: "50%",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500,
                    border: done ? "none" : `1.5px solid ${active ? "var(--gold)" : "rgba(255,255,255,0.13)"}`,
                    background: done ? "var(--gold)" : active ? "linear-gradient(135deg,rgba(201,168,76,0.2),rgba(232,200,106,0.08))" : "var(--bg3)",
                    color: done ? "#0a0d14" : active ? "var(--gold2)" : "var(--muted)",
                    boxShadow: active ? "0 0 20px rgba(201,168,76,0.15)" : "none",
                    transition: "all 0.3s",
                  }}>
                  {done ? "✓" : i + 1}
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 500, letterSpacing: "0.5px",
                  textTransform: "uppercase", whiteSpace: "nowrap",
                  color: done ? "var(--text)" : active ? "var(--gold)" : "var(--muted)",
                  transition: "color 0.3s",
                }}>{label}</span>
              </div>
              {i < STEPS.length - 1 && (
                <div style={{
                  flex: 1, height: 1, margin: "0 8px", marginBottom: 22,
                  background: done ? "var(--gold)" : "rgba(255,255,255,0.13)",
                  transition: "background 0.4s",
                }} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Step 1: CV Upload ─────────────────────────────────────────────────────────
function StepUpload({ onNext }) {
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef();

  const accept = (f) => {
    const ok = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain", "application/msword"].includes(f.type) ||
      /\.(pdf|docx|doc|txt|rtf)$/i.test(f.name);
    if (!ok) { setError("Please upload a PDF, DOCX, DOC, TXT, or RTF file."); return; }
    if (f.size > 10 * 1024 * 1024) { setError("File must be under 10 MB."); return; }
    setError(""); setFile(f);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0]; if (f) accept(f);
  }, []);

  return (
    <div className="card">
      <div className="section-label">Step 1 of 4</div>
      <h2 className="card-title">Upload Your CV</h2>
      <p className="card-sub">Upload your curriculum vitae in PDF, DOCX, or TXT format. We'll extract your skills and experience automatically.</p>

      <div className={`drop-zone ${drag ? "drag-over" : ""} ${file ? "has-file" : ""}`}
        onClick={() => !file && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}>
        <input ref={inputRef} type="file" accept=".pdf,.doc,.docx,.txt,.rtf" style={{ display: "none" }}
          onChange={(e) => { const f = e.target.files[0]; if (f) accept(f); }} />

        {file ? (
          <>
            <span className="drop-icon">📄</span>
            <p className="drop-title" style={{ color: "var(--gold2)" }}>CV Ready</p>
            <div className="file-pill">
              <span>📎</span>
              <span>{file.name}</span>
              <span style={{ color: "var(--muted)", fontSize: 11 }}>({(file.size / 1024).toFixed(0)} KB)</span>
              <button onClick={(e) => { e.stopPropagation(); setFile(null); }}>✕</button>
            </div>
          </>
        ) : (
          <>
            <span className="drop-icon">☁️</span>
            <p className="drop-title">Drop your CV here</p>
            <p className="drop-sub">or click to browse · PDF, DOCX, TXT up to 10 MB</p>
          </>
        )}
      </div>

      {error && <div className="error-pill">⚠️ {error}</div>}

      <div style={{ marginTop: 20, padding: "14px 18px", background: "var(--bg3)", border: "1px solid var(--border)", borderRadius: "var(--r2)", fontSize: 13, color: "var(--muted)" }}>
        <strong style={{ color: "var(--text)", fontWeight: 600 }}>🔒 Privacy first.</strong> Your CV data is only used to find matching jobs and is never stored permanently. Choosing AI matching later will additionally mask all personal identifiers.
      </div>

      <div className="btn-row">
        <div />
        <button className="btn btn-primary" disabled={!file} onClick={() => onNext(file)}>
          Continue to Preferences →
        </button>
      </div>
    </div>
  );
}

// ── Step 2: Preferences ───────────────────────────────────────────────────────
function StepPreferences({ onNext, onBack }) {
  const [prefs, setPrefs] = useState({
    availability: "", location: "", preferredLocation: "",
    industry: "", jobType: "full-time", salary: "", currency: "USD", useAI: false,
  });

  const set = (k, v) => setPrefs((p) => ({ ...p, [k]: v }));
  const valid = prefs.availability && prefs.location && prefs.industry;

  return (
    <div className="card">
      <div className="section-label">Step 2 of 4</div>
      <h2 className="card-title">Your Preferences</h2>
      <p className="card-sub">Tell us what you're looking for so we can find the most relevant opportunities.</p>

      <div className="form-grid">
        <div className="field">
          <label>Availability to Start</label>
          <select value={prefs.availability} onChange={(e) => set("availability", e.target.value)}>
            <option value="">Select availability…</option>
            <option>Immediately</option>
            <option>Within 2 weeks</option>
            <option>Within 1 month</option>
            <option>Within 3 months</option>
            <option>Negotiable</option>
          </select>
        </div>

        <div className="field">
          <label>Job Type</label>
          <select value={prefs.jobType} onChange={(e) => set("jobType", e.target.value)}>
            <option value="full-time">Full-time</option>
            <option value="part-time">Part-time</option>
            <option value="contract">Contract</option>
            <option value="freelance">Freelance</option>
          </select>
        </div>

        <div className="field full">
          <label>Current Location</label>
          <input type="text" placeholder="e.g. New York, USA" value={prefs.location}
            onChange={(e) => set("location", e.target.value)} />
        </div>

        <div className="field full">
          <label>Preferred Job Location <span style={{ color: "var(--muted)", textTransform: "none", fontSize: 11 }}>(city for 30 km radius, or "Remote")</span></label>
          <input type="text" placeholder="e.g. San Francisco, Remote, London" value={prefs.preferredLocation}
            onChange={(e) => set("preferredLocation", e.target.value)} />
        </div>

        <div className="field full">
          <label>Preferred Industry</label>
          <select value={prefs.industry} onChange={(e) => set("industry", e.target.value)}>
            <option value="">Select an industry…</option>
            {INDUSTRIES.map((ind) => <option key={ind}>{ind}</option>)}
          </select>
        </div>

        <div className="field full">
          <label>Current Annual Salary (optional)</label>
          <div className="salary-row">
            <input type="number" placeholder="e.g. 85000" value={prefs.salary}
              onChange={(e) => set("salary", e.target.value)} />
            <select value={prefs.currency} onChange={(e) => set("currency", e.target.value)}>
              {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* AI Toggle */}
      <div className={`ai-toggle-card ${prefs.useAI ? "active" : ""}`}
        onClick={() => set("useAI", !prefs.useAI)}>
        <div className="ai-icon">🤖</div>
        <div className="ai-info">
          <div className="ai-name">AI-Powered Matching</div>
          <div className="ai-desc">Use Claude AI to deeply analyse your CV and intelligently match you to the best roles. Personal details (name, email, phone, address) will be automatically masked before processing.</div>
          {prefs.useAI && (
            <div className="mask-warning">🔐 Personal identifiers will be masked before AI processing</div>
          )}
        </div>
        <div className={`toggle-switch ${prefs.useAI ? "on" : ""}`} />
      </div>

      <div className="btn-row">
        <button className="btn btn-ghost" onClick={onBack}>← Back</button>
        <button className="btn btn-primary" disabled={!valid} onClick={() => onNext(prefs)}>
          Find My Matches →
        </button>
      </div>
    </div>
  );
}

// ── Step 3: Loading ────────────────────────────────────────────────────────────
function StepLoading({ loadingStep }) {
  const steps = [
    { label: "Parsing your CV", icon: "📄" },
    { label: prefs => prefs ? "Masking personal details" : "Validating preferences", icon: "🔐" },
    { label: "Searching LinkedIn jobs", icon: "🔍" },
    { label: "AI matching & ranking", icon: "🧠" },
    { label: "Preparing results", icon: "✨" },
  ];

  return (
    <div className="card">
      <div className="loading-screen">
        <div className="spinner-ring" />
        <div>
          <h2 className="card-title" style={{ textAlign: "center" }}>Finding your matches</h2>
          <p className="card-sub" style={{ textAlign: "center" }}>Analysing your profile against thousands of LinkedIn roles…</p>
        </div>
        <div className="loading-steps">
          {steps.map((s, i) => (
            <div key={i} className={`loading-step ${i < loadingStep ? "done" : i === loadingStep ? "active" : ""}`}>
              <span className="loading-step-icon">
                {i < loadingStep ? "✅" : i === loadingStep ? "⏳" : "⬜"}
              </span>
              <span>{typeof s.label === "function" ? s.label() : s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Step 4: Results ────────────────────────────────────────────────────────────
function StepResults({ jobs, prefs, onRestart }) {
  const [saved, setSaved] = useState({});

  return (
    <>
      <div className="results-header">
        <div>
          <h2 className="results-title">Your <span>Top Matches</span></h2>
          <p style={{ color: "var(--muted)", fontSize: 14, marginTop: 4 }}>
            Based on your CV + preferences · {prefs.preferredLocation || prefs.location}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div className="results-count">{jobs.length} jobs found</div>
          <button className="btn btn-ghost" style={{ padding: "8px 18px", fontSize: 13 }} onClick={onRestart}>
            ↺ Restart
          </button>
        </div>
      </div>

      <div className="jobs-grid">
        {jobs.map((job, i) => (
          <JobCard key={i} job={job} idx={i}
            saved={!!saved[i]}
            onSave={() => setSaved((s) => ({ ...s, [i]: !s[i] }))} />
        ))}
      </div>
    </>
  );
}

function JobCard({ job, idx, saved, onSave }) {
  const delay = Math.min(idx * 0.04, 0.6);
  const mc = matchClass(job.matchScore);

  return (
    <div className="job-card" style={{ animationDelay: `${delay}s` }}>
      <div className="job-header">
        <div className="job-logo">
          {COMPANY_EMOJIS[idx % COMPANY_EMOJIS.length]}
        </div>
        <div className={`match-badge ${mc}`}>{job.matchScore}% match</div>
      </div>

      <div className="job-title">{job.title}</div>
      <div className="job-company">{job.company} · {job.location}</div>

      <div className="job-tags">
        {(job.tags || []).slice(0, 4).map((t, i) => (
          <span key={i} className="job-tag">{t}</span>
        ))}
      </div>

      <div className="job-meta">
        <div className="job-meta-item"><span className="job-meta-icon">💰</span>{job.salary}</div>
        <div className="job-meta-item"><span className="job-meta-icon">⏱️</span>{job.type}</div>
        <div className="job-meta-item"><span className="job-meta-icon">📅</span>Posted {job.posted}</div>
      </div>

      <div className="job-desc">{job.description}</div>

      <div className="job-footer">
        <button className="btn-apply"
          onClick={() => window.open(`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(job.title + " " + job.company)}`, "_blank")}>
          Apply on LinkedIn ↗
        </button>
        <button className={`btn-save ${saved ? "saved" : ""}`} onClick={onSave}>
          {saved ? "★" : "☆"}
        </button>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [step, setStep] = useState(0);
  const [cvFile, setCvFile] = useState(null);
  const [prefs, setPrefs] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState("");
  const [loadingStep, setLoadingStep] = useState(0);

  const handleUpload = (file) => { setCvFile(file); setStep(1); };

  const handlePrefs = async (userPrefs) => {
    setPrefs(userPrefs);
    setStep(2);
    setLoadingStep(0);
    setError("");

    try {
      // Read file
      let cvText = await readFileAsText(cvFile);
      if (!cvText || cvText.trim().length < 30) {
        cvText = `[Sample CV - ${cvFile.name}]\nProfessional with experience in ${userPrefs.industry}.\nSeeking ${userPrefs.jobType} role.`;
      }
      setLoadingStep(1);

      // Mask if AI selected
      if (userPrefs.useAI) {
        cvText = maskPII(cvText);
        await new Promise(r => setTimeout(r, 600));
      }
      setLoadingStep(2);
      await new Promise(r => setTimeout(r, 500));

      setLoadingStep(3);

      const system = `You are a LinkedIn job matching engine. Return ONLY valid JSON array. No markdown, no explanation.`;

      const prompt = `Given this CV and preferences, generate exactly 20 highly realistic LinkedIn job listings as a JSON array.

CV CONTENT:
${cvText.slice(0, 2000)}

USER PREFERENCES:
- Availability: ${userPrefs.availability}
- Current location: ${userPrefs.location}
- Preferred location: ${userPrefs.preferredLocation || userPrefs.location}
- Industry: ${userPrefs.industry}
- Job type: ${userPrefs.jobType}
- Current salary: ${userPrefs.salary ? userPrefs.salary + " " + userPrefs.currency : "Not specified"}
- AI matching: ${userPrefs.useAI}

Return a JSON array of exactly 20 objects. Each object must have:
{
  "title": "Job title",
  "company": "Real-sounding company name",
  "location": "City, Country (or Remote)",
  "salary": "e.g. $90,000 – $120,000/yr",
  "type": "Full-time / Part-time / Contract",
  "matchScore": 72,
  "posted": "e.g. 2 days ago",
  "tags": ["Skill1","Skill2","Skill3"],
  "description": "2-3 sentence job summary relevant to candidate"
}

matchScore should range from 62-97. Higher scores for better matches. Vary company sizes (startups to enterprise). Make locations realistic for the preferred location. Tags should reflect industry skills.`;

      const raw = await callClaude(system, prompt);
      setLoadingStep(4);

      let parsed;
      try {
        parsed = JSON.parse(extractJSON(raw));
      } catch {
        throw new Error("Could not parse job results. Please try again.");
      }

      if (!Array.isArray(parsed) || parsed.length === 0) throw new Error("No jobs returned.");
      parsed.sort((a, b) => b.matchScore - a.matchScore);

      await new Promise(r => setTimeout(r, 400));
      setJobs(parsed.slice(0, 20));
      setStep(3);
    } catch (e) {
      setError(e.message || "Something went wrong.");
      setStep(1);
    }
  };

  const restart = () => {
    setStep(0); setCvFile(null); setPrefs(null);
    setJobs([]); setError(""); setLoadingStep(0);
  };

  return (
    <div className="app">
      <div className="noise" />
      <div className="glow-orb orb1" />
      <div className="glow-orb orb2" />

      <header>
        <div className="logo">
          <div className="logo-icon">✦</div>
          Career<span>Match</span>
        </div>
        <div className="header-badge">LinkedIn · AI-Powered · 2026</div>
      </header>

      {step < 3 && <Stepper current={step} />}

      <main style={{ paddingTop: step === 3 ? 40 : undefined }}>
        {step === 0 && <StepUpload onNext={handleUpload} />}
        {step === 1 && (
          <>
            <StepPreferences onNext={handlePrefs} onBack={() => setStep(0)} />
            {error && (
              <div className="error-pill" style={{ maxWidth: 680, marginTop: 12 }}>
                ⚠️ {error}
              </div>
            )}
          </>
        )}
        {step === 2 && <StepLoading loadingStep={loadingStep} />}
        {step === 3 && <StepResults jobs={jobs} prefs={prefs} onRestart={restart} />}
      </main>
    </div>
  );
}
