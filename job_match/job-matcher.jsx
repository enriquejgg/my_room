/**
 * job-matcher.jsx
 * ─────────────────────────────────────────────────────────────────────────────
 * CareerMatch — AI-Powered Job Matching Application with Multi-Language Support
 *
 * SUPPORTED LANGUAGES (6):
 *   en  English   (LTR)
 *   es  Spanish   (LTR)
 *   fr  French    (LTR)
 *   de  German    (LTR)
 *   zh  Chinese   (LTR)
 *   ar  Arabic    (RTL — full right-to-left layout via dir="rtl" on <html>)
 *
 * i18n ARCHITECTURE:
 *   • All UI strings live in the TRANSLATIONS constant (Section 3).
 *   • The root App component holds `lang` state and derives a `t()` lookup
 *     function that returns strings for the active language.
 *   • `t` is passed as a prop to every sub-component.
 *   • Arabic switches the document direction to RTL automatically.
 *   • Languages that need special fonts (Arabic, Chinese) are loaded via
 *     separate Google Fonts <link> tags (Section 1).
 *
 * FILE STRUCTURE:
 *   1.  Font injection (Latin + Arabic + CJK)
 *   2.  CSS (design tokens, layout, components, RTL overrides)
 *   3.  TRANSLATIONS constant — all UI strings in all 6 languages
 *   4.  App-level constants (industries per language, currencies, emojis)
 *   5.  Helper utilities (maskPII, matchClass, callClaude, extractJSON)
 *   6.  File reader utility
 *   7.  Sub-components (Stepper, StepUpload, StepPreferences, StepLoading,
 *                        StepResults, JobCard, LanguageSelector)
 *   8.  Root App component
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { useState, useRef, useCallback } from "react";

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 1 — FONT INJECTION
// Three separate <link> tags are appended to <head>:
//   1. Latin fonts  — Playfair Display (serif) + DM Sans (sans) + DM Mono
//   2. Arabic font  — Noto Sans Arabic (covers Arabic script)
//   3. CJK font     — Noto Sans SC (covers Simplified Chinese)
// All three are always loaded; the active font is selected via CSS on the
// [lang="ar"] and [lang="zh"] selectors defined in Section 2.
// ─────────────────────────────────────────────────────────────────────────────
[
  "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap",
  "https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;500;600;700&display=swap",
  "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap",
].forEach((href) => {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = href;
  document.head.appendChild(link);
});

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 2 — CSS
// ─────────────────────────────────────────────────────────────────────────────
const css = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:         #0a0d14;
    --bg2:        #111520;
    --bg3:        #181d2e;
    --surface:    #1c2236;
    --border:     rgba(255,255,255,0.07);
    --border2:    rgba(255,255,255,0.13);
    --gold:       #c9a84c;
    --gold2:      #e8c86a;
    --goldGlow:   rgba(201,168,76,0.15);
    --text:       #e8eaf0;
    --muted:      #8890a8;
    --accent:     #4f7cff;
    --accentSoft: rgba(79,124,255,0.12);
    --red:        #ff5f6d;
    --green:      #43d48a;
    --r:          12px;
    --r2:         8px;
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

  /* ── Language-specific font overrides ── */
  /* Arabic: Noto Sans Arabic replaces all font stacks */
  [lang="ar"] body,
  [lang="ar"] input,
  [lang="ar"] select,
  [lang="ar"] button,
  [lang="ar"] .card-title,
  [lang="ar"] .job-title {
    font-family: 'Noto Sans Arabic', system-ui, sans-serif !important;
    letter-spacing: 0 !important; /* Arabic doesn't use Latin letter-spacing */
  }

  /* Chinese: Noto Sans SC replaces sans-serif stacks; serif stays for headings */
  [lang="zh"] body,
  [lang="zh"] input,
  [lang="zh"] select,
  [lang="zh"] button {
    font-family: 'Noto Sans SC', system-ui, sans-serif !important;
  }
  [lang="zh"] .card-title,
  [lang="zh"] .job-title {
    font-family: 'Noto Sans SC', serif !important;
  }

  /* ── RTL layout adjustments ── */
  /* In RTL mode the browser mirrors most flexbox and text alignment automatically.
     These rules handle the exceptions that need explicit overrides. */
  [dir="rtl"] .logo       { flex-direction: row-reverse; }
  [dir="rtl"] .header-right { flex-direction: row-reverse; }
  [dir="rtl"] .btn-row    { flex-direction: row-reverse; }
  [dir="rtl"] .salary-row { direction: rtl; }
  [dir="rtl"] .job-header { flex-direction: row-reverse; }
  [dir="rtl"] .job-meta-item { flex-direction: row-reverse; }
  [dir="rtl"] .job-tags   { flex-direction: row-reverse; }
  [dir="rtl"] .job-footer { flex-direction: row-reverse; }
  [dir="rtl"] .ai-toggle-card { flex-direction: row-reverse; }
  [dir="rtl"] .section-label { flex-direction: row-reverse; }
  [dir="rtl"] .section-label::after { margin-right: 8px; margin-left: 0; }
  [dir="rtl"] .loading-step { flex-direction: row-reverse; }
  [dir="rtl"] .results-header { flex-direction: row-reverse; }
  [dir="rtl"] .lang-flag  { margin-right: 0; margin-left: 6px; }
  [dir="rtl"] select {
    background-position: left 14px center;
    padding-right: 14px;
    padding-left: 36px;
  }

  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--surface); border-radius: 99px; }

  .app { min-height: 100vh; display: flex; flex-direction: column; position: relative; overflow-x: hidden; }

  .noise { position: fixed; inset: 0; z-index: 0; pointer-events: none; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E"); opacity: 0.4; }
  .glow-orb { position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; filter: blur(120px); }
  .orb1 { width: 600px; height: 600px; top: -200px; left: -150px; background: radial-gradient(circle, rgba(201,168,76,0.08) 0%, transparent 70%); }
  .orb2 { width: 500px; height: 500px; bottom: -100px; right: -100px; background: radial-gradient(circle, rgba(79,124,255,0.07) 0%, transparent 70%); }

  /* ── Header ── */
  header {
    position: relative; z-index: 10;
    padding: 16px 40px;
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid var(--border);
    background: rgba(10,13,20,0.8);
    backdrop-filter: blur(20px);
    gap: 16px;
  }

  .logo { display: flex; align-items: center; gap: 10px; font-family: var(--font-serif); font-size: 22px; font-weight: 700; color: var(--text); letter-spacing: -0.3px; flex-shrink: 0; }
  .logo-icon { width: 34px; height: 34px; background: linear-gradient(135deg, var(--gold), var(--gold2)); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
  .logo span { color: var(--gold); }
  .header-right { display: flex; align-items: center; gap: 10px; }
  .header-badge { font-family: var(--font-mono); font-size: 11px; font-weight: 500; color: var(--muted); background: var(--surface); border: 1px solid var(--border2); padding: 5px 12px; border-radius: 99px; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap; }

  /* ── Language Selector ── */
  .lang-selector {
    position: relative;
  }

  .lang-btn {
    display: flex; align-items: center; gap: 6px;
    background: var(--surface); border: 1px solid var(--border2);
    border-radius: 99px; padding: 6px 14px;
    color: var(--text); font-family: var(--font-sans);
    font-size: 13px; font-weight: 500;
    cursor: pointer; outline: none;
    transition: all 0.2s; white-space: nowrap;
  }
  .lang-btn:hover { border-color: var(--gold); color: var(--gold2); }

  .lang-flag { font-size: 16px; }

  /* Dropdown panel */
  .lang-dropdown {
    position: absolute; top: calc(100% + 8px); right: 0;
    background: var(--bg2); border: 1px solid var(--border2);
    border-radius: var(--r); overflow: hidden;
    min-width: 170px;
    box-shadow: 0 16px 48px rgba(0,0,0,0.5);
    z-index: 100;
    animation: slideUp 0.18s ease both;
  }
  [dir="rtl"] .lang-dropdown { right: auto; left: 0; }

  .lang-option {
    display: flex; align-items: center; gap: 10px;
    padding: 11px 16px;
    cursor: pointer;
    font-size: 13px; font-weight: 500;
    color: var(--muted);
    transition: all 0.15s;
    border: none; background: none; width: 100%; text-align: start;
  }
  .lang-option:hover  { background: var(--surface); color: var(--text); }
  .lang-option.active { background: var(--goldGlow); color: var(--gold2); }
  .lang-option-flag   { font-size: 18px; }
  .lang-option-label  { flex: 1; }
  .lang-option-native { font-size: 11px; color: var(--muted); }

  /* ── Stepper dots ── */
  .step-dot { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 13px; font-weight: 500; border: 1.5px solid var(--border2); background: var(--bg3); color: var(--muted); transition: all 0.3s; }
  .step-dot.active { border-color: var(--gold); background: linear-gradient(135deg, rgba(201,168,76,0.2), rgba(232,200,106,0.08)); color: var(--gold2); box-shadow: 0 0 20px var(--goldGlow); }
  .step-dot.done   { border-color: var(--gold); background: var(--gold); color: #0a0d14; }

  /* ── Card ── */
  .card { background: var(--surface); border: 1px solid var(--border2); border-radius: var(--r); padding: 40px; width: 100%; max-width: 680px; box-shadow: 0 24px 80px rgba(0,0,0,0.4); animation: slideUp 0.4s ease both; }
  @keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
  .card-title { font-family: var(--font-serif); font-size: 28px; font-weight: 700; color: var(--text); margin-bottom: 6px; line-height: 1.2; }
  .card-sub   { color: var(--muted); font-size: 14px; margin-bottom: 32px; }
  .section-label { font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--gold); margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
  .section-label::after { content: ''; flex: 1; height: 1px; background: var(--border2); }

  /* ── Drop zone ── */
  .drop-zone { border: 2px dashed var(--border2); border-radius: var(--r); padding: 48px 32px; text-align: center; cursor: pointer; transition: all 0.25s; }
  .drop-zone:hover, .drop-zone.drag-over { border-color: var(--gold); background: var(--goldGlow); }
  .drop-zone.has-file { border-style: solid; border-color: var(--gold); background: var(--goldGlow); }
  .drop-icon  { font-size: 42px; margin-bottom: 14px; display: block; }
  .drop-title { font-family: var(--font-serif); font-size: 18px; font-weight: 600; margin-bottom: 8px; }
  .drop-sub   { color: var(--muted); font-size: 13px; }
  .file-pill  { display: inline-flex; align-items: center; gap: 8px; background: var(--bg3); border: 1px solid var(--gold); border-radius: 99px; padding: 8px 16px; margin-top: 16px; font-size: 13px; font-family: var(--font-mono); color: var(--gold2); }
  .file-pill button { background: none; border: none; cursor: pointer; color: var(--muted); font-size: 16px; line-height: 1; padding: 0 0 0 4px; transition: color 0.2s; }
  .file-pill button:hover { color: var(--red); }

  /* ── Form ── */
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  .form-grid .full { grid-column: 1 / -1; }
  .field { display: flex; flex-direction: column; gap: 6px; }
  label { font-size: 12px; font-weight: 600; letter-spacing: 0.4px; text-transform: uppercase; color: var(--muted); }
  input[type="text"], input[type="number"], select, textarea { background: var(--bg3); border: 1px solid var(--border2); border-radius: var(--r2); color: var(--text); font-family: var(--font-sans); font-size: 14px; padding: 11px 14px; outline: none; transition: border-color 0.2s, box-shadow 0.2s; width: 100%; appearance: none; }
  select { cursor: pointer; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238890a8' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 14px center; padding-right: 36px; }
  input:focus, select:focus, textarea:focus { border-color: var(--gold); box-shadow: 0 0 0 3px var(--goldGlow); }
  select option { background: var(--bg3); }
  .salary-row { display: grid; grid-template-columns: 1fr auto; gap: 8px; }
  .salary-row select { width: 90px; }

  /* ── AI Toggle ── */
  .ai-toggle-card { background: var(--bg3); border: 1px solid var(--border2); border-radius: var(--r); padding: 20px 22px; display: flex; align-items: flex-start; gap: 16px; cursor: pointer; transition: all 0.25s; margin-top: 24px; }
  .ai-toggle-card:hover  { border-color: var(--accent); background: var(--accentSoft); }
  .ai-toggle-card.active { border-color: var(--accent); background: var(--accentSoft); box-shadow: 0 0 30px rgba(79,124,255,0.1); }
  .ai-icon { width: 42px; height: 42px; border-radius: 10px; background: linear-gradient(135deg, #4f7cff, #7b5ea7); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
  .ai-info { flex: 1; }
  .ai-name { font-weight: 600; margin-bottom: 4px; font-size: 15px; }
  .ai-desc { font-size: 13px; color: var(--muted); line-height: 1.5; }
  .toggle-switch { width: 46px; height: 26px; background: var(--border2); border-radius: 99px; position: relative; flex-shrink: 0; transition: background 0.25s; margin-top: 2px; }
  .toggle-switch.on { background: var(--accent); }
  .toggle-switch::after { content: ''; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; background: white; border-radius: 50%; transition: transform 0.25s; box-shadow: 0 2px 6px rgba(0,0,0,0.3); }
  .toggle-switch.on::after { transform: translateX(20px); }
  [dir="rtl"] .toggle-switch::after { left: auto; right: 3px; }
  [dir="rtl"] .toggle-switch.on::after { transform: translateX(-20px); }
  .mask-warning { font-size: 12px; color: #4f7cff; margin-top: 8px; display: flex; align-items: center; gap: 5px; }

  /* ── Buttons ── */
  .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 13px 28px; border-radius: var(--r2); font-family: var(--font-sans); font-size: 14px; font-weight: 600; cursor: pointer; border: none; outline: none; transition: all 0.2s; letter-spacing: 0.2px; }
  .btn-primary { background: linear-gradient(135deg, var(--gold), var(--gold2)); color: #0a0d14; }
  .btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 30px rgba(201,168,76,0.35); }
  .btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-ghost { background: transparent; color: var(--muted); border: 1px solid var(--border2); }
  .btn-ghost:hover { color: var(--text); }
  .btn-row { display: flex; justify-content: space-between; align-items: center; margin-top: 32px; gap: 12px; }

  /* ── Loading ── */
  .loading-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 24px; padding: 80px 40px; text-align: center; }
  .spinner-ring { width: 72px; height: 72px; border: 3px solid var(--border2); border-top-color: var(--gold); border-radius: 50%; animation: spin 0.9s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-steps { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
  .loading-step { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); transition: color 0.3s; }
  .loading-step.done   { color: var(--green); }
  .loading-step.active { color: var(--text);  }
  .loading-step-icon   { font-size: 16px; width: 20px; text-align: center; }

  /* ── Results ── */
  .results-header { width: 100%; max-width: 1100px; margin-bottom: 28px; display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; animation: slideUp 0.4s ease both; }
  .results-title { font-family: var(--font-serif); font-size: 32px; font-weight: 700; }
  .results-title span { color: var(--gold); }
  .results-count { font-family: var(--font-mono); font-size: 13px; color: var(--muted); background: var(--surface); border: 1px solid var(--border2); padding: 6px 14px; border-radius: 99px; white-space: nowrap; }
  .jobs-grid { width: 100%; max-width: 1100px; display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 18px; }

  /* ── Job card ── */
  .job-card { background: var(--surface); border: 1px solid var(--border2); border-radius: var(--r); padding: 24px; transition: all 0.25s; position: relative; overflow: hidden; animation: slideUp 0.4s ease both; display: flex; flex-direction: column; }
  .job-card:hover { border-color: rgba(201,168,76,0.4); transform: translateY(-2px); box-shadow: 0 16px 50px rgba(0,0,0,0.35); }
  .job-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, var(--gold), transparent); opacity: 0; transition: opacity 0.25s; }
  .job-card:hover::before { opacity: 1; }
  .job-header   { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
  .job-logo     { width: 44px; height: 44px; border-radius: 10px; background: var(--bg3); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
  .match-badge  { font-family: var(--font-mono); font-size: 12px; font-weight: 500; padding: 4px 10px; border-radius: 99px; }
  .match-high   { background: rgba(67,212,138,0.12); color: var(--green); border: 1px solid rgba(67,212,138,0.25); }
  .match-mid    { background: var(--goldGlow);        color: var(--gold2);  border: 1px solid rgba(201,168,76,0.25); }
  .match-low    { background: var(--accentSoft);      color: #7ca0ff;       border: 1px solid rgba(79,124,255,0.25); }
  .job-title    { font-family: var(--font-serif); font-size: 17px; font-weight: 600; margin-bottom: 4px; line-height: 1.3; }
  .job-company  { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
  .job-tags     { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
  .job-tag      { font-size: 11px; font-weight: 500; background: var(--bg3); border: 1px solid var(--border); border-radius: 6px; padding: 3px 9px; color: var(--muted); }
  .job-meta     { display: flex; flex-direction: column; gap: 5px; margin-bottom: 14px; }
  .job-meta-item { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--muted); }
  .job-meta-icon { font-size: 13px; }
  .job-desc     { font-size: 13px; color: var(--muted); line-height: 1.55; flex: 1; margin-bottom: 18px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .job-footer   { display: flex; gap: 8px; margin-top: auto; }
  .btn-apply    { flex: 1; padding: 10px 16px; border-radius: var(--r2); background: linear-gradient(135deg, var(--gold), var(--gold2)); color: #0a0d14; font-size: 13px; font-weight: 600; border: none; cursor: pointer; transition: all 0.2s; font-family: var(--font-sans); }
  .btn-apply:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(201,168,76,0.3); }
  .btn-save     { padding: 10px 14px; border-radius: var(--r2); background: var(--bg3); border: 1px solid var(--border2); color: var(--muted); font-size: 16px; cursor: pointer; transition: all 0.2s; }
  .btn-save:hover, .btn-save.saved { color: var(--gold); border-color: var(--gold); }

  .error-pill { display: flex; align-items: center; gap: 8px; background: rgba(255,95,109,0.1); border: 1px solid rgba(255,95,109,0.25); border-radius: var(--r2); padding: 10px 16px; color: var(--red); font-size: 13px; margin-top: 16px; }

  @media (max-width: 640px) {
    header { padding: 12px 16px; }
    .card  { padding: 28px 22px; }
    .form-grid { grid-template-columns: 1fr; }
    .form-grid .full { grid-column: auto; }
    .jobs-grid { grid-template-columns: 1fr; }
    .header-badge { display: none; }
  }
`;
const styleEl = document.createElement("style");
styleEl.textContent = css;
document.head.appendChild(styleEl);

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 3 — TRANSLATIONS
// Every visible UI string is defined here for each of the 6 supported locales.
// Access pattern: TRANSLATIONS[langCode].keyName
//
// Keys that contain {placeholders} are interpolated at render time by the
// t() function in the App component.
// ─────────────────────────────────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    // Header
    headerBadge: "LinkedIn · AI-Powered · 2026",
    // Step labels
    stepUpload: "Upload CV",
    stepPreferences: "Preferences",
    stepMatching: "Matching",
    stepResults: "Results",
    // Step 0 — Upload
    step1of4: "Step 1 of 4",
    uploadTitle: "Upload Your CV",
    uploadSub: "Upload your curriculum vitae in PDF, DOCX, or TXT format. We'll extract your skills and experience automatically.",
    dropHere: "Drop your CV here",
    dropOr: "or click to browse · PDF, DOCX, TXT up to 10 MB",
    cvReady: "CV Ready",
    privacyNote: "🔒 Privacy first. Your CV data is only used to find matching jobs and is never stored permanently. Choosing AI matching later will additionally mask all personal identifiers.",
    continueBtn: "Continue to Preferences →",
    errInvalidType: "Please upload a PDF, DOCX, DOC, TXT, or RTF file.",
    errTooLarge: "File must be under 10 MB.",
    // Step 1 — Preferences
    step2of4: "Step 2 of 4",
    prefsTitle: "Your Preferences",
    prefsSub: "Tell us what you're looking for so we can find the most relevant opportunities.",
    labelAvailability: "Availability to Start",
    labelJobType: "Job Type",
    labelLocation: "Current Location",
    labelPrefLocation: "Preferred Job Location",
    prefLocationHint: "(city for 30 km radius, or \"Remote\")",
    labelIndustry: "Preferred Industry",
    labelSalary: "Current Annual Salary (optional)",
    placeholderAvailability: "Select availability…",
    placeholderLocation: "e.g. New York, USA",
    placeholderPrefLocation: "e.g. San Francisco, Remote, London",
    placeholderSalary: "e.g. 85000",
    optImmediately: "Immediately",
    opt2Weeks: "Within 2 weeks",
    opt1Month: "Within 1 month",
    opt3Months: "Within 3 months",
    optNegotiable: "Negotiable",
    optFullTime: "Full-time",
    optPartTime: "Part-time",
    optContract: "Contract",
    optFreelance: "Freelance",
    placeholderIndustry: "Select an industry…",
    aiName: "AI-Powered Matching",
    aiDesc: "Use Claude AI to deeply analyse your CV and intelligently match you to the best roles. Personal details (name, email, phone, address) will be automatically masked before processing.",
    aiMaskWarning: "🔐 Personal identifiers will be masked before AI processing",
    backBtn: "← Back",
    findMatchesBtn: "Find My Matches →",
    // Step 2 — Loading
    loadingTitle: "Finding your matches",
    loadingSub: "Analysing your profile against thousands of LinkedIn roles…",
    loadingStage0: "Parsing your CV",
    loadingStage1: "Masking personal details",
    loadingStage2: "Searching LinkedIn jobs",
    loadingStage3: "AI matching & ranking",
    loadingStage4: "Preparing results",
    // Step 3 — Results
    resultsTitle: "Your",
    resultsHighlight: "Top Matches",
    resultsSub: "Based on your CV + preferences ·",
    jobsFound: "{n} jobs found",
    restartBtn: "↺ Restart",
    applyBtn: "Apply on LinkedIn ↗",
    matchLabel: "{n}% match",
    postedLabel: "Posted {date}",
    // Error
    parseError: "Could not parse job results. Please try again.",
    noJobsError: "No jobs returned from AI. Please try again.",
    genericError: "Something went wrong. Please try again.",
  },

  es: {
    headerBadge: "LinkedIn · IA · 2026",
    stepUpload: "Subir CV",
    stepPreferences: "Preferencias",
    stepMatching: "Búsqueda",
    stepResults: "Resultados",
    step1of4: "Paso 1 de 4",
    uploadTitle: "Sube tu CV",
    uploadSub: "Sube tu currículum en formato PDF, DOCX o TXT. Extraeremos tus habilidades y experiencia automáticamente.",
    dropHere: "Arrastra tu CV aquí",
    dropOr: "o haz clic para buscar · PDF, DOCX, TXT hasta 10 MB",
    cvReady: "CV listo",
    privacyNote: "🔒 Privacidad primero. Tus datos solo se usan para encontrar empleos y nunca se almacenan. El modo IA también enmascarará todos tus datos personales.",
    continueBtn: "Continuar a Preferencias →",
    errInvalidType: "Por favor sube un archivo PDF, DOCX, DOC, TXT o RTF.",
    errTooLarge: "El archivo debe pesar menos de 10 MB.",
    step2of4: "Paso 2 de 4",
    prefsTitle: "Tus Preferencias",
    prefsSub: "Cuéntanos qué buscas para encontrar las oportunidades más relevantes.",
    labelAvailability: "Disponibilidad de Incorporación",
    labelJobType: "Tipo de Empleo",
    labelLocation: "Ubicación Actual",
    labelPrefLocation: "Ubicación Preferida",
    prefLocationHint: "(ciudad para radio de 30 km, o \"Remoto\")",
    labelIndustry: "Industria Preferida",
    labelSalary: "Salario Anual Actual (opcional)",
    placeholderAvailability: "Selecciona disponibilidad…",
    placeholderLocation: "ej. Madrid, España",
    placeholderPrefLocation: "ej. Barcelona, Remoto, Valencia",
    placeholderSalary: "ej. 40000",
    optImmediately: "Inmediatamente",
    opt2Weeks: "En 2 semanas",
    opt1Month: "En 1 mes",
    opt3Months: "En 3 meses",
    optNegotiable: "Negociable",
    optFullTime: "Tiempo completo",
    optPartTime: "Tiempo parcial",
    optContract: "Contrato",
    optFreelance: "Freelance",
    placeholderIndustry: "Selecciona una industria…",
    aiName: "Búsqueda con IA",
    aiDesc: "Usa Claude IA para analizar tu CV en profundidad y encontrar los mejores empleos. Los datos personales (nombre, correo, teléfono, dirección) serán enmascarados automáticamente.",
    aiMaskWarning: "🔐 Los datos personales serán enmascarados antes del procesamiento con IA",
    backBtn: "← Atrás",
    findMatchesBtn: "Buscar mis empleos →",
    loadingTitle: "Buscando tus coincidencias",
    loadingSub: "Analizando tu perfil contra miles de empleos en LinkedIn…",
    loadingStage0: "Analizando tu CV",
    loadingStage1: "Enmascarando datos personales",
    loadingStage2: "Buscando empleos en LinkedIn",
    loadingStage3: "Clasificando con IA",
    loadingStage4: "Preparando resultados",
    resultsTitle: "Tus",
    resultsHighlight: "Mejores Empleos",
    resultsSub: "Basado en tu CV + preferencias ·",
    jobsFound: "{n} empleos encontrados",
    restartBtn: "↺ Reiniciar",
    applyBtn: "Aplicar en LinkedIn ↗",
    matchLabel: "{n}% compatibilidad",
    postedLabel: "Publicado {date}",
    parseError: "No se pudieron analizar los resultados. Inténtalo de nuevo.",
    noJobsError: "La IA no devolvió empleos. Inténtalo de nuevo.",
    genericError: "Algo salió mal. Inténtalo de nuevo.",
  },

  fr: {
    headerBadge: "LinkedIn · IA · 2026",
    stepUpload: "Uploader CV",
    stepPreferences: "Préférences",
    stepMatching: "Recherche",
    stepResults: "Résultats",
    step1of4: "Étape 1 sur 4",
    uploadTitle: "Uploadez votre CV",
    uploadSub: "Uploadez votre CV en format PDF, DOCX ou TXT. Nous extrairons automatiquement vos compétences et expériences.",
    dropHere: "Déposez votre CV ici",
    dropOr: "ou cliquez pour parcourir · PDF, DOCX, TXT jusqu'à 10 Mo",
    cvReady: "CV prêt",
    privacyNote: "🔒 Confidentialité d'abord. Vos données ne sont utilisées que pour trouver des emplois et ne sont jamais stockées. L'option IA masquera également tous vos identifiants personnels.",
    continueBtn: "Continuer vers les Préférences →",
    errInvalidType: "Veuillez uploader un fichier PDF, DOCX, DOC, TXT ou RTF.",
    errTooLarge: "Le fichier doit faire moins de 10 Mo.",
    step2of4: "Étape 2 sur 4",
    prefsTitle: "Vos Préférences",
    prefsSub: "Dites-nous ce que vous cherchez afin de trouver les offres les plus pertinentes.",
    labelAvailability: "Disponibilité",
    labelJobType: "Type de poste",
    labelLocation: "Localisation actuelle",
    labelPrefLocation: "Lieu de travail souhaité",
    prefLocationHint: "(ville pour un rayon de 30 km, ou \"Télétravail\")",
    labelIndustry: "Secteur préféré",
    labelSalary: "Salaire annuel actuel (optionnel)",
    placeholderAvailability: "Sélectionnez votre disponibilité…",
    placeholderLocation: "ex. Paris, France",
    placeholderPrefLocation: "ex. Lyon, Télétravail, Bordeaux",
    placeholderSalary: "ex. 45000",
    optImmediately: "Immédiatement",
    opt2Weeks: "Dans 2 semaines",
    opt1Month: "Dans 1 mois",
    opt3Months: "Dans 3 mois",
    optNegotiable: "Négociable",
    optFullTime: "Temps plein",
    optPartTime: "Temps partiel",
    optContract: "CDD / Freelance",
    optFreelance: "Indépendant",
    placeholderIndustry: "Sélectionnez un secteur…",
    aiName: "Matching par IA",
    aiDesc: "Utilisez Claude IA pour analyser votre CV en profondeur et trouver les meilleures offres. Vos données personnelles (nom, e-mail, téléphone, adresse) seront automatiquement masquées.",
    aiMaskWarning: "🔐 Les données personnelles seront masquées avant le traitement par IA",
    backBtn: "← Retour",
    findMatchesBtn: "Trouver mes offres →",
    loadingTitle: "Recherche de vos offres",
    loadingSub: "Analyse de votre profil sur des milliers d'offres LinkedIn…",
    loadingStage0: "Analyse de votre CV",
    loadingStage1: "Masquage des données personnelles",
    loadingStage2: "Recherche sur LinkedIn",
    loadingStage3: "Classement par IA",
    loadingStage4: "Préparation des résultats",
    resultsTitle: "Vos",
    resultsHighlight: "Meilleures Offres",
    resultsSub: "Basé sur votre CV + préférences ·",
    jobsFound: "{n} offres trouvées",
    restartBtn: "↺ Recommencer",
    applyBtn: "Postuler sur LinkedIn ↗",
    matchLabel: "{n}% de compatibilité",
    postedLabel: "Publié {date}",
    parseError: "Impossible d'analyser les résultats. Veuillez réessayer.",
    noJobsError: "L'IA n'a retourné aucune offre. Veuillez réessayer.",
    genericError: "Une erreur est survenue. Veuillez réessayer.",
  },

  de: {
    headerBadge: "LinkedIn · KI · 2026",
    stepUpload: "CV hochladen",
    stepPreferences: "Präferenzen",
    stepMatching: "Suche",
    stepResults: "Ergebnisse",
    step1of4: "Schritt 1 von 4",
    uploadTitle: "Laden Sie Ihren Lebenslauf hoch",
    uploadSub: "Laden Sie Ihren Lebenslauf im PDF-, DOCX- oder TXT-Format hoch. Wir extrahieren automatisch Ihre Fähigkeiten und Erfahrungen.",
    dropHere: "Lebenslauf hier ablegen",
    dropOr: "oder klicken Sie zum Durchsuchen · PDF, DOCX, TXT bis 10 MB",
    cvReady: "Lebenslauf bereit",
    privacyNote: "🔒 Datenschutz zuerst. Ihre Daten werden nur zur Jobsuche verwendet und nie dauerhaft gespeichert. Die KI-Option maskiert zusätzlich alle persönlichen Daten.",
    continueBtn: "Weiter zu Präferenzen →",
    errInvalidType: "Bitte laden Sie eine PDF-, DOCX-, DOC-, TXT- oder RTF-Datei hoch.",
    errTooLarge: "Die Datei muss kleiner als 10 MB sein.",
    step2of4: "Schritt 2 von 4",
    prefsTitle: "Ihre Präferenzen",
    prefsSub: "Teilen Sie uns mit, wonach Sie suchen, damit wir die relevantesten Stellen finden.",
    labelAvailability: "Verfügbarkeit",
    labelJobType: "Beschäftigungsart",
    labelLocation: "Aktueller Standort",
    labelPrefLocation: "Bevorzugter Arbeitsort",
    prefLocationHint: "(Stadt für 30-km-Radius oder \"Remote\")",
    labelIndustry: "Bevorzugte Branche",
    labelSalary: "Aktuelles Jahresgehalt (optional)",
    placeholderAvailability: "Verfügbarkeit auswählen…",
    placeholderLocation: "z.B. Berlin, Deutschland",
    placeholderPrefLocation: "z.B. München, Remote, Hamburg",
    placeholderSalary: "z.B. 60000",
    optImmediately: "Sofort",
    opt2Weeks: "Innerhalb von 2 Wochen",
    opt1Month: "Innerhalb von 1 Monat",
    opt3Months: "Innerhalb von 3 Monaten",
    optNegotiable: "Verhandelbar",
    optFullTime: "Vollzeit",
    optPartTime: "Teilzeit",
    optContract: "Befristet",
    optFreelance: "Freiberuflich",
    placeholderIndustry: "Branche auswählen…",
    aiName: "KI-gestütztes Matching",
    aiDesc: "Nutzen Sie Claude KI, um Ihren Lebenslauf tiefgehend zu analysieren und die besten Stellen zu finden. Persönliche Daten (Name, E-Mail, Telefon, Adresse) werden automatisch maskiert.",
    aiMaskWarning: "🔐 Persönliche Daten werden vor der KI-Verarbeitung maskiert",
    backBtn: "← Zurück",
    findMatchesBtn: "Passende Jobs finden →",
    loadingTitle: "Ihre Matches werden gesucht",
    loadingSub: "Ihr Profil wird mit Tausenden von LinkedIn-Stellen abgeglichen…",
    loadingStage0: "Lebenslauf wird analysiert",
    loadingStage1: "Persönliche Daten werden maskiert",
    loadingStage2: "LinkedIn-Jobs werden durchsucht",
    loadingStage3: "KI-Matching & Ranking",
    loadingStage4: "Ergebnisse werden vorbereitet",
    resultsTitle: "Ihre",
    resultsHighlight: "Top-Matches",
    resultsSub: "Basierend auf Ihrem Lebenslauf + Präferenzen ·",
    jobsFound: "{n} Jobs gefunden",
    restartBtn: "↺ Neu starten",
    applyBtn: "Auf LinkedIn bewerben ↗",
    matchLabel: "{n}% Übereinstimmung",
    postedLabel: "Gepostet {date}",
    parseError: "Ergebnisse konnten nicht analysiert werden. Bitte versuchen Sie es erneut.",
    noJobsError: "Die KI hat keine Jobs zurückgegeben. Bitte versuchen Sie es erneut.",
    genericError: "Etwas ist schiefgelaufen. Bitte versuchen Sie es erneut.",
  },

  zh: {
    headerBadge: "领英 · AI驱动 · 2026",
    stepUpload: "上传简历",
    stepPreferences: "偏好设置",
    stepMatching: "职位匹配",
    stepResults: "匹配结果",
    step1of4: "第 1 步，共 4 步",
    uploadTitle: "上传您的简历",
    uploadSub: "请上传 PDF、DOCX 或 TXT 格式的简历，我们将自动提取您的技能与经验。",
    dropHere: "将简历拖放至此处",
    dropOr: "或点击浏览 · 支持 PDF、DOCX、TXT，最大 10 MB",
    cvReady: "简历已就绪",
    privacyNote: "🔒 隐私优先。您的简历数据仅用于求职匹配，不会被永久存储。选择 AI 匹配后，您的个人信息也将被自动屏蔽。",
    continueBtn: "继续填写偏好设置 →",
    errInvalidType: "请上传 PDF、DOCX、DOC、TXT 或 RTF 格式的文件。",
    errTooLarge: "文件大小不得超过 10 MB。",
    step2of4: "第 2 步，共 4 步",
    prefsTitle: "您的偏好设置",
    prefsSub: "告诉我们您的求职需求，以便我们为您推荐最匹配的职位。",
    labelAvailability: "可入职时间",
    labelJobType: "工作类型",
    labelLocation: "当前所在地",
    labelPrefLocation: "期望工作地点",
    prefLocationHint: "（填写城市名以匹配30公里范围，或填写"远程"）",
    labelIndustry: "期望行业",
    labelSalary: "当前年薪（选填）",
    placeholderAvailability: "请选择可入职时间…",
    placeholderLocation: "例如：上海，中国",
    placeholderPrefLocation: "例如：北京、远程、深圳",
    placeholderSalary: "例如：200000",
    optImmediately: "随时可入职",
    opt2Weeks: "两周内",
    opt1Month: "一个月内",
    opt3Months: "三个月内",
    optNegotiable: "可协商",
    optFullTime: "全职",
    optPartTime: "兼职",
    optContract: "合同制",
    optFreelance: "自由职业",
    placeholderIndustry: "请选择行业…",
    aiName: "AI 智能匹配",
    aiDesc: "使用 Claude AI 深度分析您的简历，智能推荐最合适的职位。在处理之前，您的个人信息（姓名、邮箱、电话、地址）将自动脱敏。",
    aiMaskWarning: "🔐 个人信息将在 AI 处理前自动脱敏",
    backBtn: "← 返回",
    findMatchesBtn: "开始匹配职位 →",
    loadingTitle: "正在为您寻找匹配职位",
    loadingSub: "正在将您的资料与数千个领英职位进行比对…",
    loadingStage0: "解析简历中",
    loadingStage1: "屏蔽个人信息",
    loadingStage2: "搜索领英职位",
    loadingStage3: "AI 匹配与排名",
    loadingStage4: "准备结果",
    resultsTitle: "您的",
    resultsHighlight: "最佳匹配",
    resultsSub: "基于您的简历和偏好设置 ·",
    jobsFound: "找到 {n} 个职位",
    restartBtn: "↺ 重新开始",
    applyBtn: "在领英上申请 ↗",
    matchLabel: "{n}% 匹配度",
    postedLabel: "{date}发布",
    parseError: "无法解析职位结果，请重试。",
    noJobsError: "AI 未返回任何职位，请重试。",
    genericError: "出现错误，请重试。",
  },

  ar: {
    headerBadge: "لينكد إن · مدعوم بالذكاء الاصطناعي · 2026",
    stepUpload: "رفع السيرة",
    stepPreferences: "التفضيلات",
    stepMatching: "المطابقة",
    stepResults: "النتائج",
    step1of4: "الخطوة 1 من 4",
    uploadTitle: "ارفع سيرتك الذاتية",
    uploadSub: "ارفع سيرتك الذاتية بصيغة PDF أو DOCX أو TXT. سنستخرج مهاراتك وخبراتك تلقائياً.",
    dropHere: "أسقط سيرتك الذاتية هنا",
    dropOr: "أو انقر للتصفح · PDF, DOCX, TXT حتى 10 ميغابايت",
    cvReady: "السيرة الذاتية جاهزة",
    privacyNote: "🔒 الخصوصية أولاً. بياناتك تُستخدم فقط للبحث عن وظائف ولا تُحفظ نهائياً. عند اختيار الذكاء الاصطناعي، ستُخفى جميع بياناتك الشخصية تلقائياً.",
    continueBtn: "← المتابعة إلى التفضيلات",
    errInvalidType: "يرجى رفع ملف بصيغة PDF أو DOCX أو DOC أو TXT أو RTF.",
    errTooLarge: "يجب أن يكون حجم الملف أقل من 10 ميغابايت.",
    step2of4: "الخطوة 2 من 4",
    prefsTitle: "تفضيلاتك",
    prefsSub: "أخبرنا بما تبحث عنه حتى نجد لك أنسب الفرص الوظيفية.",
    labelAvailability: "موعد الانضمام",
    labelJobType: "نوع الوظيفة",
    labelLocation: "موقعك الحالي",
    labelPrefLocation: "الموقع المفضل للعمل",
    prefLocationHint: "(مدينة لنطاق 30 كم، أو \"عن بعد\")",
    labelIndustry: "القطاع المفضل",
    labelSalary: "الراتب السنوي الحالي (اختياري)",
    placeholderAvailability: "اختر موعد الانضمام…",
    placeholderLocation: "مثال: الرياض، المملكة العربية السعودية",
    placeholderPrefLocation: "مثال: دبي، عن بعد، القاهرة",
    placeholderSalary: "مثال: 120000",
    optImmediately: "فوراً",
    opt2Weeks: "خلال أسبوعين",
    opt1Month: "خلال شهر",
    opt3Months: "خلال 3 أشهر",
    optNegotiable: "قابل للتفاوض",
    optFullTime: "دوام كامل",
    optPartTime: "دوام جزئي",
    optContract: "عقد",
    optFreelance: "مستقل",
    placeholderIndustry: "اختر قطاعاً…",
    aiName: "المطابقة بالذكاء الاصطناعي",
    aiDesc: "استخدم Claude AI لتحليل سيرتك الذاتية بعمق وإيجاد أنسب الوظائف. ستُخفى بياناتك الشخصية (الاسم، البريد، الهاتف، العنوان) تلقائياً قبل المعالجة.",
    aiMaskWarning: "🔐 ستُخفى البيانات الشخصية قبل معالجتها بالذكاء الاصطناعي",
    backBtn: "رجوع →",
    findMatchesBtn: "← ابحث عن وظائفي",
    loadingTitle: "نبحث عن وظائف مناسبة لك",
    loadingSub: "نحلل ملفك مقارنةً بآلاف الوظائف على لينكد إن…",
    loadingStage0: "تحليل السيرة الذاتية",
    loadingStage1: "إخفاء البيانات الشخصية",
    loadingStage2: "البحث في وظائف لينكد إن",
    loadingStage3: "المطابقة والترتيب بالذكاء الاصطناعي",
    loadingStage4: "تجهيز النتائج",
    resultsTitle: "أفضل",
    resultsHighlight: "الوظائف المناسبة لك",
    resultsSub: "بناءً على سيرتك الذاتية وتفضيلاتك ·",
    jobsFound: "{n} وظيفة",
    restartBtn: "↺ البدء من جديد",
    applyBtn: "التقدم على لينكد إن ↗",
    matchLabel: "{n}% تطابق",
    postedLabel: "نُشر {date}",
    parseError: "تعذّر تحليل النتائج. يرجى المحاولة مجدداً.",
    noJobsError: "لم يُرجع الذكاء الاصطناعي أي وظائف. يرجى المحاولة مجدداً.",
    genericError: "حدث خطأ ما. يرجى المحاولة مجدداً.",
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 4 — APP-LEVEL CONSTANTS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * LANGUAGES
 * Metadata for each supported locale displayed in the language selector.
 *   code   — BCP 47 language code used as key into TRANSLATIONS and for lang attr
 *   flag   — emoji flag for the language selector button and dropdown
 *   label  — English name of the language
 *   native — Native-script name shown alongside the English label
 *   dir    — "ltr" or "rtl" — sets document direction when language is selected
 */
const LANGUAGES = [
  { code: "en", flag: "🇬🇧", label: "English",  native: "English",   dir: "ltr" },
  { code: "es", flag: "🇪🇸", label: "Spanish",  native: "Español",   dir: "ltr" },
  { code: "fr", flag: "🇫🇷", label: "French",   native: "Français",  dir: "ltr" },
  { code: "de", flag: "🇩🇪", label: "German",   native: "Deutsch",   dir: "ltr" },
  { code: "zh", flag: "🇨🇳", label: "Chinese",  native: "中文",       dir: "ltr" },
  { code: "ar", flag: "🇸🇦", label: "Arabic",   native: "العربية",   dir: "rtl" },
];

/** STEPS — step labels come from TRANSLATIONS, so this is just an index array */
const STEP_KEYS = ["stepUpload", "stepPreferences", "stepMatching", "stepResults"];

/** INDUSTRIES — localised per language since industry names vary */
const INDUSTRIES = {
  en: ["Technology / Software","Finance / Banking","Healthcare / Pharma","Marketing / Advertising","Education","Consulting","Legal","Manufacturing / Engineering","Retail / E-commerce","Media / Entertainment","Real Estate","Hospitality / Travel","Non-profit / NGO","Government / Public Sector"],
  es: ["Tecnología / Software","Finanzas / Banca","Sanidad / Farmacia","Marketing / Publicidad","Educación","Consultoría","Legal","Manufactura / Ingeniería","Retail / E-commerce","Medios / Entretenimiento","Inmobiliaria","Hostelería / Turismo","ONG / Sin ánimo de lucro","Gobierno / Sector público"],
  fr: ["Technologie / Logiciels","Finance / Banque","Santé / Pharmacie","Marketing / Publicité","Éducation","Conseil","Juridique","Industrie / Ingénierie","Commerce / E-commerce","Médias / Divertissement","Immobilier","Hôtellerie / Tourisme","Associations / ONG","Gouvernement / Secteur public"],
  de: ["Technologie / Software","Finanzen / Bankwesen","Gesundheit / Pharma","Marketing / Werbung","Bildung","Beratung","Recht","Fertigung / Ingenieurwesen","Einzelhandel / E-Commerce","Medien / Unterhaltung","Immobilien","Gastgewerbe / Tourismus","Non-Profit / NGO","Regierung / Öffentlicher Sektor"],
  zh: ["科技 / 软件","金融 / 银行","医疗 / 制药","市场营销 / 广告","教育","咨询","法律","制造 / 工程","零售 / 电商","媒体 / 娱乐","房地产","酒店 / 旅游","非盈利 / NGO","政府 / 公共部门"],
  ar: ["التكنولوجيا / البرمجيات","المالية / المصرفية","الرعاية الصحية / الأدوية","التسويق / الإعلان","التعليم","الاستشارات","القانون","التصنيع / الهندسة","التجزئة / التجارة الإلكترونية","الإعلام / الترفيه","العقارات","الضيافة / السياحة","المنظمات غير الربحية","الحكومة / القطاع العام"],
};

const CURRENCIES = ["USD", "EUR", "CNY"];

const COMPANY_EMOJIS = ["🏢","💼","🌐","⚡","🚀","💡","🔬","📊","🏛️","🎯","💎","🌱","🔧","📱"];

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 5 — HELPER UTILITIES
// ─────────────────────────────────────────────────────────────────────────────

/** Strip PII from CV text before sending to Claude */
function maskPII(text) {
  return text
    .replace(/\b[A-Z][a-z]+ [A-Z][a-z]+\b/g, "[NAME REDACTED]")
    .replace(/\b[\w.-]+@[\w.-]+\.\w{2,}\b/g, "[EMAIL REDACTED]")
    .replace(/(\+?[\d\s\-().]{7,})/g, "[PHONE REDACTED]")
    .replace(/\b\d{1,4}[\s,]+[A-Za-z][\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b/gi, "[ADDRESS REDACTED]");
}

/** Map match score to CSS badge class */
function matchClass(score) {
  if (score >= 85) return "match-high";
  if (score >= 65) return "match-mid";
  return "match-low";
}

/** POST to Claude via Vite proxy */
async function callClaude(systemPrompt, userPrompt) {
  const res = await fetch("/api/anthropic/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "anthropic-version": "2023-06-01",
      "x-api-key": import.meta.env.VITE_ANTHROPIC_KEY,
      "anthropic-dangerous-direct-browser-access": "true",
    },
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

/** Strip markdown fences and extract raw JSON array from Claude response */
function extractJSON(text) {
  const m = text.match(/```json\s*([\s\S]*?)```/);
  if (m) return m[1].trim();
  const start = text.indexOf("["), end = text.lastIndexOf("]");
  if (start !== -1 && end !== -1) return text.slice(start, end + 1);
  return text;
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 6 — FILE READER
// ─────────────────────────────────────────────────────────────────────────────
async function readFileAsText(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result || "");
    reader.readAsText(file);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 7 — SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * LanguageSelector
 * Renders a pill button that opens a dropdown of all 6 language options.
 * Selecting a language calls onSelect(code) which updates App state.
 * The dropdown is closed when clicking outside (handled by onBlur with a
 * short delay to allow the option click to register first).
 *
 * Props:
 *   lang     {string}   — Active language code
 *   onSelect {Function} — Called with the new language code on selection
 */
function LanguageSelector({ lang, onSelect }) {
  const [open, setOpen] = useState(false);
  const current = LANGUAGES.find((l) => l.code === lang);

  return (
    <div className="lang-selector">
      <button
        className="lang-btn"
        onClick={() => setOpen((o) => !o)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      >
        <span className="lang-flag">{current.flag}</span>
        <span>{current.native}</span>
        <span style={{ fontSize: 10, color: "var(--muted)" }}>▾</span>
      </button>

      {open && (
        <div className="lang-dropdown">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              className={`lang-option ${l.code === lang ? "active" : ""}`}
              onClick={() => { onSelect(l.code); setOpen(false); }}
            >
              <span className="lang-option-flag">{l.flag}</span>
              <span className="lang-option-label">{l.label}</span>
              <span className="lang-option-native">{l.native}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Stepper — horizontal progress indicator, step labels from translations.
 * Props: current {number}, t {Function}
 */
function Stepper({ current, t }) {
  return (
    <div style={{ display:"flex", justifyContent:"center", padding:"32px 40px 0", position:"relative", zIndex:5 }}>
      <div style={{ display:"flex", alignItems:"center", width:"100%", maxWidth:600 }}>
        {STEP_KEYS.map((key, i) => {
          const done = i < current, active = i === current;
          return (
            <div key={i} style={{ display:"flex", alignItems:"center", flex: i < STEP_KEYS.length - 1 ? 1 : "none" }}>
              <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:6 }}>
                <div className={`step-dot ${active?"active":""} ${done?"done":""}`}
                  style={{
                    width:36,height:36,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",
                    fontFamily:"var(--font-mono)",fontSize:13,fontWeight:500,
                    border:done?"none":`1.5px solid ${active?"var(--gold)":"rgba(255,255,255,0.13)"}`,
                    background:done?"var(--gold)":active?"linear-gradient(135deg,rgba(201,168,76,0.2),rgba(232,200,106,0.08))":"var(--bg3)",
                    color:done?"#0a0d14":active?"var(--gold2)":"var(--muted)",
                    boxShadow:active?"0 0 20px rgba(201,168,76,0.15)":"none",transition:"all 0.3s",
                  }}>
                  {done ? "✓" : i + 1}
                </div>
                <span style={{ fontSize:11,fontWeight:500,letterSpacing:"0.5px",textTransform:"uppercase",whiteSpace:"nowrap",
                  color:done?"var(--text)":active?"var(--gold)":"var(--muted)",transition:"color 0.3s" }}>
                  {t(key)}
                </span>
              </div>
              {i < STEP_KEYS.length - 1 && (
                <div style={{ flex:1,height:1,margin:"0 8px",marginBottom:22,
                  background:done?"var(--gold)":"rgba(255,255,255,0.13)",transition:"background 0.4s" }} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * StepUpload — CV drag-and-drop card.
 * Props: onNext {Function}, t {Function}, lang {string}
 */
function StepUpload({ onNext, t }) {
  const [file,  setFile]  = useState(null);
  const [drag,  setDrag]  = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef();

  const accept = (f) => {
    const ok = ["application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain","application/msword"].includes(f.type) ||
      /\.(pdf|docx|doc|txt|rtf)$/i.test(f.name);
    if (!ok)                        { setError(t("errInvalidType")); return; }
    if (f.size > 10 * 1024 * 1024) { setError(t("errTooLarge"));    return; }
    setError(""); setFile(f);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0]; if (f) accept(f);
  }, []);

  return (
    <div className="card">
      <div className="section-label">{t("step1of4")}</div>
      <h2 className="card-title">{t("uploadTitle")}</h2>
      <p className="card-sub">{t("uploadSub")}</p>

      <div className={`drop-zone ${drag?"drag-over":""} ${file?"has-file":""}`}
        onClick={() => !file && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}>
        <input ref={inputRef} type="file" accept=".pdf,.doc,.docx,.txt,.rtf"
          style={{ display:"none" }}
          onChange={(e) => { const f = e.target.files[0]; if (f) accept(f); }} />

        {file ? (
          <>
            <span className="drop-icon">📄</span>
            <p className="drop-title" style={{ color:"var(--gold2)" }}>{t("cvReady")}</p>
            <div className="file-pill">
              <span>📎</span><span>{file.name}</span>
              <span style={{ color:"var(--muted)",fontSize:11 }}>({(file.size/1024).toFixed(0)} KB)</span>
              <button onClick={(e) => { e.stopPropagation(); setFile(null); }}>✕</button>
            </div>
          </>
        ) : (
          <>
            <span className="drop-icon">☁️</span>
            <p className="drop-title">{t("dropHere")}</p>
            <p className="drop-sub">{t("dropOr")}</p>
          </>
        )}
      </div>

      {error && <div className="error-pill">⚠️ {error}</div>}

      <div style={{ marginTop:20,padding:"14px 18px",background:"var(--bg3)",
        border:"1px solid var(--border)",borderRadius:"var(--r2)",fontSize:13,color:"var(--muted)" }}>
        {t("privacyNote")}
      </div>

      <div className="btn-row">
        <div />
        <button className="btn btn-primary" disabled={!file} onClick={() => onNext(file)}>
          {t("continueBtn")}
        </button>
      </div>
    </div>
  );
}

/**
 * StepPreferences — job preferences form, fully localised.
 * Props: onNext {Function}, onBack {Function}, t {Function}, lang {string}
 */
function StepPreferences({ onNext, onBack, t, lang }) {
  const [prefs, setPrefs] = useState({
    availability:"", location:"", preferredLocation:"",
    industry:"", jobType:"full-time", salary:"", currency:"USD", useAI:false,
  });
  const set = (k, v) => setPrefs((p) => ({ ...p, [k]: v }));
  const valid = prefs.availability && prefs.location && prefs.industry;

  // Localised industry list for the active language
  const industryList = INDUSTRIES[lang] || INDUSTRIES.en;

  return (
    <div className="card">
      <div className="section-label">{t("step2of4")}</div>
      <h2 className="card-title">{t("prefsTitle")}</h2>
      <p className="card-sub">{t("prefsSub")}</p>

      <div className="form-grid">
        <div className="field">
          <label>{t("labelAvailability")}</label>
          <select value={prefs.availability} onChange={(e) => set("availability", e.target.value)}>
            <option value="">{t("placeholderAvailability")}</option>
            <option value="Immediately">{t("optImmediately")}</option>
            <option value="Within 2 weeks">{t("opt2Weeks")}</option>
            <option value="Within 1 month">{t("opt1Month")}</option>
            <option value="Within 3 months">{t("opt3Months")}</option>
            <option value="Negotiable">{t("optNegotiable")}</option>
          </select>
        </div>

        <div className="field">
          <label>{t("labelJobType")}</label>
          <select value={prefs.jobType} onChange={(e) => set("jobType", e.target.value)}>
            <option value="full-time">{t("optFullTime")}</option>
            <option value="part-time">{t("optPartTime")}</option>
            <option value="contract">{t("optContract")}</option>
            <option value="freelance">{t("optFreelance")}</option>
          </select>
        </div>

        <div className="field full">
          <label>{t("labelLocation")}</label>
          <input type="text" placeholder={t("placeholderLocation")}
            value={prefs.location} onChange={(e) => set("location", e.target.value)} />
        </div>

        <div className="field full">
          <label>
            {t("labelPrefLocation")}{" "}
            <span style={{ color:"var(--muted)",textTransform:"none",fontSize:11 }}>
              {t("prefLocationHint")}
            </span>
          </label>
          <input type="text" placeholder={t("placeholderPrefLocation")}
            value={prefs.preferredLocation} onChange={(e) => set("preferredLocation", e.target.value)} />
        </div>

        <div className="field full">
          <label>{t("labelIndustry")}</label>
          <select value={prefs.industry} onChange={(e) => set("industry", e.target.value)}>
            <option value="">{t("placeholderIndustry")}</option>
            {industryList.map((ind) => <option key={ind}>{ind}</option>)}
          </select>
        </div>

        <div className="field full">
          <label>{t("labelSalary")}</label>
          <div className="salary-row">
            <input type="number" placeholder={t("placeholderSalary")}
              value={prefs.salary} onChange={(e) => set("salary", e.target.value)} />
            <select value={prefs.currency} onChange={(e) => set("currency", e.target.value)}>
              {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className={`ai-toggle-card ${prefs.useAI ? "active" : ""}`}
        onClick={() => set("useAI", !prefs.useAI)}>
        <div className="ai-icon">🤖</div>
        <div className="ai-info">
          <div className="ai-name">{t("aiName")}</div>
          <div className="ai-desc">{t("aiDesc")}</div>
          {prefs.useAI && <div className="mask-warning">{t("aiMaskWarning")}</div>}
        </div>
        <div className={`toggle-switch ${prefs.useAI ? "on" : ""}`} />
      </div>

      <div className="btn-row">
        <button className="btn btn-ghost" onClick={onBack}>{t("backBtn")}</button>
        <button className="btn btn-primary" disabled={!valid} onClick={() => onNext(prefs)}>
          {t("findMatchesBtn")}
        </button>
      </div>
    </div>
  );
}

/**
 * StepLoading — animated loading screen with localised stage labels.
 * Props: loadingStep {number}, t {Function}
 */
function StepLoading({ loadingStep, t }) {
  const stages = [
    t("loadingStage0"), t("loadingStage1"), t("loadingStage2"),
    t("loadingStage3"), t("loadingStage4"),
  ];

  return (
    <div className="card">
      <div className="loading-screen">
        <div className="spinner-ring" />
        <div>
          <h2 className="card-title" style={{ textAlign:"center" }}>{t("loadingTitle")}</h2>
          <p className="card-sub" style={{ textAlign:"center" }}>{t("loadingSub")}</p>
        </div>
        <div className="loading-steps">
          {stages.map((label, i) => (
            <div key={i} className={`loading-step ${i < loadingStep ? "done" : i === loadingStep ? "active" : ""}`}>
              <span className="loading-step-icon">
                {i < loadingStep ? "✅" : i === loadingStep ? "⏳" : "⬜"}
              </span>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * StepResults — results header + responsive job grid.
 * Props: jobs {Array}, prefs {Object}, onRestart {Function}, t {Function}
 */
function StepResults({ jobs, prefs, onRestart, t }) {
  const [saved, setSaved] = useState({});

  return (
    <>
      <div className="results-header">
        <div>
          <h2 className="results-title">
            {t("resultsTitle")} <span>{t("resultsHighlight")}</span>
          </h2>
          <p style={{ color:"var(--muted)",fontSize:14,marginTop:4 }}>
            {t("resultsSub")} {prefs.preferredLocation || prefs.location}
          </p>
        </div>
        <div style={{ display:"flex",gap:10,alignItems:"center" }}>
          <div className="results-count">
            {t("jobsFound").replace("{n}", jobs.length)}
          </div>
          <button className="btn btn-ghost" style={{ padding:"8px 18px",fontSize:13 }} onClick={onRestart}>
            {t("restartBtn")}
          </button>
        </div>
      </div>

      <div className="jobs-grid">
        {jobs.map((job, i) => (
          <JobCard key={i} job={job} idx={i}
            saved={!!saved[i]}
            onSave={() => setSaved((s) => ({ ...s, [i]: !s[i] }))}
            t={t} />
        ))}
      </div>
    </>
  );
}

/**
 * JobCard — single job listing.
 * Props: job, idx, saved, onSave, t {Function}
 */
function JobCard({ job, idx, saved, onSave, t }) {
  const delay = Math.min(idx * 0.04, 0.6);
  const mc = matchClass(job.matchScore);

  return (
    <div className="job-card" style={{ animationDelay:`${delay}s` }}>
      <div className="job-header">
        <div className="job-logo">{COMPANY_EMOJIS[idx % COMPANY_EMOJIS.length]}</div>
        <div className={`match-badge ${mc}`}>
          {t("matchLabel").replace("{n}", job.matchScore)}
        </div>
      </div>

      <div className="job-title">{job.title}</div>
      <div className="job-company">{job.company} · {job.location}</div>

      <div className="job-tags">
        {(job.tags || []).slice(0, 4).map((tag, i) => (
          <span key={i} className="job-tag">{tag}</span>
        ))}
      </div>

      <div className="job-meta">
        <div className="job-meta-item"><span className="job-meta-icon">💰</span>{job.salary}</div>
        <div className="job-meta-item"><span className="job-meta-icon">⏱️</span>{job.type}</div>
        <div className="job-meta-item">
          <span className="job-meta-icon">📅</span>
          {t("postedLabel").replace("{date}", job.posted)}
        </div>
      </div>

      <div className="job-desc">{job.description}</div>

      <div className="job-footer">
        <button className="btn-apply"
          onClick={() => window.open(`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(job.title + " " + job.company)}`, "_blank")}>
          {t("applyBtn")}
        </button>
        <button className={`btn-save ${saved ? "saved" : ""}`} onClick={onSave}>
          {saved ? "★" : "☆"}
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 8 — ROOT APP COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

/**
 * App — root state machine with language management.
 *
 * Language state:
 *   lang {string} — active BCP 47 language code (default "en")
 *
 * When lang changes:
 *   1. document.documentElement.lang is set to the code (e.g. "ar")
 *   2. document.documentElement.dir is set to "ltr" or "rtl"
 *   3. The CSS [lang="ar"] and [dir="rtl"] selectors automatically apply
 *      the correct font stack and layout mirroring.
 *
 * Translation function t(key):
 *   Looks up key in TRANSLATIONS[lang] and returns the localised string.
 *   Falls back to TRANSLATIONS.en[key] if the key is missing in the locale.
 */
export default function App() {
  const [step,        setStep]        = useState(0);
  const [cvFile,      setCvFile]      = useState(null);
  const [prefs,       setPrefs]       = useState(null);
  const [jobs,        setJobs]        = useState([]);
  const [error,       setError]       = useState("");
  const [loadingStep, setLoadingStep] = useState(0);
  const [lang,        setLang]        = useState("en"); // active language code

  /**
   * handleLangChange(code)
   * Updates the active language and applies document-level attributes so that
   * CSS font and RTL selectors fire immediately.
   *
   * @param {string} code — BCP 47 language code from LANGUAGES array
   */
  const handleLangChange = (code) => {
    const meta = LANGUAGES.find((l) => l.code === code);
    setLang(code);
    document.documentElement.lang = code;
    document.documentElement.dir  = meta?.dir || "ltr";
  };

  /**
   * t(key)
   * Translation lookup function passed as a prop to every component.
   * Returns the localised string for `key` in the active language,
   * falling back to English if the key is not found.
   *
   * @param   {string} key — TRANSLATIONS key name
   * @returns {string}     — Localised UI string
   */
  const t = (key) =>
    TRANSLATIONS[lang]?.[key] ?? TRANSLATIONS.en[key] ?? key;

  const handleUpload = (file) => { setCvFile(file); setStep(1); };

  const handlePrefs = async (userPrefs) => {
    setPrefs(userPrefs);
    setStep(2); setLoadingStep(0); setError("");

    try {
      let cvText = await readFileAsText(cvFile);
      if (!cvText || cvText.trim().length < 30) {
        cvText = `[CV — ${cvFile.name}]\nProfessional seeking a ${userPrefs.jobType} role in ${userPrefs.industry}.\nAvailable ${userPrefs.availability}.`;
      }
      setLoadingStep(1);
      if (userPrefs.useAI) { cvText = maskPII(cvText); await new Promise(r => setTimeout(r, 600)); }

      setLoadingStep(2);
      await new Promise(r => setTimeout(r, 500));
      setLoadingStep(3);

      // Tell Claude to respond in the active UI language
      const langName = LANGUAGES.find((l) => l.code === lang)?.label || "English";

      const system = `You are a LinkedIn job matching engine. Return ONLY valid JSON array. No markdown, no explanation. Write all job titles, company names, descriptions, and tags in ${langName}.`;

      const prompt =
`Generate exactly 20 realistic LinkedIn job listings as a JSON array.

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
- Response language: ${langName}

Return a JSON array of exactly 20 objects:
{
  "title": "Job title",
  "company": "Company name",
  "location": "City, Country or Remote",
  "salary": "e.g. $90,000–$120,000/yr",
  "type": "Full-time / Part-time / Contract",
  "matchScore": 72,
  "posted": "e.g. 2 days ago",
  "tags": ["Skill1","Skill2","Skill3"],
  "description": "2–3 sentence summary relevant to this candidate"
}

Rules: matchScore 62–97, vary company sizes, realistic locations, relevant tags.`;

      const raw = await callClaude(system, prompt);
      setLoadingStep(4);

      let parsed;
      try { parsed = JSON.parse(extractJSON(raw)); }
      catch { throw new Error(t("parseError")); }

      if (!Array.isArray(parsed) || parsed.length === 0) throw new Error(t("noJobsError"));

      parsed.sort((a, b) => b.matchScore - a.matchScore);
      await new Promise(r => setTimeout(r, 400));
      setJobs(parsed.slice(0, 20));
      setStep(3);

    } catch (e) {
      setError(e.message || t("genericError"));
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
        <div className="header-right">
          <div className="header-badge">{t("headerBadge")}</div>
          {/* Language selector — always visible in the header */}
          <LanguageSelector lang={lang} onSelect={handleLangChange} />
        </div>
      </header>

      {step < 3 && <Stepper current={step} t={t} />}

      <main style={{
        position:"relative", zIndex:5, flex:1,
        padding: step === 3 ? "40px 24px 60px" : "40px 24px 60px",
        display:"flex", flexDirection:"column", alignItems:"center",
      }}>
        {step === 0 && <StepUpload onNext={handleUpload} t={t} lang={lang} />}
        {step === 1 && (
          <>
            <StepPreferences onNext={handlePrefs} onBack={() => setStep(0)} t={t} lang={lang} />
            {error && (
              <div className="error-pill" style={{ maxWidth:680, marginTop:12 }}>
                ⚠️ {error}
              </div>
            )}
          </>
        )}
        {step === 2 && <StepLoading loadingStep={loadingStep} t={t} />}
        {step === 3 && <StepResults jobs={jobs} prefs={prefs} onRestart={restart} t={t} />}
      </main>
    </div>
  );
}