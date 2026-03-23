<div align="center">

# Visual Story Creator

**Transform any topic into a publication-grade interactive visual story — fully automated.**

One topic in. One stunning scrollytelling HTML page out.

[**See the Live Demo (EN)**](https://lowtidebuild.github.io/visual-story-creator/en.html) &nbsp;&middot;&nbsp; [**라이브 데모 (KO)**](https://lowtidebuild.github.io/visual-story-creator/ko.html) &nbsp;&middot;&nbsp; [한국어 README](README.ko.md)

---

<br>

<img src="https://img.shields.io/badge/pipeline-7_steps-7C3AED?style=for-the-badge" alt="7 Steps" />
<img src="https://img.shields.io/badge/agents-5_specialized-2563EB?style=for-the-badge" alt="5 Agents" />
<img src="https://img.shields.io/badge/output-self--contained_HTML-10B981?style=for-the-badge" alt="Self-contained HTML" />
<img src="https://img.shields.io/badge/quality-FT%20%2F%20NYT%20grade-F59E0B?style=for-the-badge" alt="FT/NYT Grade" />

</div>

<br>

## What It Does

Visual Story Creator is an orchestrated AI pipeline that takes a **single topic** and produces a **complete, self-contained scrollytelling HTML page** — the kind you'd see on the Financial Times or The New York Times.

No templates. No drag-and-drop. No manual layout. Just a topic and a pipeline that handles everything: deep research, narrative arc design, section writing, editorial review, and interactive HTML assembly.

> **The output is a single `.html` file.** Open it in any browser. No server, no dependencies, no build step.

<br>

## Pipeline Architecture

```
 Topic
  │
  ▼
 ┌─────────────────────────────────────────────┐
 │  Step 1.  Deep Research                      │  → Researcher Agent
 │           15–30 research questions            │     web search, cross-verification
 │           quantitative data extraction        │     70%+ verification rate
 └──────────────────┬──────────────────────────┘
                    ▼
 ┌─────────────────────────────────────────────┐
 │  Step 2.  Story Arc Design                   │  → Arc Designer Agent
 │           5–20 beat narrative structure       │     HOOK → BUILD → TURN → RESOLVE
 │           visual directives per beat          │     data-viz specifications
 └──────────────────┬──────────────────────────┘
                    ▼
 ╔═════════════════════════════════════════════╗
 ║  Gate 1   Human reviews the arc             ║
 ║           approve · revise · reject          ║
 ╚══════════════════╤══════════════════════════╝
                    ▼
 ┌─────────────────────────────────────────────┐
 │  Step 3.  Section Writing (parallel)         │  → Section Writer Agent × N
 │           up to 5 beats written concurrently  │     FT/NYT editorial style
 │           per-beat retry on failure            │     strict word limits
 └──────────────────┬──────────────────────────┘
                    ▼
 ┌─────────────────────────────────────────────┐
 │  Step 4.  Editing & Fact-Check               │  → Editor Agent
 │           narrative flow review               │     fact verification
 │           style enforcement                   │     in-place rewrites
 └──────────────────┬──────────────────────────┘
                    ▼
 ┌─────────────────────────────────────────────┐
 │  Step 7.  HTML Assembly                      │  → Layout Assembler Agent
 │           scroll animations (Scrollama)       │     responsive layout
 │           data tables, progress bar           │     single self-contained file
 └──────────────────┬──────────────────────────┘
                    ▼
 ┌─────────────────────────────────────────────┐
 │  Step 7.5 QA Check (non-blocking)            │  → qa-check.py
 │           viewport, OG tags, accessibility    │     beat count validation
 └──────────────────┬──────────────────────────┘
                    ▼
 ╔═════════════════════════════════════════════╗
 ║  Gate 2   Human reviews the final HTML      ║
 ║           approve · revise beats · reject    ║
 ╚══════════════════╤══════════════════════════╝
                    ▼
               story.html
```

<br>

## The Agents

Five specialized Claude Code sub-agents, each with a single responsibility:

| Agent | Role | Key Capability |
|:------|:-----|:---------------|
| **Researcher** | Deep-dives into the topic | Decomposes into 15–30 questions, web-searches each, cross-verifies facts to 70%+ confidence |
| **Arc Designer** | Architects the narrative | Designs a 5–20 beat story arc following FT/Pudding scrollytelling patterns |
| **Section Writer** | Writes each beat | FT/NYT editorial voice, strict word limits per beat type, runs in parallel (up to 5×) |
| **Editor** | Reviews and polishes | Checks narrative flow, fact accuracy, word counts, style — rewrites in-place |
| **Layout Assembler** | Builds the final HTML | Converts beats to interactive scrollytelling with Scrollama, data tables, responsive design |

<br>

## Output Quality

The pipeline targets **publication-grade** output across multiple dimensions:

- **Writing** — Short, concrete, active voice. No filler. Every sentence earns its place.
- **Data** — Every numeric claim traced to a source. Unverified data explicitly tagged.
- **Visuals** — Scroll-triggered animations, stat cards, comparison grids, timelines, and data tables.
- **Interactivity** — Progress bar, table of contents navigation, smooth scroll transitions.
- **Accessibility** — Semantic HTML, responsive design, readable typography.
- **Portability** — Single `.html` file. No external dependencies. Opens anywhere.

<br>

## Project Structure

```
visual-story-creator/
├── .claude/agents/          # 5 specialized sub-agent instructions
│   ├── researcher/
│   ├── arc-designer/
│   ├── section-writer/
│   ├── editor/
│   └── layout-assembler/
├── schemas/                 # JSON schemas for pipeline validation
│   ├── pipeline_state.schema.json
│   ├── story_arc.schema.json
│   └── data_points.schema.json
├── scripts/
│   └── qa-check.py          # HTML quality validator
├── assets/js/
│   └── scrollama.min.js     # Scroll-triggered animation library
├── input/                   # User-provided reference materials
├── output/                  # Generated artifacts (gitignored)
│   ├── research/            # Step 1: reports, data, citations
│   ├── arc/                 # Step 2: story arc JSON
│   ├── sections/            # Steps 3–4: beat markdown files
│   ├── build/               # Step 7: final HTML
│   └── qa/                  # Step 7.5: QA reports
└── CLAUDE.md                # Orchestrator instructions
```

<br>

## How It Works

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed and authenticated

### Run the Pipeline

```bash
cd visual-story-creator
claude
```

The orchestrator reads `CLAUDE.md` and prompts you for a topic. From there, it runs autonomously — pausing only at the two human review gates.

### Pipeline State

All progress is tracked in `output/pipeline_state.json`. If a run is interrupted, re-launching Claude Code in this directory automatically resumes from the last completed step.

<br>

## Design Principles

| Principle | Implementation |
|:----------|:---------------|
| **Quality over speed** | Each step runs thoroughly; no shortcuts |
| **Non-blocking progress** | Missing images or data-viz render as placeholders, never block the pipeline |
| **Graceful recovery** | Each step retries up to 2× before escalating to the user |
| **Human in the loop** | Two approval gates ensure the human stays in control of narrative direction |
| **Preserve user work** | Gate rejections never delete existing artifacts |
| **Single-file output** | The final deliverable is one portable HTML file — no server required |

<br>

## Built With

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — AI agent orchestration
- [Scrollama](https://github.com/russellsamora/scrollama) — Scroll-triggered animation
- Inspired by visual storytelling from the [Financial Times](https://ig.ft.com/) and [The Pudding](https://pudding.cool/)

<br>

---

<div align="center">

**[See It Live](https://lowtidebuild.github.io/visual-story-creator/)**

Made with Claude Code.

</div>
