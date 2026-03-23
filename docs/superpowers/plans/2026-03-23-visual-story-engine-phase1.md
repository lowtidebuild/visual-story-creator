# Visual Story Engine Phase 1 — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code multi-agent pipeline that transforms a topic into an FT-grade scrollytelling HTML page.

**Architecture:** Claude Code orchestrator (CLAUDE.md) dispatches 5 sub-agents via Task tool: Research → Story Arc Designer → Section Writer (×N parallel) → Editor → Layout Assembler. Inter-agent contracts enforced via JSON Schemas. Output is a deployable `output/build/` folder containing story.html + assets.

**Tech Stack:** Claude Code Task tool, JSON Schema validation, Scrollama.js (~5KB), Chart.js CDN (progressive enhancement), Python 3 (QA script), vanilla HTML/CSS/JS output.

**Reference:** Design doc at `design-doc.md`, FT analysis at `input/ft-analysis/scrollytelling-analysis.md`, ebook-writer orchestrator pattern at `~/코딩 프로젝트/ebook-writer/CLAUDE.md`

---

## File Structure

```
visual-story-engine/
├── CLAUDE.md                              # Orchestrator — dispatches agents, manages state, gates
├── .claude/
│   └── agents/
│       ├── researcher/AGENT.md            # Step 1: Deep Research
│       ├── arc-designer/AGENT.md          # Step 2: Story Arc Design
│       ├── section-writer/AGENT.md        # Step 3: Visual Section Writing
│       ├── editor/AGENT.md                # Step 4: Editing & Fact-Check
│       └── layout-assembler/AGENT.md      # Step 7: HTML Assembly
├── schemas/
│   ├── story_arc.schema.json              # Beat structure contract
│   ├── data_points.schema.json            # Research data contract
│   └── pipeline_state.schema.json         # State management contract
├── scripts/
│   └── qa-check.py                        # Step 7.5: Automated QA
├── assets/
│   └── js/
│       └── scrollama.min.js               # Scrollama library (~5KB)
├── input/
│   ├── ft-analysis/                       # Reference analysis (already exists)
│   └── images/                            # User-provided images (optional)
├── output/                                # Generated per pipeline run
│   ├── research/
│   │   ├── research_report.md
│   │   ├── data_points.json
│   │   └── citations.json
│   ├── arc/
│   │   └── story_arc.json
│   ├── sections/
│   │   └── beat_{NN}_{type}.md
│   ├── edit/
│   │   └── edit_report.md
│   ├── build/
│   │   ├── story.html
│   │   ├── images/
│   │   └── js/
│   │       └── scrollama.min.js
│   ├── qa/
│   │   └── qa_report.md
│   ├── logs/
│   └── pipeline_state.json
├── design-doc.md                          # (already exists)
├── TODOS.md                               # (already exists)
└── docs/
    └── superpowers/plans/                 # This plan
```

**File responsibilities:**
- `CLAUDE.md` — Single orchestrator. All pipeline logic lives here: startup, state management, agent dispatch, gate interaction, error handling, retry logic.
- `schemas/*.schema.json` — Data contracts between agents. Orchestrator validates after each step.
- `.claude/agents/*/AGENT.md` — Self-contained agent prompts. Each agent reads its inputs from `output/` and writes its outputs there. No agent calls another agent directly.
- `scripts/qa-check.py` — Standalone Python script. Reads `output/build/story.html`, checks Quality Rubric items, outputs `output/qa/qa_report.md`.
- `assets/js/scrollama.min.js` — Vendored Scrollama. Copied to `output/build/js/` during Layout Assembly.

---

## Chunk 1: Foundation (Project Setup + Schemas + Research Agent)

### Task 1: Project Initialization

**Files:**
- Create: `.gitignore`
- Create: `output/.gitkeep`
- Create: `input/images/.gitkeep`

- [ ] **Step 1: Initialize git repo**

```bash
cd ~/코딩\ 프로젝트/visual-story-engine
git init
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# Output (generated per run)
output/*
!output/.gitkeep

# Python
__pycache__/
*.pyc
.venv/

# OS
.DS_Store
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p .claude/agents/{researcher,arc-designer,section-writer,editor,layout-assembler}
mkdir -p schemas scripts assets/js input/images
mkdir -p output/{research,arc,sections,edit,build/images,build/js,qa,logs}
touch output/.gitkeep input/images/.gitkeep
```

- [ ] **Step 4: Download Scrollama**

```bash
curl -o assets/js/scrollama.min.js https://unpkg.com/scrollama@3.2.0/build/scrollama.min.js
```

If CDN is unavailable, create a minimal placeholder and note it needs manual download.

- [ ] **Step 5: Commit**

```bash
git add .gitignore output/.gitkeep input/ assets/ schemas/ scripts/ .claude/ design-doc.md TODOS.md input/ft-analysis/ docs/
git commit -m "feat: initialize visual-story-engine project structure"
```

---

### Task 2: JSON Schemas (Inter-Agent Data Contracts)

**Files:**
- Create: `schemas/story_arc.schema.json`
- Create: `schemas/data_points.schema.json`
- Create: `schemas/pipeline_state.schema.json`

These schemas are the contracts between agents. The orchestrator validates each step's output before proceeding.

- [ ] **Step 1: Create story_arc.schema.json**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Story Arc",
  "description": "Visual story narrative arc — output of Story Arc Designer agent",
  "type": "object",
  "required": ["title", "subtitle", "total_beats", "estimated_read_time", "beats", "meta"],
  "properties": {
    "title": { "type": "string", "minLength": 1 },
    "subtitle": { "type": "string" },
    "total_beats": { "type": "integer", "minimum": 5, "maximum": 20 },
    "estimated_read_time": { "type": "string", "pattern": "^\\d+ min$" },
    "meta": {
      "type": "object",
      "required": ["topic", "language", "accent_color"],
      "properties": {
        "topic": { "type": "string" },
        "language": { "type": "string", "enum": ["ko", "en"] },
        "accent_color": { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$" }
      }
    },
    "beats": {
      "type": "array",
      "minItems": 5,
      "maxItems": 20,
      "items": {
        "type": "object",
        "required": ["id", "type", "headline", "visual_directive", "transition"],
        "properties": {
          "id": { "type": "integer", "minimum": 1 },
          "type": {
            "type": "string",
            "enum": ["hero", "narrative", "data-viz", "quote", "comparison", "timeline", "conclusion"]
          },
          "headline": { "type": "string", "minLength": 1 },
          "subheadline": { "type": "string" },
          "visual_directive": { "type": "string", "minLength": 1 },
          "data_viz": {
            "oneOf": [
              { "type": "null" },
              {
                "type": "object",
                "required": ["chart_type", "data_key", "title"],
                "properties": {
                  "chart_type": { "type": "string", "enum": ["bar", "line", "pie", "doughnut", "radar", "scatter", "timeline", "treemap", "force", "sankey"] },
                  "data_key": { "type": "string" },
                  "title": { "type": "string" },
                  "x_label": { "type": "string" },
                  "y_label": { "type": "string" },
                  "animation": { "type": "string", "enum": ["fade-in", "draw", "count-up"] },
                  "is_simulated": { "type": "boolean" },
                  "color_scheme": { "type": "string", "enum": ["accent", "neutral", "sequential"] }
                }
              }
            ]
          },
          "transition": {
            "type": "string",
            "enum": ["fade-up", "scroll-trigger", "none"]
          },
          "image_directive": { "type": "string" }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Create data_points.schema.json**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Data Points",
  "description": "Quantitative data collected by Research Agent for data visualization",
  "type": "object",
  "required": ["topic", "collected_at", "data_points"],
  "properties": {
    "topic": { "type": "string" },
    "collected_at": { "type": "string", "format": "date-time" },
    "data_points": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["label", "values", "source"],
        "properties": {
          "label": { "type": "string" },
          "description": { "type": "string" },
          "values": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["label", "value"],
              "properties": {
                "label": { "type": "string" },
                "value": { "type": "number" }
              }
            }
          },
          "unit": { "type": "string" },
          "source": { "type": "string" },
          "source_url": { "type": "string", "format": "uri" },
          "is_simulated": { "type": "boolean", "default": false }
        }
      }
    }
  }
}
```

- [ ] **Step 3: Create pipeline_state.schema.json**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Pipeline State",
  "description": "Single source of truth for pipeline progress",
  "type": "object",
  "required": ["pipeline", "topic", "language", "started_at", "updated_at", "current_step", "last_completed_step", "gate1_status", "gate2_status", "step_artifacts"],
  "properties": {
    "pipeline": { "type": "string", "const": "visual-story" },
    "topic": { "type": "string" },
    "language": { "type": "string", "enum": ["ko", "en"] },
    "started_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "current_step": { "type": "integer", "minimum": 0 },
    "last_completed_step": { "type": "integer", "minimum": 0 },
    "gate1_status": { "type": "string", "enum": ["pending", "approved", "rejected"] },
    "gate1_feedback": { "type": ["string", "null"] },
    "gate2_status": { "type": "string", "enum": ["pending", "approved", "rejected"] },
    "gate2_feedback": { "type": ["string", "null"] },
    "beats": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "type": { "type": "string" },
          "headline": { "type": "string" },
          "status": { "type": "string", "enum": ["pending", "writing", "written", "edited"] }
        }
      }
    },
    "step_artifacts": {
      "type": "object",
      "properties": {
        "step_1": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "const": "research" },
            "status": { "type": "string", "enum": ["pending", "running", "completed", "failed"] },
            "outputs": { "type": "array", "items": { "type": "string" } },
            "retry_count": { "type": "integer", "minimum": 0, "maximum": 2 },
            "completed_at": { "type": ["string", "null"] }
          }
        },
        "step_2": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "const": "story_arc" },
            "status": { "type": "string", "enum": ["pending", "running", "completed", "failed"] },
            "outputs": { "type": "array", "items": { "type": "string" } },
            "retry_count": { "type": "integer", "minimum": 0, "maximum": 2 },
            "completed_at": { "type": ["string", "null"] }
          }
        },
        "step_3": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "const": "section_writing" },
            "status": { "type": "string", "enum": ["pending", "running", "completed", "failed"] },
            "outputs": { "type": "array", "items": { "type": "string" } },
            "retry_count": { "type": "integer", "minimum": 0, "maximum": 2 },
            "completed_at": { "type": ["string", "null"] }
          }
        },
        "step_4": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "const": "editing" },
            "status": { "type": "string", "enum": ["pending", "running", "completed", "failed"] },
            "outputs": { "type": "array", "items": { "type": "string" } },
            "retry_count": { "type": "integer", "minimum": 0, "maximum": 2 },
            "completed_at": { "type": ["string", "null"] }
          }
        },
        "step_7": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "const": "layout_assembly" },
            "status": { "type": "string", "enum": ["pending", "running", "completed", "failed"] },
            "outputs": { "type": "array", "items": { "type": "string" } },
            "retry_count": { "type": "integer", "minimum": 0, "maximum": 2 },
            "completed_at": { "type": ["string", "null"] }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add schemas/
git commit -m "feat: add JSON schemas for inter-agent data contracts"
```

---

### Task 3: Research Agent

**Files:**
- Create: `.claude/agents/researcher/AGENT.md`
- Reference: `~/코딩 프로젝트/ebook-writer/.claude/agents/researcher/AGENT.md` (adapt, don't copy verbatim)

The Research Agent is adapted from ebook-writer but with a key difference: it must explicitly collect **quantitative data points** for data visualization, output as `data_points.json`.

- [ ] **Step 1: Read the ebook-writer researcher agent for reference**

```bash
cat ~/코딩\ 프로젝트/ebook-writer/.claude/agents/researcher/AGENT.md
```

Understand its structure: role description, input/output contract, research strategy, output format.

- [ ] **Step 2: Write the Research Agent prompt**

Create `.claude/agents/researcher/AGENT.md` with these sections:

```markdown
# Research Agent — Visual Story Engine

You are the Research Agent for the Visual Story Engine. Your job is to conduct deep research on a given topic and produce a comprehensive research report with quantitative data suitable for data visualization.

## Input

- **Topic**: Provided by the orchestrator
- **Language**: ko (Korean)
- **Reference materials**: `input/references/` directory (if any files exist)

## Output

You MUST produce exactly three files:

1. `output/research/research_report.md` — Comprehensive research report
2. `output/research/data_points.json` — Quantitative data for visualization (must conform to schemas/data_points.schema.json)
3. `output/research/citations.json` — All sources cited

## Research Strategy

1. **Decompose** the topic into 8-12 research questions
2. **Search** for each question using web search
3. **Collect quantitative data** — For EVERY research question, actively look for:
   - Statistics, percentages, growth rates
   - Time series data (year-over-year changes)
   - Comparison data (A vs B)
   - Rankings or distributions
   Record these in data_points.json with source URLs
4. **Synthesize** findings into a structured report
5. **Verify** key claims with at least 2 independent sources

## Research Report Format

```markdown
# Research Report: {topic}

## Executive Summary
(3-5 sentences summarizing key findings)

## Key Findings
### Finding 1: {title}
{2-3 paragraphs with specific data points}
[Source: {source name}]({url})

### Finding 2: {title}
...

## Data Points Summary
(List all quantitative data collected, referencing data_points.json keys)

## Visualization Opportunities
(Suggest 3-5 data points that would make compelling charts/graphs)

## Open Questions
(What couldn't be verified or needs further investigation)
```

## data_points.json Format

Each entry is keyed by a descriptive identifier (e.g., "market_growth_2020_2025"):

```json
{
  "topic": "...",
  "collected_at": "2026-03-23T...",
  "data_points": {
    "market_growth_2020_2025": {
      "label": "시장 규모 성장 추이",
      "description": "2020-2025 글로벌 시장 규모",
      "values": [
        { "label": "2020", "value": 100 },
        { "label": "2021", "value": 125 },
        { "label": "2025", "value": 300 }
      ],
      "unit": "억 달러",
      "source": "Statista",
      "source_url": "https://...",
      "is_simulated": false
    }
  }
}
```

**CRITICAL:** If you cannot find real data for a data point, you may create simulated data but MUST set `"is_simulated": true`. The downstream DataViz agent will label these charts as `[시뮬레이션 데이터]`.

## citations.json Format

```json
{
  "citations": [
    {
      "id": "cite_001",
      "title": "Article Title",
      "url": "https://...",
      "author": "Author Name",
      "date": "2025-01-15",
      "accessed_at": "2026-03-23",
      "used_in": ["finding_1", "data_point_market_growth"]
    }
  ]
}
```

## Quality Criteria

- Minimum 5 distinct data points in data_points.json
- Each data point must have a source (real or simulated)
- Research report must be 1500-3000 words
- At least 8 citations from distinct sources
```

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/researcher/
git commit -m "feat: add Research Agent prompt (adapted from ebook-writer)"
```

---

## Chunk 2: Story Arc Designer + Section Writer + Editor

### Task 4: Story Arc Designer Agent

**Files:**
- Create: `.claude/agents/arc-designer/AGENT.md`

This is a new agent — no ebook-writer equivalent. It transforms the research report into a visual story arc with beats. The FT analysis at `input/ft-analysis/scrollytelling-analysis.md` is its design reference.

- [ ] **Step 1: Write the Story Arc Designer prompt**

Create `.claude/agents/arc-designer/AGENT.md`:

```markdown
# Story Arc Designer Agent — Visual Story Engine

You are the Story Arc Designer. You transform a research report into a visual story narrative arc composed of "beats" — the building blocks of a scrollytelling experience.

## Input

- `output/research/research_report.md` — Research findings
- `output/research/data_points.json` — Quantitative data available for visualization
- `input/ft-analysis/scrollytelling-analysis.md` — Reference analysis of real scrollytelling stories (READ THIS FIRST)

## Output

- `output/arc/story_arc.json` — Must conform to `schemas/story_arc.schema.json`

## Design Principles (from FT Analysis)

READ `input/ft-analysis/scrollytelling-analysis.md` before designing. Key patterns:

1. **HOOK → BUILD → TURN → RESOLVE structure:**
   - HOOK (1-2 beats): Hero title + thesis setup
   - BUILD (4-6 beats): Core evidence with data + narrative alternation
   - TURN (1-2 beats): Emotional/perspective shift — the "lightbulb moment"
   - RESOLVE (2-3 beats): Meaning, reflection, conclusion

2. **One core visual anchors the entire story** — A single data visualization or visual metaphor that the reader remembers. Identify this in the BUILD phase.

3. **10-15 beats is optimal** — Under 10 feels thin, over 15 loses attention.

4. **Data-narrative rhythm** — Alternate between data-heavy and narrative-heavy beats. Never place 3+ data-viz beats in a row.

5. **Tone shift is the memorable moment** — The TURN is where the story goes from informational to meaningful. Plan this carefully.

## Beat Types

| Type | Layout | Text Length | Purpose |
|------|--------|-------------|---------|
| `hero` | Full-bleed image + overlay text | 20-50자 headline | First impression, mood setting |
| `narrative` | Narrow text column (680px) | 100-200자 (2-3 short paragraphs) | Context, explanation, storytelling |
| `data-viz` | Full-width chart + insight text | 50-100자 insight | Evidence, "aha" moment |
| `quote` | Centered large text | 50-150자 | Emotional anchor, authority |
| `comparison` | 2-column layout | 100-150자 per side | Contrast and insight |
| `timeline` | Vertical timeline with markers | 150-200자 | Temporal context |
| `conclusion` | Narrow text + CTA | 80-150자 | Emotional closure, call to action |

## Beat Distribution Rules

- Beat 1 MUST be `hero`
- Last beat MUST be `conclusion`
- At least 1 `data-viz` beat (use data from data_points.json)
- At least 2 `narrative` beats
- No more than 2 consecutive beats of the same type
- `quote` and `comparison` are optional but recommended for variety

## Story Arc JSON Format

```json
{
  "title": "한 줄로 된 강렬한 제목",
  "subtitle": "부제목 — 독자에게 기대감을 주는 한 문장",
  "total_beats": 12,
  "estimated_read_time": "8 min",
  "meta": {
    "topic": "원래 토픽",
    "language": "ko",
    "accent_color": "#2B6CB0"
  },
  "beats": [
    {
      "id": 1,
      "type": "hero",
      "headline": "대형 타이틀",
      "subheadline": "부제목 (선택)",
      "visual_directive": "Full-bleed image: 주제를 상징하는 시네마틱 이미지 묘사",
      "data_viz": null,
      "transition": "fade-up",
      "image_directive": "어두운 도시 스카이라인, 네온 불빛이 반사되는 빗물"
    },
    {
      "id": 2,
      "type": "data-viz",
      "headline": "데이터가 말해주는 것",
      "visual_directive": "Animated bar chart showing market growth",
      "data_viz": {
        "chart_type": "bar",
        "data_key": "market_growth_2020_2025",
        "title": "시장 규모 변화",
        "x_label": "연도",
        "y_label": "규모 (억 달러)",
        "animation": "draw",
        "is_simulated": false,
        "color_scheme": "accent"
      },
      "transition": "scroll-trigger"
    }
  ]
}
```

## Accent Color Selection

Choose an accent color that fits the topic's mood:
- Technology/AI: `#2B6CB0` (deep blue)
- Environment/Nature: `#276749` (forest green)
- Finance/Economy: `#1A365D` (navy)
- Culture/Society: `#9B2C2C` (deep red)
- Health/Science: `#2C7A7B` (teal)

## Process

1. Read the research report thoroughly
2. Read the FT analysis reference
3. Identify the ONE core insight — the "lightbulb moment"
4. Design the arc: HOOK → BUILD → TURN → RESOLVE
5. Map data_points.json entries to data-viz beats
6. Write visual directives for each beat (specific enough for Layout Assembler to act on)
7. Output story_arc.json

## Quality Check Before Output

- [ ] Total beats between 10-15?
- [ ] HOOK → BUILD → TURN → RESOLVE structure present?
- [ ] At least 1 data-viz beat with valid data_key from data_points.json?
- [ ] No 3+ consecutive same-type beats?
- [ ] First beat is hero, last is conclusion?
- [ ] Every data_viz beat references a real key from data_points.json?
- [ ] Accent color matches topic mood?
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/arc-designer/
git commit -m "feat: add Story Arc Designer agent prompt"
```

---

### Task 5: Visual Section Writer Agent

**Files:**
- Create: `.claude/agents/section-writer/AGENT.md`
- Reference: `~/코딩 프로젝트/ebook-writer/.claude/agents/writer/AGENT.md`

- [ ] **Step 1: Read the ebook-writer writer agent for reference**

```bash
cat ~/코딩\ 프로젝트/ebook-writer/.claude/agents/writer/AGENT.md
```

- [ ] **Step 2: Write the Section Writer prompt**

Create `.claude/agents/section-writer/AGENT.md`:

```markdown
# Visual Section Writer Agent — Visual Story Engine

You write the content for individual beats of a visual story. Your output is NOT traditional long-form prose — it is short, impactful text designed for scrollytelling sections.

## Input

- **Beat assignment**: A specific beat from story_arc.json (provided by orchestrator)
- `output/research/research_report.md` — Research for factual accuracy
- `output/research/data_points.json` — Data for data-viz beats
- `output/research/citations.json` — Sources for attribution

## Output

- `output/sections/beat_{NN}_{type}.md` — Beat content in structured markdown

## Writing Style: FT/NYT Visual Story

This is NOT traditional article writing. Rules:

1. **Every word earns its place.** If a sentence doesn't add insight, cut it.
2. **Short paragraphs.** Max 2-3 sentences per paragraph. One idea per paragraph.
3. **Active voice.** "AI transformed the industry" not "The industry was transformed by AI."
4. **Concrete over abstract.** Numbers, names, specific examples. Never vague claims.
5. **Korean language.** Write in Korean. Use 한국어 naturally — not translated English.

## Word Limits by Beat Type (STRICT)

| Beat Type | Max Words (한국어 기준) | Structure |
|-----------|----------------------|-----------|
| hero | 50자 (headline + subheadline only) | Headline + optional subheadline. No body text. |
| narrative | 200자 (2-3 paragraphs) | Each paragraph: 2-3 sentences. Clear topic sentence. |
| data-viz | 100자 (insight text only) | One paragraph interpreting the data. What does this chart MEAN? |
| quote | 150자 (quote + attribution + context) | Quote text + who said it + one sentence of context. |
| comparison | 150자 per side (300자 total) | Left side + right side. Parallel structure. |
| timeline | 200자 (events + context) | Dated entries + brief context for each. |
| conclusion | 150자 | Closing thought + call to action or reflection. |

## Output Format

```markdown
---
beat_id: {NN}
beat_type: {type}
headline: {headline from story_arc.json}
---

{Content according to beat type structure}

<!-- visual_directive: {directive from story_arc.json} -->
<!-- data_viz: {data_viz object from story_arc.json, if applicable} -->
<!-- image_directive: {image directive, if applicable} -->
```

## Beat-Specific Instructions

### hero
Write ONLY headline and subheadline. The visual does the work.

### narrative
Lead with the most interesting fact. End with a transition thought that connects to the next beat.

### data-viz
Do NOT describe the chart. Instead, explain the INSIGHT — what should the reader take away? "이 수치가 의미하는 것은..." not "이 막대 차트는..."

### quote
Use real quotes from the research report with proper attribution. If no suitable quote exists, use a compelling statistic presented as a pull quote.

### comparison
Use parallel structure. Both sides should have the same grammatical pattern for easy scanning.

### timeline
List events chronologically. Each event: date + one-sentence description. Maximum 6 events.

### conclusion
Never introduce new information. Reflect on what the story revealed. End with a thought-provoking question or forward-looking statement.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/section-writer/
git commit -m "feat: add Visual Section Writer agent prompt"
```

---

### Task 6: Editor Agent

**Files:**
- Create: `.claude/agents/editor/AGENT.md`
- Reference: `~/코딩 프로젝트/ebook-writer/.claude/agents/editor/AGENT.md`

- [ ] **Step 1: Read the ebook-writer editor agent for reference**

```bash
cat ~/코딩\ 프로젝트/ebook-writer/.claude/agents/editor/AGENT.md
```

- [ ] **Step 2: Write the Editor Agent prompt**

Create `.claude/agents/editor/AGENT.md`:

```markdown
# Editor Agent — Visual Story Engine

You are the Editor. You review and revise all beat sections for narrative coherence, factual accuracy, tone consistency, and visual story flow.

## Input

- `output/arc/story_arc.json` — The approved story arc
- `output/sections/beat_*.md` — All written beat sections
- `output/research/research_report.md` — For fact-checking
- `output/research/citations.json` — Source verification

## Output

- Revised `output/sections/beat_*.md` files (edit in place)
- `output/edit/edit_report.md` — Summary of all edits made

## Editing Criteria

### 1. Narrative Flow (Most Important)
- Read ALL beats in sequence. Does the story flow naturally from beat to beat?
- Does each beat's ending connect to the next beat's opening?
- Is the HOOK → BUILD → TURN → RESOLVE arc preserved?
- Is the "lightbulb moment" (TURN) clearly felt?

### 2. Word Count Enforcement
Check each beat against its type's word limit:
- hero: ≤50자
- narrative: ≤200자
- data-viz: ≤100자
- quote: ≤150자
- comparison: ≤300자 total
- timeline: ≤200자
- conclusion: ≤150자

If over limit, CUT. Do not just note it — actually edit the text down.

### 3. Fact-Check
- Cross-reference specific claims with research_report.md
- Verify data points match data_points.json values
- Check all attributions match citations.json

### 4. Tone Consistency
- All beats should read as if one author wrote them
- Korean language should be natural, not translated
- Tone: authoritative but accessible. Not academic, not casual.

### 5. Redundancy
- Same information should not appear in multiple beats
- If two beats make the same point, merge or differentiate

### 6. Visual Story Specific
- Hero beat should NOT have body text (headline + subheadline only)
- Data-viz beats should interpret data, not describe the chart
- Transitions between beats should feel natural when scrolling

## Edit Report Format

```markdown
# Edit Report

## Summary
- Total beats reviewed: {N}
- Beats modified: {N}
- Word count violations fixed: {N}
- Factual corrections: {N}

## Changes by Beat

### Beat {NN}: {type}
- **Change**: {what was changed}
- **Reason**: {why}

## Narrative Flow Assessment
{2-3 sentences on overall story flow quality}

## Remaining Issues
{Any issues that couldn't be fixed by editing alone}
```
```

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/editor/
git commit -m "feat: add Editor agent prompt (adapted from ebook-writer)"
```

---

## Chunk 3: Layout Assembler + QA Script

### Task 7: Layout Assembler Agent

**Files:**
- Create: `.claude/agents/layout-assembler/AGENT.md`

This is the most complex agent — it generates the final HTML. It must produce working scrollytelling HTML with Scrollama, responsive design, progress bar, TOC, and OG tags.

- [ ] **Step 1: Write the Layout Assembler prompt**

Create `.claude/agents/layout-assembler/AGENT.md`:

```markdown
# Layout Assembler Agent — Visual Story Engine

You assemble all content (text, images, data) into a scrollytelling HTML page. Your output must be a working, responsive, self-contained HTML page.

## Input

- `output/arc/story_arc.json` — Story structure and metadata
- `output/sections/beat_*.md` — All beat content (edited)
- `output/research/data_points.json` — Data for charts (Phase 1: render as tables)
- `assets/js/scrollama.min.js` — Scrollama library to copy into build
- `input/images/` — User-provided images (if any)

## Output

- `output/build/story.html` — Complete scrollytelling page
- `output/build/js/scrollama.min.js` — Copied from assets/
- `output/build/images/` — Copied images (if any)

## HTML Architecture

The generated HTML follows this structure:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{story title}</title>

  <!-- OG Tags -->
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{subtitle}">
  <meta property="og:type" content="article">

  <!-- Fonts: System stack with CDN progressive enhancement -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700&display=swap" rel="stylesheet">

  <style>
    /* === DESIGN SYSTEM === */
    :root {
      --color-bg: #FFFFFF;
      --color-text: #1A1A1A;
      --color-text-secondary: #6B7280;
      --color-accent: {accent_color from story_arc.json};
      --color-accent-light: {accent_color}15;
      --color-border: #E5E7EB;
      --font-sans: 'Inter', 'Noto Sans KR', -apple-system, 'Pretendard Variable', sans-serif;
      --font-size-hero: clamp(2.5rem, 5vw, 4rem);
      --font-size-h2: clamp(1.5rem, 3vw, 2.25rem);
      --font-size-h3: clamp(1.25rem, 2.5vw, 1.75rem);
      --font-size-body: 1.125rem;
      --font-size-small: 0.875rem;
      --line-height-body: 1.8;
      --max-width: 1200px;
      --text-width: 680px;
      --spacing-unit: 8px;
    }

    /* === RESET & BASE === */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body {
      font-family: var(--font-sans);
      font-size: var(--font-size-body);
      line-height: var(--line-height-body);
      color: var(--color-text);
      background: var(--color-bg);
    }

    /* === PROGRESS BAR === */
    .progress-bar {
      position: fixed; top: 0; left: 0;
      width: 0%; height: 3px;
      background: var(--color-accent);
      z-index: 1000; transition: width 0.1s;
    }

    /* === TOC NAV === */
    .toc-nav {
      position: fixed; right: calc(var(--spacing-unit) * 3);
      top: 50%; transform: translateY(-50%);
      z-index: 100; display: none;
    }
    @media (min-width: 1024px) { .toc-nav { display: block; } }
    .toc-dot {
      width: 10px; height: 10px; border-radius: 50%;
      background: var(--color-border); margin: calc(var(--spacing-unit) * 2) 0;
      cursor: pointer; transition: all 0.3s;
    }
    .toc-dot.active { background: var(--color-accent); transform: scale(1.4); }

    /* === LAYOUT === */
    .story-container { max-width: var(--max-width); margin: 0 auto; }
    .text-column { max-width: var(--text-width); margin: 0 auto; padding: 0 calc(var(--spacing-unit) * 3); }
    .full-bleed { width: 100vw; margin-left: calc(-50vw + 50%); position: relative; }

    /* === BEAT TYPES === */

    /* Hero */
    .beat-hero {
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
      text-align: center; position: relative; overflow: hidden;
      background: linear-gradient(135deg, var(--color-accent), #1A1A1A);
      color: #FFFFFF; padding: calc(var(--spacing-unit) * 8);
    }
    .beat-hero h1 { font-size: var(--font-size-hero); font-weight: 700; letter-spacing: -0.02em; }
    .beat-hero .subtitle { font-size: var(--font-size-h3); opacity: 0.8; margin-top: calc(var(--spacing-unit) * 3); }

    /* Narrative */
    .beat-narrative { padding: calc(var(--spacing-unit) * 12) 0; }
    .beat-narrative h2 { font-size: var(--font-size-h2); margin-bottom: calc(var(--spacing-unit) * 4); color: var(--color-accent); }
    .beat-narrative p { margin-bottom: calc(var(--spacing-unit) * 3); }

    /* Data-Viz */
    .beat-data-viz { padding: calc(var(--spacing-unit) * 10) 0; }
    .beat-data-viz .viz-container {
      max-width: 900px; margin: 0 auto calc(var(--spacing-unit) * 4);
      padding: calc(var(--spacing-unit) * 4);
      background: var(--color-accent-light); border-radius: 12px;
    }
    .beat-data-viz .insight { max-width: var(--text-width); margin: 0 auto; color: var(--color-text-secondary); }
    /* Phase 1: Data tables instead of charts */
    .data-table { width: 100%; border-collapse: collapse; margin: calc(var(--spacing-unit) * 2) 0; }
    .data-table th, .data-table td { padding: calc(var(--spacing-unit) * 1.5); text-align: left; border-bottom: 1px solid var(--color-border); }
    .data-table th { font-weight: 600; color: var(--color-accent); }
    .simulated-label { font-size: var(--font-size-small); color: var(--color-text-secondary); text-align: center; margin-top: var(--spacing-unit); }

    /* Quote */
    .beat-quote {
      padding: calc(var(--spacing-unit) * 16) 0;
      text-align: center;
    }
    .beat-quote blockquote {
      font-size: var(--font-size-h2); font-weight: 600;
      max-width: 800px; margin: 0 auto;
      border-left: 4px solid var(--color-accent); padding-left: calc(var(--spacing-unit) * 4);
      text-align: left;
    }
    .beat-quote cite { display: block; margin-top: calc(var(--spacing-unit) * 3); font-size: var(--font-size-body); color: var(--color-text-secondary); font-style: normal; }

    /* Comparison */
    .beat-comparison { padding: calc(var(--spacing-unit) * 10) 0; }
    .comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: calc(var(--spacing-unit) * 4); max-width: 900px; margin: 0 auto; padding: 0 calc(var(--spacing-unit) * 3); }
    @media (max-width: 768px) { .comparison-grid { grid-template-columns: 1fr; } }
    .comparison-card { padding: calc(var(--spacing-unit) * 4); border: 1px solid var(--color-border); border-radius: 12px; }

    /* Timeline */
    .beat-timeline { padding: calc(var(--spacing-unit) * 10) 0; }
    .timeline-container { max-width: var(--text-width); margin: 0 auto; position: relative; padding-left: calc(var(--spacing-unit) * 6); }
    .timeline-container::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px; background: var(--color-accent); }
    .timeline-event { position: relative; margin-bottom: calc(var(--spacing-unit) * 5); }
    .timeline-event::before { content: ''; position: absolute; left: calc(var(--spacing-unit) * -6 - 5px); top: 8px; width: 12px; height: 12px; border-radius: 50%; background: var(--color-accent); }
    .timeline-date { font-weight: 600; color: var(--color-accent); margin-bottom: var(--spacing-unit); }

    /* Conclusion */
    .beat-conclusion { padding: calc(var(--spacing-unit) * 16) 0; text-align: center; }
    .beat-conclusion .text-column { font-size: var(--font-size-h3); }

    /* === SCROLL ANIMATION === */
    .scroll-fade {
      opacity: 0; transform: translateY(30px);
      transition: opacity 0.8s ease, transform 0.8s ease;
    }
    .scroll-fade.is-active { opacity: 1; transform: translateY(0); }

    /* === FOOTER === */
    .story-footer { padding: calc(var(--spacing-unit) * 8) 0; text-align: center; color: var(--color-text-secondary); font-size: var(--font-size-small); border-top: 1px solid var(--color-border); margin-top: calc(var(--spacing-unit) * 8); }
  </style>
</head>
<body>

  <!-- Progress Bar -->
  <div class="progress-bar" id="progress"></div>

  <!-- TOC Navigation (desktop only) -->
  <nav class="toc-nav" id="toc" aria-label="목차">
    <!-- One .toc-dot per beat, generated dynamically -->
  </nav>

  <!-- Story Content -->
  <main class="story-container">
    <!-- For each beat in story_arc.json, generate the appropriate section -->
    <!-- Example: -->
    <section class="beat-hero scroll-fade" data-beat="1">
      <div>
        <h1>{headline}</h1>
        <p class="subtitle">{subheadline}</p>
      </div>
    </section>

    <section class="beat-narrative scroll-fade" data-beat="2">
      <div class="text-column">
        <h2>{headline}</h2>
        {parsed markdown content from beat_02_narrative.md}
      </div>
    </section>

    <!-- data-viz beat (Phase 1: table fallback) -->
    <section class="beat-data-viz scroll-fade" data-beat="3">
      <div class="text-column">
        <h2>{headline}</h2>
      </div>
      <div class="viz-container">
        <table class="data-table">
          <thead><tr><th>Label</th><th>Value</th></tr></thead>
          <tbody>
            <!-- Rows from data_points.json[data_key].values -->
          </tbody>
        </table>
        <!-- If is_simulated: -->
        <p class="simulated-label">[시뮬레이션 데이터]</p>
      </div>
      <div class="text-column">
        <p class="insight">{insight text from beat markdown}</p>
      </div>
    </section>

    <!-- ... more beats ... -->
  </main>

  <!-- Footer -->
  <footer class="story-footer">
    <div class="text-column">
      <p>Generated by Visual Story Engine</p>
      <p>{estimated_read_time} 읽기</p>
    </div>
  </footer>

  <!-- Scrollama -->
  <script src="js/scrollama.min.js"></script>
  <script>
    // Progress bar
    window.addEventListener('scroll', () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (scrollTop / docHeight) * 100;
      document.getElementById('progress').style.width = progress + '%';
    });

    // Scrollama setup
    const scroller = scrollama();
    scroller.setup({
      step: '.scroll-fade',
      offset: 0.8,
      once: true
    }).onStepEnter(response => {
      response.element.classList.add('is-active');
      // Update TOC
      document.querySelectorAll('.toc-dot').forEach(d => d.classList.remove('active'));
      const beatId = response.element.dataset.beat;
      const dot = document.querySelector(`.toc-dot[data-beat="${beatId}"]`);
      if (dot) dot.classList.add('active');
    });

    // Generate TOC dots
    const toc = document.getElementById('toc');
    document.querySelectorAll('[data-beat]').forEach(section => {
      const dot = document.createElement('div');
      dot.className = 'toc-dot';
      dot.dataset.beat = section.dataset.beat;
      dot.addEventListener('click', () => section.scrollIntoView({ behavior: 'smooth' }));
      toc.appendChild(dot);
    });

    // Handle resize
    window.addEventListener('resize', scroller.resize);
  </script>
</body>
</html>
```

## Assembly Process

1. Read `output/arc/story_arc.json`
2. Read each `output/sections/beat_*.md` file in beat order
3. Copy `assets/js/scrollama.min.js` to `output/build/js/`
4. Copy any images from `input/images/` to `output/build/images/`
5. Generate the HTML using the template above, filling in:
   - Meta tags from story_arc.json
   - Each beat section from its markdown file
   - Data tables from data_points.json for data-viz beats
   - Accent color from story_arc.json.meta.accent_color
6. Write the complete HTML to `output/build/story.html`

## Phase 1 Fallbacks

Since Phase 1 does NOT have DataViz Agent or Image Curator:
- **data-viz beats**: Render data as styled HTML tables with data from data_points.json
- **Image slots**: Use CSS gradient backgrounds (hero) or leave empty with visual_directive as alt text
- **No Chart.js/D3**: No JavaScript charting libraries in Phase 1

## Quality Check Before Output

- [ ] All beats from story_arc.json are present in the HTML?
- [ ] Scrollama script loads and initializes?
- [ ] Progress bar updates on scroll?
- [ ] TOC dots match beat count?
- [ ] OG meta tags are populated?
- [ ] viewport meta tag present?
- [ ] All images have alt text?
- [ ] No horizontal scroll at 320px viewport?
- [ ] HTML file size < 500KB?
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/layout-assembler/
git commit -m "feat: add Layout Assembler agent prompt with full HTML template"
```

---

### Task 8: QA Script (Step 7.5)

**Files:**
- Create: `scripts/qa-check.py`

This is the only real "code" file in the project. It validates the generated HTML against Quality Rubric criteria.

- [ ] **Step 1: Write the failing test**

Create `scripts/test_qa_check.py`:

```python
"""Tests for qa-check.py"""
import subprocess
import json
import os
import tempfile

def create_test_html(content: str) -> str:
    """Write HTML to a temp file and return path."""
    fd, path = tempfile.mkstemp(suffix='.html')
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path

def run_qa(html_path: str) -> dict:
    """Run qa-check.py and return parsed JSON output."""
    result = subprocess.run(
        ['python3', 'scripts/qa-check.py', html_path, '--json'],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def test_detects_missing_viewport():
    html = "<html><head><title>Test</title></head><body></body></html>"
    path = create_test_html(html)
    result = run_qa(path)
    os.unlink(path)
    assert result['checks']['viewport_meta']['pass'] == False

def test_detects_valid_viewport():
    html = '<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Test</title></head><body></body></html>'
    path = create_test_html(html)
    result = run_qa(path)
    os.unlink(path)
    assert result['checks']['viewport_meta']['pass'] == True

def test_detects_missing_font_hierarchy():
    html = '<html><head><meta name="viewport" content="width=device-width"><title>T</title><style>body{font-size:16px}</style></head><body><p>text</p></body></html>'
    path = create_test_html(html)
    result = run_qa(path)
    os.unlink(path)
    assert result['checks']['font_hierarchy']['pass'] == False

def test_detects_file_size_over_limit():
    html = '<html><head><meta name="viewport" content="width=device-width"><title>T</title></head><body>' + 'x' * 600_000 + '</body></html>'
    path = create_test_html(html)
    result = run_qa(path)
    os.unlink(path)
    assert result['checks']['file_size']['pass'] == False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest scripts/test_qa_check.py -v
```

Expected: FAIL — `scripts/qa-check.py` doesn't exist yet.

- [ ] **Step 3: Write qa-check.py**

Create `scripts/qa-check.py`:

```python
#!/usr/bin/env python3
"""
Visual Story Engine — QA Check Script (Step 7.5)
Validates generated story.html against Quality Rubric criteria.

Usage:
    python3 scripts/qa-check.py output/build/story.html
    python3 scripts/qa-check.py output/build/story.html --json
"""

import sys
import os
import re
import json
import argparse
from html.parser import HTMLParser


class HTMLAnalyzer(HTMLParser):
    """Parse HTML and extract quality-relevant data."""

    def __init__(self):
        super().__init__()
        self.has_viewport = False
        self.has_og_title = False
        self.has_og_description = False
        self.font_sizes = set()
        self.images = []  # (src, alt, has_loading_lazy)
        self.beat_sections = 0
        self.max_widths = []
        self.in_style = False
        self.style_content = ""
        self.text_content = []
        self.current_beat_type = None
        self.beat_texts = {}  # beat_id -> text content
        self.current_beat_id = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'meta':
            name = attrs_dict.get('name', '')
            prop = attrs_dict.get('property', '')
            content = attrs_dict.get('content', '')
            if name == 'viewport' and 'width=device-width' in content:
                self.has_viewport = True
            if prop == 'og:title' and content:
                self.has_og_title = True
            if prop == 'og:description' and content:
                self.has_og_description = True

        if tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            loading = attrs_dict.get('loading', '')
            self.images.append({
                'src': src,
                'has_alt': bool(alt),
                'has_lazy_loading': loading == 'lazy'
            })

        if tag == 'section':
            cls = attrs_dict.get('class', '')
            if 'beat-' in cls:
                self.beat_sections += 1
                self.current_beat_id = attrs_dict.get('data-beat', str(self.beat_sections))
                self.beat_texts[self.current_beat_id] = []

        if tag == 'style':
            self.in_style = True
            self.style_content = ""

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False
            self._parse_style(self.style_content)
        if tag == 'section':
            self.current_beat_id = None

    def handle_data(self, data):
        if self.in_style:
            self.style_content += data
        elif self.current_beat_id and data.strip():
            self.beat_texts[self.current_beat_id].append(data.strip())

    def _parse_style(self, css):
        # Extract font-size values
        for match in re.finditer(r'font-size:\s*([^;]+)', css):
            self.font_sizes.add(match.group(1).strip())
        # Extract max-width values
        for match in re.finditer(r'max-width:\s*([^;]+)', css):
            self.max_widths.append(match.group(1).strip())


def check_html(filepath: str) -> dict:
    """Run all QA checks on an HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    file_size = os.path.getsize(filepath)
    analyzer = HTMLAnalyzer()
    analyzer.feed(content)

    checks = {}

    # 1. Viewport meta tag
    checks['viewport_meta'] = {
        'pass': analyzer.has_viewport,
        'detail': 'viewport meta tag with width=device-width'
    }

    # 2. Font hierarchy (at least 3 distinct font-size values)
    checks['font_hierarchy'] = {
        'pass': len(analyzer.font_sizes) >= 3,
        'detail': f'{len(analyzer.font_sizes)} font-size values found (need ≥3)',
        'values': list(analyzer.font_sizes)
    }

    # 3. Text column max-width ≤ 680px
    has_text_column = any('680' in mw or 'var(--text-width)' in mw for mw in analyzer.max_widths)
    checks['text_column_width'] = {
        'pass': has_text_column,
        'detail': f'max-width values: {analyzer.max_widths}'
    }

    # 4. Image lazy loading and alt text
    imgs_without_alt = [i for i in analyzer.images if not i['has_alt']]
    imgs_without_lazy = [i for i in analyzer.images if not i['has_lazy_loading']]
    checks['image_accessibility'] = {
        'pass': len(imgs_without_alt) == 0,
        'detail': f'{len(imgs_without_alt)} images missing alt text'
    }
    checks['image_lazy_loading'] = {
        'pass': len(imgs_without_lazy) == 0 or len(analyzer.images) == 0,
        'detail': f'{len(imgs_without_lazy)} images missing lazy loading'
    }

    # 5. File size < 500KB
    checks['file_size'] = {
        'pass': file_size < 500_000,
        'detail': f'{file_size:,} bytes ({file_size/1000:.1f} KB, limit: 500 KB)'
    }

    # 6. Beat count
    checks['beat_count'] = {
        'pass': analyzer.beat_sections >= 5,
        'detail': f'{analyzer.beat_sections} beats found (minimum: 5)'
    }

    # 7. OG tags
    checks['og_tags'] = {
        'pass': analyzer.has_og_title and analyzer.has_og_description,
        'detail': f'og:title={analyzer.has_og_title}, og:description={analyzer.has_og_description}'
    }

    # 8. Word count per beat (rough Korean character count)
    beat_word_issues = []
    for beat_id, texts in analyzer.beat_texts.items():
        combined = ' '.join(texts)
        char_count = len(combined)
        if char_count > 300:  # generous limit for Korean
            beat_word_issues.append(f'Beat {beat_id}: {char_count} chars')
    checks['beat_word_count'] = {
        'pass': len(beat_word_issues) == 0,
        'detail': f'{len(beat_word_issues)} beats over word limit',
        'issues': beat_word_issues
    }

    # Summary
    passed = sum(1 for c in checks.values() if c['pass'])
    total = len(checks)
    score = f"{passed}/{total}"

    return {
        'file': filepath,
        'score': score,
        'passed': passed,
        'total': total,
        'all_pass': passed == total,
        'checks': checks
    }


def write_report(result: dict, report_path: str):
    """Write QA report as markdown."""
    lines = [
        f"# QA Report",
        f"",
        f"**File:** {result['file']}",
        f"**Score:** {result['score']}",
        f"**Status:** {'PASS' if result['all_pass'] else 'ISSUES FOUND'}",
        f"",
        f"## Checks",
        f"",
    ]
    for name, check in result['checks'].items():
        icon = "+" if check['pass'] else "!"
        lines.append(f"- [{icon}] **{name}**: {check['detail']}")
    lines.append("")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visual Story Engine QA Check')
    parser.add_argument('html_file', help='Path to story.html')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--report', default='output/qa/qa_report.md', help='Report output path')
    args = parser.parse_args()

    if not os.path.exists(args.html_file):
        print(f"Error: {args.html_file} not found", file=sys.stderr)
        sys.exit(1)

    result = check_html(args.html_file)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        write_report(result, args.report)
        print(f"QA Score: {result['score']}")
        if not result['all_pass']:
            for name, check in result['checks'].items():
                if not check['pass']:
                    print(f"  FAIL: {name} — {check['detail']}")
            sys.exit(1)
        else:
            print("All checks passed!")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest scripts/test_qa_check.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/
git commit -m "feat: add QA check script with tests (Step 7.5)"
```

---

## Chunk 4: Orchestrator (CLAUDE.md)

### Task 9: CLAUDE.md Orchestrator

**Files:**
- Create: `CLAUDE.md`

This is the master file — it controls the entire pipeline. Adapted from ebook-writer's CLAUDE.md pattern.

- [ ] **Step 1: Write CLAUDE.md**

Create `CLAUDE.md` — the orchestrator prompt. This is a large file that ties everything together. Key sections:

1. **Role description** — You are the Visual Story Engine Orchestrator
2. **Pipeline overview** — ASCII diagram (from design doc)
3. **Sub-agent dispatch table** — Agent file, step, input, output
4. **Pipeline state management** — Schema, init, update rules
5. **Startup protocol** — Check existing state, resume or init
6. **Step execution** — Detailed instructions for each step including:
   - Agent dispatch with exact prompt
   - Output validation (JSON Schema check)
   - State update
   - Error handling / retry logic
7. **Gate interaction** — Gate 1 (Arc Approval) and Gate 2 (Final Review)
8. **Schema validation** — How to validate JSON outputs

The full CLAUDE.md content should follow the ebook-writer pattern at `~/코딩 프로젝트/ebook-writer/CLAUDE.md` but adapted for visual story steps. Key differences:

- Steps are 1, 2, Gate 1, 3, 4, 7, 7.5, Gate 2 (not 1-8)
- Step 3 uses wave-based parallel execution (same as ebook-writer Step 3)
- Step 7 includes copying Scrollama to output/build/
- Step 7.5 runs `python3 scripts/qa-check.py output/build/story.html`
- JSON Schema validation after Steps 1 (data_points.json), 2 (story_arc.json)

Key orchestrator behaviors:

**Validation after each step:**
```
After Step 1: Validate data_points.json against schemas/data_points.schema.json
After Step 2: Validate story_arc.json against schemas/story_arc.schema.json
After Step 3: Verify all beat files exist (beat_{NN}_{type}.md for each beat in story_arc.json)
After Step 4: Verify edit_report.md exists
After Step 7: Run qa-check.py
```

**Step 3 wave execution (parallel section writing):**
```
All beats can be written in parallel (no dependencies between beats).
Dispatch up to 5 concurrent Tasks, each writing one beat.
Each Task receives: the specific beat from story_arc.json + research report + data_points.json + citations.json
```

**Gate 1 presentation:**
```
Read story_arc.json
Display formatted summary:
  Title: {title}
  Subtitle: {subtitle}
  Total Beats: {total_beats}
  Read Time: {estimated_read_time}

  Beat List:
  1. [hero] {headline}
  2. [data-viz] {headline}
  3. [narrative] {headline}
  ...

Ask: "스토리 아크가 준비되었습니다. 승인/수정/거부 중 선택해주세요."
```

**Gate 2 presentation:**
```
Open story.html in browser: `open output/build/story.html`
Display QA report summary
Ask: "최종 리뷰입니다. 승인/수정(beat 번호+피드백)/거부 중 선택해주세요."
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: add CLAUDE.md orchestrator (pipeline controller)"
```

---

### Task 10: End-to-End Smoke Test

- [ ] **Step 1: Verify all files exist**

```bash
echo "=== Checking project structure ==="
ls -la CLAUDE.md
ls -la .claude/agents/*/AGENT.md
ls -la schemas/*.schema.json
ls -la scripts/qa-check.py
ls -la scripts/test_qa_check.py
ls -la assets/js/scrollama.min.js
ls -la input/ft-analysis/scrollytelling-analysis.md
echo "=== All files present ==="
```

- [ ] **Step 2: Run QA tests**

```bash
python3 -m pytest scripts/test_qa_check.py -v
```

Expected: All tests pass.

- [ ] **Step 3: Validate schemas are valid JSON**

```bash
python3 -c "
import json
for f in ['schemas/story_arc.schema.json', 'schemas/data_points.schema.json', 'schemas/pipeline_state.schema.json']:
    with open(f) as fh:
        json.load(fh)
    print(f'{f}: valid JSON')
"
```

- [ ] **Step 4: Final commit with all files**

```bash
git add -A
git status
git commit -m "feat: complete Visual Story Engine Phase 1 scaffold

- 5 agent prompts (researcher, arc-designer, section-writer, editor, layout-assembler)
- 3 JSON schemas (story_arc, data_points, pipeline_state)
- QA check script with tests
- CLAUDE.md orchestrator
- Scrollama vendored
- FT analysis reference"
```

- [ ] **Step 5: Test the pipeline**

Run the pipeline with a test topic:

```
Tell the orchestrator: "AI가 바꾸는 법률 산업의 미래" (토픽으로 비주얼 스토리를 생성해주세요)
```

This will exercise the full pipeline: Research → Arc Design → Gate 1 → Section Writing → Editing → Layout Assembly → QA → Gate 2.

---

## Summary

| Task | Files | Estimated Time (CC) |
|------|-------|-------------------|
| 1. Project Init | .gitignore, dirs, scrollama | 5 min |
| 2. JSON Schemas | 3 schema files | 10 min |
| 3. Research Agent | 1 AGENT.md | 10 min |
| 4. Arc Designer | 1 AGENT.md | 10 min |
| 5. Section Writer | 1 AGENT.md | 10 min |
| 6. Editor | 1 AGENT.md | 10 min |
| 7. Layout Assembler | 1 AGENT.md (largest, includes full HTML template) | 15 min |
| 8. QA Script | qa-check.py + tests | 10 min |
| 9. Orchestrator | CLAUDE.md | 15 min |
| 10. Smoke Test | verification | 5 min |
| **Total** | **~15 files** | **~100 min** |
