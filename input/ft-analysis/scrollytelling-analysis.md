# Scrollytelling Visual Story 구조 분석

분석일: 2026-03-23
목적: Story Arc Designer 및 Layout Assembler 에이전트 프롬프트 설계를 위한 레퍼런스
참고: ig.ft.com 직접 접근 불가하여 FT Story Playbook(공개) + 접근 가능한 고품질 스크롤리텔링 3개 분석

---

## 0. FT Story Playbook 요약 (공식 템플릿 6종)

FT가 GitHub에 공개한 6종의 스토리 템플릿 (github.com/ft-interactive/story-playbook):

| 템플릿 | 용도 | 레이아웃 | Visual Story Engine 매핑 |
|--------|------|---------|------------------------|
| **Charticle** | 차트+텍스트로 트렌드 설명 | 텍스트와 차트 교차 배치 | → `data-viz` beat 타입 |
| **Timeline Story** | 시간순 사건 정리 | 수직/수평 타임라인 | → `timeline` beat 타입 |
| **Photo Essay** | 사진 중심 스토리 | 이미지 풀블리드 + 최소 텍스트 | → `hero` + `narrative` beat |
| **Profile Cards** | 인물/엔티티 소개 | 카드 기반 그리드 | → `comparison` beat 타입 |
| **Reader Response** | 독자 반응 모음 | 인용 블록 나열 | → `quote` beat 타입 |
| **Animated Explainer** | 복잡한 개념 설명 | 비디오/애니메이션 시퀀스 | → Phase 3 고려 |

**FT의 핵심 설계 원칙:**
- "Situate readers — show them the scale, where things are happening, how they're happening"
- "Lightbulb moment" — 텍스트+비주얼 결합으로 이해의 질적 변화를 만드는 것이 목표
- Font: Sans 또는 Serif 선택 가능
- Background: Dark 또는 Light
- Text position: right, left, center
- 스크롤리텔링 포맷: "full-width images and text that unfolds as the reader scrolls"

---

## 1. The Pudding — "In Pursuit of Democracy" (2025)

**URL:** https://pudding.cool/2025/11/democracy/
**주제:** 미국 의회 기록 145년 분석 — 민주주의 위협 언급 변화
**읽기 시간:** ~15분

### Beat 구조 (23 beats)

```
Beat   타입           콘텐츠                              임팩트 요소
─────────────────────────────────────────────────────────────────────────
 1     hero           제목 + 네비게이션                    깔끔한 진입점
 2     data-viz       점 도표 (145년 의회 기록)            ★ 핵심 비주얼 — 각 점=5개 연설
 3     narrative      건국 이념 역사 맥락                  Sean Wilentz 인용
 4     timeline       1870s-1920s 투표 억압               통계: 75%→30% 투표율 하락
 5     narrative      여성 참정권 (WWI-1920)               1920 수정헌법 마일스톤
 6     comparison     대공황 시대 대립 의견                 뉴딜 찬반 대비 배치
 7     narrative      WWII 일본계 수용                    110,000+ 수용 통계
 8     quote          매카시즘 — Welch 인용                ★ "Have you no sense of decency?"
 9     timeline       시민권 운동 (1954-60s)               Brown v. Board 판결
10     data-viz       분석 전환 (절대→비율)                "Keep scrolling" 프롬프트
11     narrative      워터게이트 (1972)                    사실 기반 서술
12     narrative      이란-콘트라                          유죄 11명, 사면 6명 통계
13     narrative      9/11 + 부시 연설                    2,977명 사망 통계
14     narrative      Citizens United (2010)               정책 설명
15     narrative      2016 러시아 개입                     FBI/상원 조사 결과
16     narrative      1/6 사태 (2021)                     ★ 분석 전환점 명시
17     narrative      2024 트럼프 행정부                    행정명령 사실
18     narrative      이민 단속 (2025)                     ProPublica 인용
19     data-viz       현재 분석 요약                       핵심 발견 1문장
20     narrative      저자 개인 에세이                     ★ 1인칭 전환 — 감정적 정점
21     interactive    "점을 클릭하세요"                    독자 참여 유도
22     narrative      방법론                              투명성 확보
23     conclusion     푸터 + CTA                          후원/구독 링크
```

### 트랜지션/애니메이션
- **스크롤 트리거:** 섹션 진입 시 콘텐츠 점진적 노출
- **명시적 전환:** Beat 10에서 "Keep scrolling" 텍스트로 분석 방식 전환 신호
- **데이터 애니메이션:** 점 도표의 점들이 시간에 따라 활성화
- **전체 방향:** 선형 시간순 진행 → 가속 (초반 넓은 시대 → 후반 밀집)

### 핵심 패턴 (Story Arc Designer 참고)
1. **시간 압축:** 초기 역사는 넓게, 최근은 밀집 → 긴급성 강조
2. **단일 핵심 비주얼:** 전체 스토리를 관통하는 하나의 데이터 시각화 (점 도표)
3. **감정 전환:** Beat 16에서 분석적 → 긴급한 톤 전환, Beat 20에서 저널리즘 → 개인 에세이
4. **텍스트 비율:** 전체적으로 텍스트 중심 (~75%), 비주얼은 전략적 배치

---

## 2. The Pudding — "The Sadness of Song" (2024, AI로 제작)

**URL:** https://pudding.cool/2024/07/ai/
**주제:** 60년간 팝 음악의 감정 변화 데이터 분석
**읽기 시간:** ~10분

### Beat 구조 (15 beats)

```
Beat   타입           콘텐츠                              임팩트 요소
─────────────────────────────────────────────────────────────────────────
 1     hero           로고 + 네비게이션                    브랜드 진입
 2     hero           커버 아트 + 대형 제목                ★ AI 생성 이미지 — 분위기 설정
 3     narrative      Julia Michaels 가사 인용 + 논제     가사 예시로 즉각적 공감
 4     narrative      방법론 미리보기 (8감정 프레임워크)    데이터셋 범위: 1960-2020
 5     data-viz       라인 차트: 부정적 곡 비율 추이       ★ 핵심 발견 — 2010년대 급등
 6     data-viz       Small multiples: 감정별 궤적        순수 시각화, 텍스트 없음
 7     data-viz       장르 비교 레이더 차트                Hip Hop vs Pop 감정 지문
 8     interactive    아티스트 산점도 (검색/필터)           ★ 독자가 좋아하는 아티스트 찾기
 9     data-viz       아티스트별 레이더 차트 비교           Billie Eilish vs Ariana Grande
10     narrative      Taylor Swift 사례 연구              데이터→문화 분석 전환
11     narrative      사회/문화 요인 고찰                  400단어, 비주얼 없음
12     image          AI 생성 감정 여정 일러스트           ★ 60년 여정의 시각적 종합
13     conclusion     마무리 + 음악 인용                   주제적 북엔드
14     narrative      방법론 (NRC Emotion Lexicons)       한계점 인정
15     conclusion     푸터 + 소셜/후원                    CTA
```

### 트랜지션/애니메이션
- **점진적 공개:** 스크롤에 따른 순차적 콘텐츠 노출
- **차트 애니메이션:** 라인 차트 그리기(draw) 애니메이션
- **인터랙티브:** 산점도 필터/검색 → 독자 참여
- **반응형:** `bind:clientWidth` 기반 모바일 적응

### 핵심 패턴 (Story Arc Designer 참고)
1. **거시→미시 줌:** 전체 트렌드(Beat 5) → 장르(Beat 7) → 개별 아티스트(Beat 8-9) → 개인 사례(Beat 10)
2. **데이터-내러티브 리듬:** 데이터 클러스터(5-9) + 내러티브 클러스터(10-11) 교차
3. **순수 비주얼 beat:** Beat 6은 텍스트 0% — 시각화만으로 소통
4. **인터랙티브 정점:** 독자가 직접 탐색하는 산점도가 가장 임팩트 있는 순간

### 기술 구조 (Layout Assembler 참고)
```
Svelte 컴포넌트 구조:
App.svelte
├── Header
├── Introduction
├── Section: "Rise of Negativity"
│   ├── NegativeSongsChart (라인 차트)
│   └── EmotionChart (small multiples)
├── Section: "Artist Landscape"
│   ├── ArtistScatterplot (인터랙티브)
│   └── ArtistRadarChart
├── Conclusion
├── Methodology
└── Footer

데이터: assets/billboard.csv → D3로 클라이언트 사이드 처리
접근성: SVG에 title, desc, aria-labelledby 표준화
반응형: bind:clientWidth 기반 적응
```

---

## 3. Josh Worth — "If the Moon Were Only 1 Pixel" (2014, Webby Award)

**URL:** https://joshworth.com/dev/pixelspace/pixelspace_solarsystem.html
**주제:** 태양계의 실제 비율을 1px = 달 크기로 시각화
**읽기 시간:** ~10분 (속도에 따라 변동)

### Beat 구조 (14 beats)

```
Beat   타입           콘텐츠                              임팩트 요소
─────────────────────────────────────────────────────────────────────────
 1     hero           SVG 타이틀 + 스케일 지표             비주얼 진입
 2     interactive    태양계 수평 스크롤 맵                ★ 행성 아이콘 + 거리 마커
 3     narrative      "Pretty empty out here"             ★ 인지적 전환 — 빈 공간 체감
 4     comparison     여행 시간 비유                       2000편 영화 = 화성 왕복
 5     data-viz       목성까지 500년 (시속 75마일)         스케일 충격
 6     narrative      비유 클러스터 (화면, 인쇄물 475피트)  친숙한 단위로 번역
 7     narrative      뇌의 한계 에세이                    감각 박탈 레퍼런스
 8     quote          셰익스피어 인용                     문학적 앵커
 9     data-viz       99.9999...958% 비어있음             ★ 압도적 통계
10     data-viz       수소 원자 비율 → "11개 더 필요"     프랙탈 재귀 — 무한 스케일
11     narrative      존재론적 균형                        ★ "하찮으면서 기적적으로 중요"
12     conclusion     마무리 + "놀랍지 않나요"              감성적 클로징
13     interactive    "6,771개 더 스크롤" 유머              게임화 요소
14     conclusion     행성 점프 링크 + 언어 선택           리플레이 네비게이션
```

### 트랜지션/애니메이션
- **수평 스크롤:** 유일하게 가로 방향 — 우주 공간의 선형성 체현
- **거리 기반 공백:** 행성 사이의 실제 비율만큼의 빈 공간 → 스크롤 자체가 콘텐츠
- **산발적 텍스트:** 긴 빈 공간 사이에 갑자기 나타나는 텍스트 → 서프라이즈 효과
- **행성 점프:** 네비게이션으로 특정 행성으로 즉시 이동 가능

### 핵심 패턴 (Story Arc Designer 참고)
1. **빈 공간이 콘텐츠:** 스크롤하는 동안의 "아무것도 없음"이 핵심 메시지
2. **감정 아크:** 호기심(1-2) → 놀라움(3-5) → 경외(6-9) → 철학(10-11) → 위로(12)
3. **단일 메타포:** 전체 스토리가 하나의 비유(1px=달)로 구동
4. **유머 삽입:** 건조한 유머로 무거운 주제 완화 ("6,771개 더 스크롤")

---

## 종합 분석: Story Arc Designer를 위한 패턴

### 공통 beat 구조 (3개 스토리 종합)

```
전형적 비주얼 스토리 아크 (10-15 beats):

  HOOK (1-2 beats)
  ├── hero: 대형 타이틀 + 핵심 비주얼
  └── narrative: 논제/전제 설정

  BUILD (4-6 beats)
  ├── data-viz: 핵심 데이터 시각화 (가장 중요한 차트)
  ├── narrative: 맥락 설명
  ├── data-viz/comparison: 세부 분석
  └── timeline/narrative: 역사적/시간적 진행

  TURN (1-2 beats)
  ├── quote/narrative: 감정적 전환점
  └── data-viz: 새로운 관점 제시

  RESOLVE (2-3 beats)
  ├── narrative: 의미 해석 / 개인적 성찰
  ├── interactive: 독자 참여 (선택적)
  └── conclusion: 마무리 + CTA
```

### Beat 타입별 텍스트 비율

| Beat 타입 | 텍스트 비율 | 권장 단어 수 (한국어) | 핵심 역할 |
|-----------|-----------|---------------------|----------|
| hero | 10-30% | 20-50자 | 제목 + 분위기 설정 |
| narrative | 70-90% | 100-200자 | 맥락 전달 + 스토리 진행 |
| data-viz | 20-40% | 50-100자 (인사이트 텍스트) | 증거 제시 + "아하" 순간 |
| quote | 80-100% | 50-150자 | 감정적 앵커 + 권위 부여 |
| comparison | 50-60% | 100-150자 | 대비를 통한 통찰 |
| timeline | 60-70% | 150-200자 | 시간적 맥락 |
| interactive | 10-20% | 30-50자 (지시문) | 독자 참여 + 개인화 |
| conclusion | 80-90% | 80-150자 | 감정적 종결 + CTA |

### 임팩트 패턴 (가장 효과적인 순간들)

1. **"아하" 데이터 모먼트:** 하나의 통계/차트가 전체 논지를 결정적으로 보여줌
   - 예: 99.99% 빈 공간, 2010년대 부정적 곡 급등, 투표율 75%→30%
2. **톤 전환:** 분석적 → 개인적/감정적 전환이 가장 기억에 남는 순간
   - 예: "In Pursuit" Beat 20의 1인칭 에세이
3. **독자 참여:** 자기가 직접 탐색하는 인터랙티브가 몰입도 최고
   - 예: 아티스트 산점도 검색, 행성 점프 네비게이션
4. **단일 메타포:** 전체를 관통하는 하나의 강력한 비유
   - 예: "1px = 달", "각 점 = 5개 연설"

### 트랜지션 패턴

| 트랜지션 | 사용 맥락 | 구현 |
|---------|---------|------|
| fade-up | 새 섹션 진입 | IntersectionObserver + opacity/translateY |
| scroll-trigger | 차트 애니메이션 시작 | IntersectionObserver threshold |
| keep-scrolling | 분석 방식 전환 | 명시적 텍스트 프롬프트 |
| progressive-reveal | 데이터 점진적 노출 | scroll position → 데이터 필터 |
| zoom-in | 거시→미시 전환 | CSS transform: scale() |

### Layout Assembler를 위한 CSS 패턴

```
/* 공통 레이아웃 그리드 */
.story-container { max-width: 1200px; margin: 0 auto; }
.text-column { max-width: 680px; margin: 0 auto; }
.full-bleed { width: 100vw; margin-left: calc(-50vw + 50%); }

/* Beat 타입별 레이아웃 */
.beat-hero { position: relative; min-height: 100vh; }
.beat-narrative { padding: 4rem 0; }
.beat-data-viz { padding: 2rem 0; }
.beat-quote { text-align: center; font-size: 2rem; padding: 6rem 0; }

/* 스크롤 트리거 */
.scroll-trigger { opacity: 0; transform: translateY(20px); transition: all 0.6s; }
.scroll-trigger.visible { opacity: 1; transform: translateY(0); }

/* 반응형 */
@media (max-width: 768px) {
  .text-column { max-width: 100%; padding: 0 1rem; }
  .beat-quote { font-size: 1.5rem; }
}
```

---

## 권장사항: Design Doc 업데이트

### Story Arc Designer 프롬프트에 반영할 것
1. **10-15 beats가 최적** (분석 결과 14-23 범위, FT 기준 10-15)
2. **HOOK → BUILD → TURN → RESOLVE 4단계 구조** 필수
3. **하나의 핵심 데이터 비주얼**이 전체 스토리를 관통해야 함
4. **톤 전환점**을 명시적으로 설계 (BUILD → TURN 경계)
5. **텍스트 비율 가이드**: beat 타입별 권장 단어 수 제공

### Layout Assembler 프롬프트에 반영할 것
1. **Scrollama step-based architecture** 사용
2. **text-column (680px) + full-bleed 패턴** 기본
3. **fade-up이 기본 트랜지션**, scroll-trigger는 data-viz에만
4. **순수 비주얼 beat 허용** (텍스트 0%, 차트만으로 소통하는 순간)
5. **모바일 퍼스트**: 680px 텍스트 컬럼은 모바일에서 100% + 패딩
