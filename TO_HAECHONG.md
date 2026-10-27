# TO_HAECHONG.md — 해총님에게
**담당:** AI AutoML Analyst 개발 총괄
**검수 대상:** `hibi89/AI_AutoML_Analyst` / `feature/kmong-v1`
**기준일:** 2026-10-28 KST
**최종 질의:** 기존 병목이 무엇이었고, 실제로 어떤 작업 절차를 없앴으며, 그 결과 어떤 기능을 추가로 완성했는가?

> **요약 판정 요청: FIX + KEEP(부분적)**. 개발 운영과 로컬 검증 진입점의 *구현·CI 사전검증*은 이루어졌지만, 이 운영 개편 **이후 신규 고객용 분석 기능은 완성되지 않았음(미개선)**. 신규 전체 Windows 단일 명령의 끝까지 실제 실행도 **NOT RUN**. 개발 완료나 측정된 시간 단축을 주장하지 않음.

## 1. 기존 병목 TOP 3
1. **GitHub 수정·확인 반복:** 2026-10-28 P6E45–47에서 기능별 코드·테스트 이후 `HANDOFF.md`, `STATUS.md`, `docs/dispatch/ACTIVE_TASK.md`, `WORKER_START_HERE.md`까지 중복 기록하고 HEAD/Actions를 반복 확인. 최종 산출과 무관한 커밋·호출 다수.
2. **Windows 최종 검수 경로의 분산·부분 실행:** 기존 `scripts/windows_release_qa.ps1`은 정해진 약 10개 테스트 모듈만 실행. Linux에서는 전체 테스트 273 PASS/3 SKIP이었지만 Windows owner가 한 번에 전체 회귀와 실제 Chromium 다운로드, 합성 3개 SKU ZIP 검사를 호출할 루트 명령이 없었음.
3. **CI 환경 부트스트랩·중복 검증:** Python 의존성·한글 글꼴·렌더러·Chromium 설치 시간이 전체 pytest 실행보다 큰 구간이 있었음. GitHub Actions 재조회와 같은 SHA의 중복 실행을 줄여야 함.

## 2. 발생 원인 및 측정 근거
- **도구/API:** 연결된 GitHub API의 단일 파일 수정 방식과 작업 습관 때문에 파일별 커밋이 발생. Git tree/commit/ref 갱신 방식으로 묶을 수 있었으나 이전엔 거의 이용하지 않음.
- **문서·순서:** 실제 기능보다 기록을 과도하게 자세히 반복. P6E45–47 이력과 580줄 이상의 `HANDOFF.md`로 확인. 문서 작업 소요시간 측정은 **없음**.
- **테스트 환경:** 기존 Windows 스크립트의 고정 모듈 목록 및 별도 브라우저 스크립트 `scripts/p6_browser_smoke.py`. Linux [40548766131](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548766131)의 전체 **273 PASS/3 SKIP/69 warnings**. 테스트 실행 64.16초(로그 기준); 그 이전 CI에서 글꼴 apt 설치가 약 11분 걸린 사례가 프로젝트 기록에 있음. 이는 동일 실행 비교가 아니며 평균 소요시간이나 절감률이 아님.

## 3. 실제 개선 조치 (적용 vs 계획)
| 개선 | 실제 적용 | 아직 미완료/검증 |
|---|---|---|
| **기능 단위 커밋** | `142aae58`에서 Git tree + 단일 커밋/expected-SHA 브랜치 보호로 **4개 파일 원자적 반영**. `AGENTS.md`에 해당 원칙 기록 | 한 번의 적용 사례만 확인. 장기 반복 감소·시간 절감 측정 **미실시** |
| **중복 문서 폐지** | `AGENTS.md`에서 STATUS=현재, HANDOFF=복구, README=사용법으로 역할 명시. 작은 변경마다 전 문서 동시 수정 의무를 제거 | 과거 중복 문서 전체 정리/삭제 **미실시**(이력 보존). 이번 별도 보고서는 소유자 지정 예외 |
| **단일 Windows 검증 명령** | 루트 `verify_local.ps1` 새로 구현. `-Quick`, `-SkipBrowser`, `-CheckOnly` 및 기본 FULL. `scripts/windows_release_qa.ps1 -AllTests`로 전체 pytest를 한 번 호출하고 합성 ZIP 검수·Chromium 6경로를 연결. 로그 및 JSON 요약은 무시 폴더 `qa-preview/`; 고객/DB 파일 삭제·경로 탐색 없음 | 기본 FULL에서 전체 pytest + ZIP + 실제 Chromium의 **Windows owner 실환경 종단 실행은 NOT RUN** |
| **CI 사전 검사** | `.github/workflows/windows-compat.yml`에서 두 PowerShell 스크립트 구문 검사 + `verify_local.ps1 -CheckOnly` 실행. 유효 Git SHA 출력 검사 | 사전 검사 통과를 FULL 검수와 동일시 금지 |
| **CI 중복 최소화** | 필요 기능 변경 시 집중 테스트 후 통합/릴리스 단계 전체 회귀, 불변 SHA 반복 재조회를 줄이라는 정책 적용 | 실제 총 CI 실행량·시간 절감률은 **미측정**. 기존 push 트리거는 유지 |

**변경 중 실패 투명 공개:** 첫 원자적 변경 `142aae58`에서 Windows 워크플로 YAML이 문자열 패치 오류로 깨져 [40552170957](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40552170957) **failure(작업 jobs 0, 워크플로 정의 오류)**. 이전 정상 파일을 기준으로 `ad0cf70420e6d81243331687ed4245e4964284f8`에서 복구 후 [40552439435](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40552439435) **SUCCESS**. 즉 최초 적용은 재작업 비용이 발생했음.

## 4. 개선 이후 실제 기능 진척
- **개발·검증 기능(완료된 소스 변경):** Windows 한 줄 진입점, QUICK/FULL 선택, 자동 합성 3단계 납품팩 생성 연결, 실물 브라우저 ZIP 다운로드 검증 호출, 로그+JSON 결과 기록과 보호 플래그 추가. 기존 원래 분석 기능/브라우저 테스트를 재사용하며 새 프레임워크나 서비스 없음.
- **새 고객용 AI AutoML 분석 기능:** 이 운영 개편 직후 **추가 구현 0건 = 미개선**. 기존 제품 기능(P6E45 날짜 파생열 충돌, P6E46 boolean 결측, P6E47 문자 범주 `001` 보존)은 **개편 이전에 구현된 것**이며 개편 성과로 계산하지 않음.
- **MVP:** BASIC·STANDARD·PREMIUM의 합성 E2E는 앞선 CI에서 작동. 신규 작업은 이 세 제품의 실제 Windows 최종 납품 검증을 실행하기 쉽게 만드는 것.
- **해총 검수용 구분:** '검증 자동화 코드 구현'은 완료; '검증 자동화의 전체 실환경 성공'은 미검증; '상품 기능 추가'는 미개선.

## 5. 전후 SHA / 파일 / 실제 실행 증거
| 시점 | SHA 및 변경 | 실행된 검증 |
|---|---|---|
| **개편 직전 기준** | `45874f3d605332e6baa4f4f5752541079c5eb483`; P6E47 기능 소스 `aa2ffb19`, 테스트 `6c376ace` | Linux 전체 [40548766131](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548766131) **273 PASS/3 SKIP/69 warnings**, 기본 PDF 6/9/11페이지. Windows native [40548671991](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548671991), Windows Chromium [40548671949](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548671949), Linux Chromium [40548672179](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548672179), Docker [40548672267](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40548672267) 모두 **SUCCESS** (기존 기능 증거) |
| **운영 개편 기능 변경** | [`142aae58`](https://github.com/hibi89/AI_AutoML_Analyst/commit/142aae58da7e809afb9c8e1ed7b5bcb4efce3082): `AGENTS.md`, `verify_local.ps1`, `scripts/windows_release_qa.ps1`, `.github/workflows/windows-compat.yml` | 신규 Windows Actions 1차 **failure**(유효하지 않은 워크플로 정의; 앞 절 참조) |
| **CI 수정/검증 기준** | [`ad0cf704`](https://github.com/hibi89/AI_AutoML_Analyst/commit/ad0cf70420e6d81243331687ed4245e4964284f8) 워크플로 수정 | Windows [40552439435](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40552439435) **SUCCESS: 99 PASS/9 warnings**; 구문 검사 및 `-CheckOnly` 정상 종료. Linux 전체 검증은 새 운영-only SHA에서 **NOT RUN**(Linux 기능 코드는 변경하지 않음) |
| **신규 원클릭 FULL** | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\verify_local.ps1` | **NOT RUN (owner Windows)**. `-CheckOnly` 검증만 통과. 예상 PASS/FAIL/시간 임의 기재 금지 |

출력 로그·JSON: `qa-preview/verify-local-*.log`, `qa-preview/verify-local-*.json` (현재 사용자 PC에 생성된 결과물은 없음, 스크립트 구현 위치만 확인). 원본 `main`은 수정하지 않음.

## 6. 남아 있는 병목 — 직접 해결 vs 소유자 전용
**총괄/AI가 직접 가능**
- 새 로컬 QA 경로의 누락된 검증 범위·실제 오류 재현/수정, 환경 설치 병목의 불필요한 반복 제거.
- GitHub Actions로 합성 테스트, 독립 Windows/Linux 브라우저 CI, ZIP 계약/헤더/모델 재예측 자동 검증.
- SKU 납품 패키지 관련 실제 결함을 재현했을 때만 기능 수정 및 회귀 테스트. 소수의 검증 가능한 단위로 커밋.

**사용자 로컬 PC 또는 명시적 승인 필요**
- 대상 Windows에서 `verify_local.ps1` FULL 1회 실행(또는 승인된 로컬 Codex 실행), 생성된 실제 PDF/ZIP 및 글꼴 표시 육안 확인.
- 폰트의 실제 출처·배포 조건, 의존성 및 NOTICE를 확인하여 상업적 사용 승인 여부 결정.
- 합성 테스트가 아닌 고객 데이터 사용, 실제 고객 대상 서비스·결제, 외부 공개, `main` 병합, BASIC/STANDARD/PREMIUM 각 SKU의 별도 판매 GO.
- Windows 전체 FULL이 실패하면 결과 JSON/log를 받아 AI가 원인을 해결해야 함. 사용자가 반복 수동 테스트를 수행하는 것은 요구하지 않음.

## 7. 다음 개발 계획 / 완료 조건
1. **우선 순위: Windows 원클릭 FULL 종단 검증.** 기준: 해당 HEAD에서 전체 pytest, 합성 BASIC/STANDARD/PREMIUM PDF·ZIP 생성, 실제 Chromium에서 3 SKU × 2 인코딩 다운로드 및 ZIP 무결성, PASS/FAIL/SKIP/환경/SHA 요약 JSON 생성. 현재 **코드 준비, 전체 실제 실행 미검증**. 새 기능을 무작정 추가하지 않고 오류가 나타나면 해당 경로만 수정.
2. **다음 실질적 제품 목표:** `REQUIREMENTS.md`와 `docs/product/SKU_MATRIX.md`의 실제 누락/구현 결함을 최소 1개 증거 기반으로 선택. 예: 판매 전 최종 검수에서 재현된 사용자 입력 오류/ZIP/모델 재예측 결함. 필요할 때만 집중 테스트→통합 CI.
3. **상업용 결과물 마감:** PDF 페이지 품질과 한일 폰트 사용 권리/라이선스·NOTICE 표, 실물 Windows ZIP 사용자 인계 품질 확인, 상품별 원가/수정 범위·안전성 점검, 소유자별 명시적 GO.
4. **MVP 및 최종 잔여:** 세 SKU의 합성 MVP는 구현·자동 검증되어 있음. 공식 단계 승인은 **P0–P6 중 5/7(71%)**, P1 PARTIAL, P6 NOT ACCEPTED. 이는 전체 기능 구현률이 아닌 **형식적 승인 진행률**. 최종 완료에는 실환경 Windows 통합 QA·사용자 시각/라이선스 심사·SKU별 판매 승인과 발견된 실제 오류 수정이 남음. 남은 시간을 실측하지 않았으므로 확정 시간/절감률 제시하지 않음. 전 SKU **SALE NO-GO**.

**검수 제안:** 코드 운영변경은 KEEP, 미실행 전체 로컬 검증 및 고객용 신기능 0건은 FIX, 중복 문서/동일 SHA 폴링은 STOP, 검증 결과 기반 제품 기능 작업은 ACCELERATE. 이 보고서 작성만으로 개발이 완료되었다고 판정하지 말 것.
