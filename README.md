# brain

`harangon/drbrain` 볼트를 Notion처럼 보고 편집하는 단일 페이지(`index.html`). 서버 없음, GitHub Contents API 직접 호출. PWA로 홈 화면 설치 가능.

## 사용
- 첫 실행: ⚙ → 저장소 `harangon/drbrain`, 브랜치 `main`, Fine-grained 토큰(Contents 읽기·쓰기). 토큰은 브라우저 localStorage에만 저장
- 탭: 문서(폴더 트리 + 편집기) · 노트(표 / 보드 / 갤러리 전환) · 할 일 · 일정. 노트 탭에서 필터·정렬 조합을 "현재 뷰 저장"
- 빠른 입력 → `00_Inbox/YYYY-MM-DD-제목.md`. 폴더의 `+` → `_templates/` 기반 새 노트
- 노트 패널: 상태 · 라벨(여러 개) · 마감 · 사용자 속성 · 체크리스트(즉시 저장) · 본문(`[[` 자동완성, 이미지 첨부 → `_attachments/`) · 백링크. 저장 = 커밋 `web: 제목`
- ⋯ 메뉴: 넓게 보기 · 복제 · 폴더 이동 · 보관(90_Archive) · GitHub에서 보기 · 삭제
- 보드: 드래그로 열 이동(status/label), 같은 열 안 드래그로 순서(`order`)
- 표: 체크박스 선택 → 일괄 변경. 셀에서 바로 편집
- 할 일: 위 '오늘' 상자에 Google 일정 + 오늘 할 일 + 지연. 입력창 + 오늘/내일/다음 주 칩 + 저장할 노트(데일리 또는 프로젝트·영역 노트의 `## 할 일`). 행마다 노트 칩, → 내일 / → 다음 주 미루기(📅만 변경). 이번 주 / 이후 / 날짜 없음 / 오늘 완료(접힘). 오른쪽(폰은 칩)에서 노트별로 좁혀 보기
- 일정: 월 달력에 Google 일정 + 마감·할 일·데일리. 날짜 선택 → 목록, 일정 클릭 → 수정, 칸 드래그 → 날짜 이동, 검색(전 기간), + 일정 / + 마감 노트 / + 할 일
- Ctrl+K 팔레트, Ctrl+S 저장, Esc 닫기
- 오프라인: 저장·삭제·새 노트는 큐에 쌓였다가 자동 반영. 다른 기기가 먼저 바꾼 파일은 `(오프라인 사본)`으로 저장. 상단 "대기 N" 배지로 재시도·버리기

## Google 캘린더 연결 (Apps Script 프록시)
`gcal.gs`를 Google Apps Script 웹 앱으로 배포(실행 계정: 나, 액세스: 모든 사용자)하고, brain ⚙ → 연결에 웹 앱 URL과 KEY를 넣는다. 일정은 매번 Google에서 직접 읽고 쓰며 저장소에는 남지 않는다. 월 단위 5분 캐시, 오프라인이면 마지막 캐시를 "기준 시각"과 함께 표시. KEY는 브라우저에만 저장되고 요청 본문(POST)으로만 보낸다.

## 설정 파일
`drbrain/_scripts/brain.config.json` — `statuses`, `labels`, `props`(사용자 속성: id/name/type[text|number|date|select|checkbox]/options), `views`. ⚙ → 속성에서 편집하면 커밋됨. 볼트의 `CLAUDE.md`가 이 파일을 참조.

## 프론트매터 규약
- `label`: 하나면 `label: work`, 여럿이면 `label: [read, work]`
- `order`: 보드 수동 순서(숫자). 바꿔도 `updated`는 갱신 안 함
- Obsidian 블록 리스트(`related:` + `  - "[[x]]"`)도 읽고, 쓸 때는 `[...]`로 정규화. 중첩 맵은 지원 안 함(저장 시 사라짐)

## 개발
- 코드 전부 `index.html` 하나. `sw.js`는 network-first 셸 캐시
- 테스트: `index.html`의 `<script>`를 뽑아 `api.*`를 메모리 파일로 바꾼 mock 페이지를 만들고 Playwright(Chromium)로 각 뷰·흐름을 돌린다. 순수 함수(parseFM/buildFM/titleOf/slug/mdToHtml)는 node 단위 테스트
- 알려진 한계: 커밋 단위 파일 1개 · 이동·보관·첨부는 온라인 전용 · 미리보기는 기본 마크다운만
