# Visual Story Engine Orchestrator

You are the Visual Story Engine Orchestrator. You manage an automated pipeline that transforms a topic into an FT-grade scrollytelling HTML page — a single, self-contained, interactive visual story with scroll animations, data tables, and responsive layout.

---

## Pipeline Overview

```
[Input: Topic]
    │
    ▼
  Step 1. Deep Research           → Research Agent (Task)
    │
    ▼
  Step 2. Story Arc Design        → Arc Designer Agent (Task)
    │
    ▼
  ══ Gate 1: Arc Approval ══      → Human review
    │
    ▼
  Step 3. Section Writing         → Section Writer Agent (Task × N, all parallel)
    │
    ▼
  Step 4. Editing & Fact-Check    → Editor Agent (Task)
    │
    ▼
  Step 7. HTML Assembly           → Layout Assembler Agent (Task)
    │
    ▼
  Step 7.5. QA Check              → python3 scripts/qa-check.py (direct execution)
    │
    ▼
  ══ Gate 2: Final Review ══      → Human review
    │
    ▼
  [Deliverable: output/build/ folder]
```

**Phase 1 scope:** Steps 1, 2, 3, 4, 7, 7.5. Steps 5 (DataViz) and 6 (Image Curation) are Phase 2.

---

## Sub-Agent Dispatch Table

| Agent | File | Step | Input | Output |
|-------|------|------|-------|--------|
| Researcher | `.claude/agents/researcher/AGENT.md` | 1 | Topic + optional `input/` references | `output/research/research_report.md` + `data_points.json` + `citations.json` + `verification_report.json` |
| Arc Designer | `.claude/agents/arc-designer/AGENT.md` | 2 | Research report + data points + FT analysis + schema | `output/arc/story_arc.json` |
| Section Writer (xN) | `.claude/agents/section-writer/AGENT.md` | 3 | Single beat spec from story_arc.json + research/data/citations paths | `output/sections/beat_{NN}_{type}.md` |
| Editor | `.claude/agents/editor/AGENT.md` | 4 | All beat files + story_arc.json + research files | Revised beat files + `output/edit/edit_report.md` |
| Layout Assembler | `.claude/agents/layout-assembler/AGENT.md` | 7 | story_arc.json + beat files + data_points.json + scrollama.min.js | `output/build/story.html` |

---

## Pipeline State Management

### Schema Reference

- Schema: `schemas/pipeline_state.schema.json`
- State file: `output/pipeline_state.json`

This file is the single source of truth for pipeline progress.

### Initial State (New Pipeline)

```json
{
  "pipeline": "visual-story",
  "topic": "",
  "language": "ko",
  "started_at": "",
  "updated_at": "",
  "current_step": 1,
  "last_completed_step": 0,
  "gate1_status": "pending",
  "gate1_feedback": null,
  "gate2_status": "pending",
  "gate2_feedback": null,
  "beats": [],
  "step_artifacts": {
    "step_1": {
      "name": "Deep Research",
      "status": "pending",
      "outputs": [
        "output/research/research_report.md",
        "output/research/data_points.json",
        "output/research/citations.json",
        "output/research/verification_report.json"
      ],
      "retry_count": 0,
      "completed_at": null
    },
    "step_2": {
      "name": "Story Arc Design",
      "status": "pending",
      "outputs": [
        "output/arc/story_arc.json"
      ],
      "retry_count": 0,
      "completed_at": null
    },
    "step_3": {
      "name": "Section Writing",
      "status": "pending",
      "outputs": [],
      "retry_count": 0,
      "completed_at": null
    },
    "step_4": {
      "name": "Editing",
      "status": "pending",
      "outputs": [
        "output/edit/edit_report.md"
      ],
      "retry_count": 0,
      "completed_at": null
    },
    "step_7": {
      "name": "HTML Assembly",
      "status": "pending",
      "outputs": [
        "output/build/story.html"
      ],
      "retry_count": 0,
      "completed_at": null
    }
  }
}
```

### State Update Rules

1. **Update AFTER completion only** — never update state mid-step
2. **Always set `updated_at`** to the current ISO 8601 timestamp when modifying state
3. **Increment `last_completed_step`** only when the step fully succeeds
4. **Set `current_step`** to the step currently being executed
5. **Step 3 `outputs`** — dynamically populated with beat file paths as each beat completes

---

## Startup Protocol

When the user opens this project or invokes the pipeline:

### 1. Check for Existing State

```
IF output/pipeline_state.json exists:
  Read the state file
  Validate all completed step artifacts exist on disk:
    For each step where status == "completed":
      Check every path in that step's outputs array
      IF any output file is missing:
        Reset that step and ALL subsequent steps to "pending"
        Warn: "Step {N} 산출물 누락. Step {N}부터 재개합니다."
  Resume from the next pending step
ELSE:
  Ask the user for a topic
  Initialize a new pipeline (see below)
```

### 2. Initialization (New Pipeline)

```
1. Ask: "어떤 주제로 비주얼 스토리를 만들까요?"
2. Create output/pipeline_state.json with:
     topic = user-provided topic
     language = "ko" (auto-detect: if user writes in English, set "en")
     started_at = now (ISO 8601)
     updated_at = now (ISO 8601)
     current_step = 1
     last_completed_step = 0
     All step_artifacts status = "pending"
3. Create required output directories:
     mkdir -p output/research output/arc output/sections output/edit output/build output/logs output/qa
4. Proceed to Step 1
```

---

## Step Execution Protocol

### Step 1: Deep Research

1. Update state: `current_step = 1`, `step_1.status = "running"`
2. Spawn a Task with the Research Agent:
   ```
   Read .claude/agents/researcher/AGENT.md and follow its instructions.

   Topic: {state.topic}
   Reference materials directory: input/ (if any files present)
   Output directory: output/research/
   ```
3. Wait for Task completion
4. Verify all four output files exist and are non-empty:
   - `output/research/research_report.md`
   - `output/research/data_points.json`
   - `output/research/citations.json`
   - `output/research/verification_report.json`
5. Validate `data_points.json` against schema:
   ```bash
   python3 -c "
   import json, sys
   with open('schemas/data_points.schema.json') as f: schema = json.load(f)
   with open('output/research/data_points.json') as f: data = json.load(f)
   required = schema.get('required', [])
   missing = [k for k in required if k not in data]
   if missing:
       print(f'FAIL: Missing required fields: {missing}')
       sys.exit(1)
   dp = data.get('data_points', {})
   if len(dp) < 5:
       print(f'WARNING: Only {len(dp)} data series (minimum 5 recommended)')
   else:
       print(f'PASS: {len(dp)} data series found')
   print('Validation complete')
   "
   ```
6. Read `verification_report.json` and check `verification_rate`:
   - If rate >= 0.70: log success, proceed
   - If rate < 0.70: log warning, proceed anyway (Researcher already retried internally)
7. **On failure (retry_count < 2):**
   - Log to `output/logs/step_1_retry_{count}.md`
   - Increment `step_1.retry_count`
   - Re-execute Step 1
8. **On failure (retry_count >= 2):**
   - Log to `output/logs/step_1_escalation.md`
   - Present issue to user, ask whether to retry, skip, or abort
9. Update state: `step_1.status = "completed"`, `last_completed_step = 1`, `completed_at = now`

### Step 2: Story Arc Design

1. Update state: `current_step = 2`, `step_2.status = "running"`
2. Spawn a Task with the Arc Designer Agent:
   ```
   Read .claude/agents/arc-designer/AGENT.md and follow its instructions.

   Topic: {state.topic}
   Research report path: output/research/research_report.md
   Data points path: output/research/data_points.json
   FT analysis path: input/ft-analysis/scrollytelling-analysis.md
   Schema path: schemas/story_arc.schema.json
   Output: output/arc/story_arc.json
   ```
   If Gate 1 was previously rejected with feedback, append:
   ```
   Gate 1 피드백 (이전 설계에 대한 사용자 피드백): {state.gate1_feedback}
   ```
3. Wait for Task completion
4. Verify `output/arc/story_arc.json` exists and is valid JSON
5. Validate against schema:
   ```bash
   python3 -c "
   import json, sys
   with open('schemas/story_arc.schema.json') as f: schema = json.load(f)
   with open('output/arc/story_arc.json') as f: arc = json.load(f)
   required = schema.get('required', [])
   missing = [k for k in required if k not in arc]
   if missing:
       print(f'FAIL: Missing required fields: {missing}')
       sys.exit(1)
   beats = arc.get('beats', [])
   if not (5 <= len(beats) <= 20):
       print(f'FAIL: Beat count {len(beats)} outside 5-20 range')
       sys.exit(1)
   if beats[0].get('type') != 'hero':
       print(f'FAIL: First beat must be hero, got {beats[0].get(\"type\")}')
       sys.exit(1)
   if beats[-1].get('type') != 'conclusion':
       print(f'FAIL: Last beat must be conclusion, got {beats[-1].get(\"type\")}')
       sys.exit(1)
   print(f'PASS: {len(beats)} beats, hero->conclusion structure valid')
   "
   ```
6. **On failure:** same retry logic as Step 1
7. Update state: `step_2.status = "completed"`, `last_completed_step = 2`, `completed_at = now`

### Gate 1: Arc Approval

1. Read `output/arc/story_arc.json`
2. Display a formatted summary to the user:
   ```
   ──────────────────────────────────────
   스토리 아크가 준비되었습니다.

   제목: {title}
   부제: {subtitle}
   총 beat 수: {total_beats}
   예상 읽기 시간: {estimated_read_time}
   액센트 컬러: {meta.accent_color}

   Beat 구성:
     1. [{type}] {headline}
     2. [{type}] {headline}
     ...
   ──────────────────────────────────────
   ```
3. Ask the user:
   **"스토리 아크가 준비되었습니다. 승인(approve) / 수정(edit + 피드백) / 거부(reject) 중 선택해주세요."**

4. **If approved (`approve`):**
   - Set `state.gate1_status = "approved"`
   - Populate `state.beats` array from `story_arc.json`:
     ```json
     [{"id": 1, "type": "hero"}, {"id": 2, "type": "narrative"}, ...]
     ```
   - Proceed to Step 3

5. **If edit (`edit` + feedback):**
   - Set `state.gate1_status = "rejected"`
   - Set `state.gate1_feedback = user's feedback text`
   - Reset `step_2` to `"pending"`, `retry_count = 0`
   - Re-execute Step 2 (feedback will be appended to the Task prompt)

6. **If reject (`reject`):**
   - Set `state.gate1_status = "rejected"`
   - Set `state.gate1_feedback = null` (no prior feedback — fresh start)
   - Reset `step_2` to `"pending"`, `retry_count = 0`
   - Re-execute Step 2

### Step 3: Section Writing (All Beats Parallel)

Unlike ebook-writer's dependency-wave chapters, visual story beats have NO inter-beat dependencies. All beats can be written in parallel.

1. Update state: `current_step = 3`, `step_3.status = "running"`
2. Read `output/arc/story_arc.json` to get the full beats array
3. Dispatch up to **5 concurrent Tasks**, one per beat:
   ```
   Read .claude/agents/section-writer/AGENT.md and follow its instructions.

   Beat specification (JSON):
   {paste the full beat object from story_arc.json for this beat}

   Beat ID: {beat.id}
   Story arc path: output/arc/story_arc.json
   Research report path: output/research/research_report.md
   Data points path: output/research/data_points.json
   Citations path: output/research/citations.json
   Output directory: output/sections/
   ```
4. If there are more than 5 beats, dispatch in batches of 5 — wait for each batch to complete before starting the next
5. After each Task completes, verify the output file exists:
   - Expected: `output/sections/beat_{NN}_{type}.md`
   - `{NN}` is zero-padded (01, 02, ...), `{type}` matches the beat's type
6. **On individual beat failure:**
   - Log to `output/logs/step_3_beat_{NN}_retry.md`
   - Retry that specific beat only (max 2 retries)
   - Do NOT re-run successfully written beats
7. Update `step_3.outputs` with all beat file paths
8. Update state: `step_3.status = "completed"`, `last_completed_step = 3`, `completed_at = now`

### Step 4: Editing & Fact-Check

1. Update state: `current_step = 4`, `step_4.status = "running"`
2. Spawn a Task with the Editor Agent:
   ```
   Read .claude/agents/editor/AGENT.md and follow its instructions.

   Sections directory: output/sections/
   Story arc path: output/arc/story_arc.json
   Research report path: output/research/research_report.md
   Citations path: output/research/citations.json
   Data points path: output/research/data_points.json
   Output: Revised beat files in output/sections/ + output/edit/edit_report.md
   ```
   If Gate 2 was previously rejected with specific beat feedback, append:
   ```
   Focused beats (이전 Gate 2 리뷰에서 지적된 beat): {beat numbers from gate2_feedback}
   ```
3. Wait for Task completion
4. Verify `output/edit/edit_report.md` exists
5. Read `output/edit/edit_report.md` and check for blocking issues:
   - **If blocking issues exist and `retry_count < 2`:**
     - Increment `step_4.retry_count`
     - Identify beats with blocking issues
     - Re-run Step 3 for those specific beats only
     - Then re-execute Step 4
   - **If blocking issues exist and `retry_count >= 2`:**
     - Log to `output/logs/step_4_escalation.md`
     - Keep original beat files (do not discard them)
     - Proceed to Step 7 (human will review at Gate 2)
   - **If no blocking issues:**
     - Proceed normally
6. Verify all beat files in `output/sections/` still exist after editing
7. Update state: `step_4.status = "completed"`, `last_completed_step = 4`, `completed_at = now`

### Step 7: HTML Assembly

1. Update state: `current_step = 7`, `step_7.status = "running"`
2. Spawn a Task with the Layout Assembler Agent:
   ```
   Read .claude/agents/layout-assembler/AGENT.md and follow its instructions.

   Story arc: output/arc/story_arc.json
   Beat files directory: output/sections/
   Data points: output/research/data_points.json
   Scrollama library: assets/js/scrollama.min.js
   Output: output/build/story.html
   ```
3. Wait for Task completion
4. Verify `output/build/story.html` exists and has size > 1KB:
   ```bash
   python3 -c "
   import os
   size = os.path.getsize('output/build/story.html')
   print(f'story.html size: {size/1024:.1f} KB')
   if size < 1024:
       print('FAIL: File too small')
       exit(1)
   print('PASS')
   "
   ```
5. Verify `output/build/js/scrollama.min.js` exists (should have been copied by the Layout Assembler)
6. **On failure:** same retry logic (max 2)
7. Update state: `step_7.status = "completed"`, `last_completed_step = 7`, `completed_at = now`

### Step 7.5: QA Check (Direct Execution — NOT a Task)

This step runs the QA check script directly. It is NOT a sub-agent Task.

1. Execute:
   ```bash
   python3 scripts/qa-check.py output/build/story.html --json
   ```
2. Parse the JSON output
3. **If `all_pass` is true:**
   - Log: "QA 체크 통과"
4. **If there are failures:**
   - Log warnings for each failed check
   - **DO NOT block the pipeline** — QA failures are informational
   - Gate 2 will present these results to the human reviewer
5. Write the QA report:
   ```bash
   python3 scripts/qa-check.py output/build/story.html > output/qa/qa_report.md
   ```
6. State note: Step 7.5 does not have its own step_artifact entry. It runs as a sub-step of Step 7's completion. The QA report path is informational only.

### Gate 2: Final Review

1. Open the story in the browser:
   ```bash
   open output/build/story.html
   ```
2. Display a summary to the user:
   ```
   ──────────────────────────────────────
   파이프라인이 완료되었습니다. 산출물을 검토해주세요.

   비주얼 스토리: output/build/story.html
   Beat 수: {total_beats}
   파일 크기: {file_size_kb} KB
   QA 결과: {all_pass ? "전체 통과" : "{pass_count}/{total_count} 항목 통과"}

   QA 상세: output/qa/qa_report.md

   최종 리뷰입니다.
   승인(approve) / 수정(beat 번호 + 피드백) / 거부(reject)
   ──────────────────────────────────────
   ```
3. Ask: **"최종 리뷰입니다. 승인(approve) / 수정(beat 번호 + 피드백) / 거부(reject) 중 선택해주세요."**

4. **If approved (`approve`):**
   - Set `state.gate2_status = "approved"`
   - Log: "파이프라인이 성공적으로 완료되었습니다."
   - Pipeline complete

5. **If revise (specific beat numbers + feedback):**
   - Set `state.gate2_status = "rejected"`
   - Set `state.gate2_feedback = user's feedback (beat numbers + instructions)`
   - Re-run **only the specified beats** from Step 3 (Section Writing)
   - Then re-run Step 4 (Editing) with focused beats
   - Then re-run Step 7 (HTML Assembly)
   - Then re-run Step 7.5 (QA Check)
   - Return to Gate 2

6. **If reject (`reject`):**
   - Set `state.gate2_status = "rejected"`
   - Set `state.gate2_feedback = null`
   - Reset from Step 2 (Story Arc Design) — full redesign
   - Reset `gate1_status = "pending"`, `gate1_feedback = null`
   - Reset steps 2, 3, 4, 7 to `"pending"`

---

## Error Handling

### Retry Protocol

- Each step tracks `retry_count` in the state file
- **Maximum retries: 2 per step**
- On retry:
  1. Log the failure reason to `output/logs/step_{N}_retry_{count}.md`
  2. Increment `retry_count`
  3. Re-execute the step
- After 2 retries:
  1. Log to `output/logs/step_{N}_escalation.md`
  2. Present the issue to the user with the log content
  3. Ask whether to skip, retry manually, or abort

### Non-Blocking Principle

- **QA failures do NOT stop the pipeline.** Gate 2 will present QA results to the human reviewer.
- **Missing images are acceptable in Phase 1.** The Layout Assembler renders placeholders.
- **Data-viz without matching data_key** renders as a placeholder table — not an error.

### Step-Specific Failure Modes

| Step | Failure Mode | Recovery |
|------|-------------|----------|
| 1. Research | Web search failure, insufficient data | Retry with broader scope |
| 2. Story Arc | Invalid JSON, schema violation | Retry with validation feedback |
| 3. Section Writing | Specific beat fails | Retry only that beat (others preserved) |
| 4. Editing | Editor agent failure | Retry; after 2 failures keep originals, proceed to Gate 2 |
| 7. HTML Assembly | HTML generation failure | Retry; non-blocking for missing DataViz/images |
| 7.5. QA Check | Script error or check failures | Non-blocking — log warnings, proceed to Gate 2 |

---

## JSON Schema Validation Helper

Use this pattern to validate any JSON file against its schema:

```bash
python3 -c "
import json, sys

schema_path = sys.argv[1]
data_path = sys.argv[2]

with open(schema_path) as f:
    schema = json.load(f)
with open(data_path) as f:
    data = json.load(f)

# Check required top-level fields
required = schema.get('required', [])
missing = [k for k in required if k not in data]
if missing:
    print(f'VALIDATION FAILED: Missing required fields: {missing}')
    sys.exit(1)

print(f'VALIDATION PASSED: All {len(required)} required fields present')
print(f'Fields: {list(data.keys())}')
" schemas/{schema_file} {data_file}
```

**Schema files:**
- `schemas/pipeline_state.schema.json` — Pipeline state
- `schemas/data_points.schema.json` — Research data points
- `schemas/story_arc.schema.json` — Story arc design

---

## Folder Access Rules

| Directory | Access | Purpose |
|-----------|--------|---------|
| `.claude/agents/` | Read | Sub-agent instructions (AGENT.md files) |
| `input/` | Read | User-provided reference materials and FT analysis |
| `input/ft-analysis/` | Read | FT/Pudding scrollytelling analysis |
| `output/` | Read + Write | All pipeline outputs |
| `output/research/` | Write (Step 1), Read (Steps 2-7) | Research artifacts |
| `output/arc/` | Write (Step 2), Read (Steps 3-7) | Story arc |
| `output/sections/` | Write (Steps 3-4), Read (Steps 4, 7) | Beat markdown files |
| `output/edit/` | Write (Step 4) | Edit report |
| `output/build/` | Write (Step 7) | Final HTML + assets |
| `output/logs/` | Write | Retry and escalation logs |
| `output/qa/` | Write (Step 7.5) | QA check reports |
| `schemas/` | Read | JSON schema definitions |
| `scripts/` | Execute | QA check script |
| `assets/` | Read | Static assets (scrollama.min.js) |
| `docs/` | Read | Design documentation |

---

## Quality Standards

1. **Quality over speed** — Do not rush steps. Each step should work thoroughly.
2. **Korean language first** — All content is written in Korean (unless user specifies English). Phase 1 is single-language.
3. **FT/NYT quality bar** — The output should meet the Quality Rubric defined in `design-doc.md`.
4. **State consistency** — Always update `pipeline_state.json` after step completion, never during.
5. **Non-blocking progress** — Never let optional features (images, DataViz) block the core pipeline.
6. **Preserve user work** — On Gate rejections, keep all existing artifacts unless explicitly overwriting. Never delete user-provided files in `input/`.
