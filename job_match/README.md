# CareerMatch — AI-Powered Job Matching Application

> Upload your CV, set your preferences, and receive your top 20 LinkedIn job matches — powered by Claude AI with multi-language support and automatic PII masking.

---

## Table of Contents

1. [Overview](#overview)
2. [Supported Languages](#supported-languages)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Prerequisites](#prerequisites)
7. [Installation](#installation)
8. [Configuration](#configuration)
9. [Running Locally](#running-locally)
10. [Application Flow](#application-flow)
11. [i18n Architecture](#i18n-architecture)
12. [Adding a New Language](#adding-a-new-language)
13. [Component Reference](#component-reference)
14. [Helper Functions](#helper-functions)
15. [AI Matching & PII Masking](#ai-matching--pii-masking)
16. [Design System](#design-system)
17. [RTL Support](#rtl-support)
18. [Environment Variables](#environment-variables)
19. [Known Limitations](#known-limitations)
20. [Future Improvements](#future-improvements)
21. [Security Notes](#security-notes)

---

## Overview

CareerMatch is a single-page React application that guides job seekers through a four-step workflow:

| Step | Name        | Description                                               |
|------|-------------|-----------------------------------------------------------|
| 0    | Upload      | Drag-and-drop or click-to-browse CV upload (PDF/DOCX/TXT) |
| 1    | Preferences | Form: availability, location, industry, job type, salary  |
| 2    | Matching    | Animated loading screen while AI analyses the CV          |
| 3    | Results     | Responsive grid of 20 ranked job cards with LinkedIn links |

The language selector in the header lets users switch between 6 languages instantly, with no page reload. Arabic triggers a full RTL layout flip.

---

## Supported Languages

| Code | Language | Script | Direction | Font             |
|------|----------|--------|-----------|------------------|
| `en` | English  | Latin  | LTR       | Playfair Display + DM Sans |
| `es` | Spanish  | Latin  | LTR       | Playfair Display + DM Sans |
| `fr` | French   | Latin  | LTR       | Playfair Display + DM Sans |
| `de` | German   | Latin  | LTR       | Playfair Display + DM Sans |
| `zh` | Chinese (Simplified) | CJK | LTR | Noto Sans SC    |
| `ar` | Arabic   | Arabic | **RTL**   | Noto Sans Arabic |

---

## Features

- **6-language UI** — all labels, placeholders, error messages, and job content switch instantly
- **RTL layout** — Arabic triggers `dir="rtl"` on `<html>` and CSS mirrors the entire layout
- **Language-aware AI prompts** — Claude is instructed to return job titles, descriptions, and tags in the active language
- **Localised industry lists** — industry dropdown is translated per language
- **CV Upload** — accepts PDF, DOCX, DOC, TXT, RTF up to 10 MB
- **Preferences Form** — availability, location, preferred location (30 km radius), industry, job type, salary + currency
- **AI Job Matching** — Claude generates 20 ranked, realistic LinkedIn job listings
- **PII Masking** — personal details redacted before AI processing when enabled
- **Match Score Badges** — green (≥ 85%), gold (≥ 65%), blue (< 65%)
- **LinkedIn Deep Links** — each card opens a LinkedIn job search in a new tab
- **Bookmark Toggle** — session-scoped star bookmarks on each job card
- **Responsive Layout** — auto-fill CSS grid, mobile-friendly single column

---

## Tech Stack

| Layer       | Technology                                         |
|-------------|----------------------------------------------------|
| Framework   | React 18 (hooks only)                              |
| Build Tool  | Vite 8                                             |
| Styling     | Injected CSS with CSS custom properties            |
| i18n        | Custom `TRANSLATIONS` object + `t()` function      |
| Fonts       | Google Fonts: Playfair Display, DM Sans, DM Mono, Noto Sans Arabic, Noto Sans SC |
| AI          | Anthropic Claude `claude-sonnet-4-20250514`        |
| API Proxy   | Vite dev-server proxy (`/api/anthropic/*`)         |
| Node        | v18 or higher                                      |

---

## Project Structure

```
career-match/
├── public/
├── src/
│   ├── App.jsx          ← Replace with job-matcher.jsx contents
│   ├── index.css        ← Clear this file completely
│   └── main.jsx         ← Unchanged (Vite entry point)
├── .env                 ← API key (never commit)
├── .gitignore
├── index.html
├── package.json
└── vite.config.js       ← Proxy config (see Configuration)
```

---

## Prerequisites

- **Node.js** v18+ — [nodejs.org](https://nodejs.org)
- **npm** v9+ (bundled with Node)
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)

---

## Installation

### 1. Create Vite + React project

```bash
npm create vite@latest career-match -- --template react
cd career-match
npm install
```

### 2. Replace App component

```bash
cp /path/to/job-matcher.jsx src/App.jsx
```

### 3. Clear default stylesheets

Open `src/index.css` and `src/App.css` and delete all contents (leave the files empty).

---

## Configuration

### vite.config.js

Replace the entire file:

```js
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api/anthropic': {
          target: 'https://api.anthropic.com',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/anthropic/, ''),
          headers: {
            'anthropic-version': '2023-06-01',
            'x-api-key': env.VITE_ANTHROPIC_KEY,
            'anthropic-dangerous-direct-browser-access': 'true',
          },
        },
      },
    },
  }
})
```

---

## Environment Variables

Create `.env` in the project root:

```
VITE_ANTHROPIC_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx
```

Rules: no quotes, no spaces around `=`, never commit this file.

---

## Running Locally

```bash
npm run dev
# Open http://localhost:5173
```

Restart the dev server after any change to `vite.config.js` or `.env`.

---

## Application Flow

```
User opens http://localhost:5173
         │
         ▼
  [Language Selector] ─── Changes lang state → updates document lang/dir
         │
         ▼
STEP 0 — StepUpload
  Drag-and-drop or pick CV → validate type/size → "Continue →"
         │  handleUpload(file)
         ▼
STEP 1 — StepPreferences
  Fill availability, location, preferred location, industry,
  job type, salary, currency. Toggle AI matching.
         │  handlePrefs(prefs)
         ▼
STEP 2 — StepLoading (async pipeline)
  Stage 0  Read CV as text
  Stage 1  maskPII() if useAI (+ 600ms visual delay)
  Stage 2  Visual delay — "Searching LinkedIn"
  Stage 3  POST to /api/anthropic/v1/messages
           Claude returns JSON array of 20 jobs (in active language)
  Stage 4  Parse, sort by matchScore, store
         │  setJobs + setStep(3)
         ▼
STEP 3 — StepResults
  20 job cards, sorted by match %, with Apply + bookmark buttons
  "↺ Restart" resets all state to Step 0
```

---

## i18n Architecture

### Overview

The application uses a lightweight custom i18n system — no external library is required.

```
TRANSLATIONS (constant)
    └── { en: {...}, es: {...}, fr: {...}, de: {...}, zh: {...}, ar: {...} }
              │
              │  App state: lang = "en" | "es" | "fr" | "de" | "zh" | "ar"
              │
              ▼
         t(key) function
    Returns TRANSLATIONS[lang][key] ?? TRANSLATIONS.en[key] ?? key
              │
              │  Passed as prop to every sub-component
              ▼
    <StepUpload t={t} />
    <StepPreferences t={t} lang={lang} />
    <StepLoading t={t} />
    <StepResults t={t} />
    <JobCard t={t} />
    <Stepper t={t} />
```

### Language switching

When the user selects a language in `LanguageSelector`:

```js
handleLangChange(code)
  → setLang(code)                          // React state re-render
  → document.documentElement.lang = code   // triggers CSS [lang="ar"] selectors
  → document.documentElement.dir  = dir    // triggers CSS [dir="rtl"] selectors
```

### String interpolation

Some translation strings contain `{placeholder}` tokens. These are resolved at render time using `.replace()`:

```js
// TRANSLATIONS.en.jobsFound = "{n} jobs found"
t("jobsFound").replace("{n}", jobs.length)   // → "20 jobs found"

// TRANSLATIONS.ar.jobsFound = "{n} وظيفة"
t("jobsFound").replace("{n}", jobs.length)   // → "20 وظيفة"
```

### Language-aware Claude prompts

The active language name is injected into the Claude system prompt:

```
Write all job titles, company names, descriptions, and tags in ${langName}.
```

This ensures job listings appear in the same language as the UI without post-processing.

### Localised industry lists

Industries are stored per language in `INDUSTRIES[langCode]`, since industry names vary significantly across languages. The active language list is selected at render time:

```js
const industryList = INDUSTRIES[lang] || INDUSTRIES.en;
```

---

## Adding a New Language

To add a 7th language (e.g. Portuguese `pt`):

### 1. Add font loading (if needed)

If the language uses a non-Latin script, add a Google Fonts `<link>` to the font injection array at the top of the file.

### 2. Add to LANGUAGES array

```js
{ code: "pt", flag: "🇧🇷", label: "Portuguese", native: "Português", dir: "ltr" },
```

### 3. Add to TRANSLATIONS

```js
pt: {
  headerBadge: "LinkedIn · IA · 2026",
  stepUpload: "Enviar CV",
  uploadTitle: "Envie seu currículo",
  // ... all keys from the en object
},
```

All keys present in `en` must be present in the new locale. The `t()` function falls back to `en` for missing keys, so partial translations work without breaking the UI.

### 4. Add to INDUSTRIES

```js
INDUSTRIES.pt = ["Tecnologia / Software", "Finanças / Banco", /* ... */];
```

### 5. Add RTL CSS overrides (if needed)

If the language is RTL, add `dir: "rtl"` to its LANGUAGES entry. The existing `[dir="rtl"]` CSS block handles the layout mirroring automatically.

---

## Component Reference

### `App`

Root state machine. Owns all state including language.

| State | Type | Description |
|-------|------|-------------|
| `step` | `number` | Active step (0–3) |
| `cvFile` | `File\|null` | Uploaded CV |
| `prefs` | `Object\|null` | User preferences |
| `jobs` | `Array` | Sorted job results |
| `error` | `string` | Error message |
| `loadingStep` | `number` | Loading stage (0–4) |
| `lang` | `string` | Active language code |

| Function | Description |
|----------|-------------|
| `t(key)` | Translates a key for the active language |
| `handleLangChange(code)` | Updates lang state + document attributes |
| `handleUpload(file)` | Stores CV, advances to step 1 |
| `handlePrefs(prefs)` | Runs async pipeline, drives loading |
| `restart()` | Resets all state to step 0 |

---

### `LanguageSelector`

Flag + name pill button with dropdown of all 6 languages.

| Prop | Type | Description |
|------|------|-------------|
| `lang` | `string` | Active language code |
| `onSelect` | `Function(code)` | Called when user picks a language |

---

### `Stepper`

4-step progress bar. Step labels come from `t()`.

| Prop | Type | Description |
|------|------|-------------|
| `current` | `number` | Active step index |
| `t` | `Function` | Translation function |

---

### `StepUpload`

| Prop | Type | Description |
|------|------|-------------|
| `onNext` | `Function(file)` | Advances to step 1 |
| `t` | `Function` | Translation function |
| `lang` | `string` | Active language (passed for future extension) |

---

### `StepPreferences`

| Prop | Type | Description |
|------|------|-------------|
| `onNext` | `Function(prefs)` | Submits preferences |
| `onBack` | `Function` | Returns to upload |
| `t` | `Function` | Translation function |
| `lang` | `string` | Used to select the correct `INDUSTRIES[lang]` list |

---

### `StepLoading`

| Prop | Type | Description |
|------|------|-------------|
| `loadingStep` | `number` | Active stage index (0–4) |
| `t` | `Function` | Translation function |

---

### `StepResults`

| Prop | Type | Description |
|------|------|-------------|
| `jobs` | `Array` | Sorted job objects |
| `prefs` | `Object` | Preferences (for location subtitle) |
| `onRestart` | `Function` | Resets to step 0 |
| `t` | `Function` | Translation function |

---

### `JobCard`

| Prop | Type | Description |
|------|------|-------------|
| `job` | `Object` | Job data |
| `idx` | `number` | Card index (emoji cycling + stagger delay) |
| `saved` | `boolean` | Bookmarked state |
| `onSave` | `Function` | Toggles bookmark |
| `t` | `Function` | Translation function |

Job object schema:

```js
{
  title:       string,   // In active language
  company:     string,
  location:    string,
  salary:      string,
  type:        string,
  matchScore:  number,   // 62–97
  posted:      string,
  tags:        string[], // In active language
  description: string,   // In active language
}
```

---

## Helper Functions

### `maskPII(text)`

Strips names, emails, phone numbers, and addresses before sending to Claude. Called only when `useAI` is `true`.

### `matchClass(score)`

| Score | CSS class | Colour |
|-------|-----------|--------|
| ≥ 85 | `match-high` | Green |
| ≥ 65 | `match-mid` | Gold |
| < 65 | `match-low` | Blue |

### `callClaude(systemPrompt, userPrompt)`

POSTs to `/api/anthropic/v1/messages`. Returns Claude's text response or throws on API error.

### `extractJSON(text)`

Strips markdown fences and extracts the JSON array from Claude's response.

### `readFileAsText(file)`

Wraps `FileReader` in a Promise. Returns UTF-8 text or empty string for binary files.

---

## AI Matching & PII Masking

### Language-aware prompt

The active language is passed into the Claude system prompt:

```
Write all job titles, company names, descriptions, and tags in German.
```

Claude responds with all human-readable job content in the requested language, so the results page feels native to the user.

### PII masking pipeline (when AI enabled)

```
Raw CV text
    │
    ▼
maskPII() — regex passes:
    │  [NAME REDACTED]     (two Title-Cased words)
    │  [EMAIL REDACTED]    (email pattern)
    │  [PHONE REDACTED]    (7+ digit sequences)
    │  [ADDRESS REDACTED]  (street number + road keyword)
    ▼
Masked CV text ──→ Claude API
```

---

## Design System

### Colour tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--gold` | `#c9a84c` | Primary brand accent |
| `--accent` | `#4f7cff` | AI feature highlights |
| `--green` | `#43d48a` | High match scores |
| `--red` | `#ff5f6d` | Errors |
| `--surface` | `#1c2236` | Cards |
| `--muted` | `#8890a8` | Secondary text |

### Typography tokens

| Token | Font | Usage |
|-------|------|-------|
| `--font-serif` | Playfair Display | Headings (Latin only) |
| `--font-sans` | DM Sans | Body, buttons, labels |
| `--font-mono` | DM Mono | Badges, step numbers |

Language-specific overrides apply automatically via CSS attribute selectors:
- `[lang="ar"]` → Noto Sans Arabic for all text
- `[lang="zh"]` → Noto Sans SC for body; preserved for headings

---

## RTL Support

Arabic (`ar`) triggers a full right-to-left layout via two mechanisms:

**1. Document attribute** (set by `handleLangChange`):
```js
document.documentElement.dir = "rtl"
```

**2. CSS `[dir="rtl"]` overrides** that explicitly mirror:
- Flex row direction (`.logo`, `.header-right`, `.btn-row`, etc.)
- Select arrow position (moves from right to left)
- Toggle switch thumb direction (slides left instead of right)
- Dropdown panel alignment (appears from the right edge)
- Letter-spacing removed (Arabic does not use Latin tracking)

The browser handles text alignment, bidirectional text rendering, and most flexbox mirroring automatically once `dir="rtl"` is set.

---

## Known Limitations

| Limitation | Detail |
|------------|--------|
| Binary CV parsing | PDF/DOCX text extraction is unreliable via FileReader; a synthetic fallback is used |
| Regex PII masking | Heuristic; misses non-Latin names and non-Western address formats |
| AI-generated jobs | Claude produces realistic but fictional listings — not live LinkedIn data |
| Session-only bookmarks | Saved jobs are lost on page refresh |
| Partial RTL for mixed content | Job cards with mixed LTR/RTL content may have minor alignment edge cases |
| Claude language accuracy | For low-resource languages, Claude may occasionally mix languages in job content |

---

## Future Improvements

- **Real LinkedIn API** — Replace simulated jobs with live listings
- **Server-side CV parsing** — Use `pdf-parse` / `mammoth.js` for binary files
- **i18n library** — Replace custom `t()` with `react-i18next` for plural rules, date formatting, and number formatting per locale
- **More languages** — Japanese, Korean, Portuguese, Hindi, Russian
- **Locale-aware formatting** — Salary ranges, date strings, and number separators vary by locale
- **Persistent bookmarks** — `localStorage` or database-backed saves
- **Production API proxy** — Express middleware or edge function instead of Vite dev proxy

---

## Security Notes

- The Anthropic API key is read by the Vite proxy at startup from `.env` and is never included in the browser bundle
- CV text is held in memory only and is never written to disk or a database
- PII masking runs locally in the browser before any data leaves the device
- The `.env` file is excluded from Git by Vite's default `.gitignore`
- For production, replace the Vite proxy with a server-side middleware that authenticates users before forwarding to the Anthropic API