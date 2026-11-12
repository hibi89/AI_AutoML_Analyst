# P6E50–P6E52 — 독립 고객 납품 ZIP/PDF 검토 (2026-11-12 KST)

## 확인된 목표·원본

- 개발 원본: `hibi89/AI_AutoML_Analyst@feature/kmong-v1`, 시작 HEAD `4b7da83e037badab545ff14d03e7fe8cd049b52a`; `main` 미변경. 기존 BASIC·STANDARD·PREMIUM 모델·FastAPI·PDF·ZIP 생성 엔진을 보존.
- 확정 상품: BASIC 60,000원(모델 학습 없음), STANDARD 150,000원(최대 비-Dummy 3모델+holdout), PREMIUM 300,000원(최대 5모델+신뢰된 재예측). 납품 ZIP에는 `manifest.json`, `report.pdf`, `README.txt`, 표·차트 등이 있으며 기존 `scripts/p6e6_delivery_policy.py`가 필수 항목·SHA·수량·외부 의존성 금지를 검증한다.
- **실제 고객 소스·개인정보·권한/의존성 원본·실고객 모델 사용/외부전송 없음.** 오직 합성 입력과 소유자가 명시한 *이미 생성된 로컬 결과물* 검사. 로그인·모델 로드·압축해제·원격 전송·구매자 자동 승인은 금지.

## 설계 비교와 선택

| 접근 | 속도·비용 | 위험 | 선택 |
|---|---|---|---|
| A. 기존 `p6e5_windows_demo` 합성 ZIP 결과만 신뢰, `pytest` 성공을 상품판매 GO로 변환 | 개발비 낮음 | 합성 증거와 실제 소유자 파일 SHA 불일치, 악의적/비정상 ZIP, 종별 법적 승인 누락을 포착 못함 | 기각 |
| B. 기존 SHA 검사 함수를 **물리 ZIP에 다시 적용**, 선행 압축폭탄·경로·개수 상한, PDF 구조/페이지 실증, 세 SKU 독립 검수 및 무JS 정적 사람용 검토표; CI의 실상품 엔진+합성 3종 E2E는 별도 | 추가 Python 도구·테스트만 필요; API 호출비·사용료0 | 고객파일·글꼴권리/시각검수는 별도 필요하지만 검증 경계 명확 | **채택** |

## 구현

### P6E50 물리 ZIP / PDF 독립 확인

`scripts/p6e50_owner_zip_review.py`:

- 소유자가 선택한 **절대경로** `.zip`을 원본 변경·추출 없이 읽음; 파일/부모 링크 거부, 원본 파일 크기 최대72MiB, member 80개, member당24MiB, 총 압축해제 예상128MiB, 압축비250:1 초과, 중복·대소문자 중복·상대상위경로·암호 ZIP·미지원 압축 거부.
- 입력 SHA256을 **사용자가 별도로 전달한 기대값**과 대조하고 후처리 시 물리 원본 재해시; 기존 `verify_shipping_zip`를 재사용해 SKU별 필수 구성·manifest 각 멤버 바이트 SHA/길이·README 글꼴 권리 *문구 포함 여부* 확인.
- `pypdf`로 실제 PDF 암호화 여부/구조·BASIC 6–8p, STANDARD 8–12p, PREMIUM 10–15p와 페이지 치수 검토. **PDF 글꼴의 시각 품질·라이선스 원문/재배포권까지 자동 증명하지 않음.**
- 소유자가 지정한 **존재하지 않는 새 JSON**만 생성, `os.O_EXCL` 사용, 실패 시 새 출력만 정리, 원본/경로/레코드/모델 내용 메타데이터에 복사하거나 출력하지 않음.

실행:

```powershell
python -m scripts.p6e50_owner_zip_review `
  --zip "C:\Private\BASIC-owner-existing.zip" `
  --tier BASIC `
  --expected-sha256 "<원본 ZIP SHA256 64자리>" `
  --out "C:\Private\BASIC-review-NEW.json"
```

### P6E51 소유자 3종 교차 검토표

`scripts/p6e51_owner_three_tier_review.py`:

- 서로 다른 3개 ZIP을 각 **정확한 SHA**와 결합, P6E50으로 실제 BASIC/STANDARD/PREMIUM 개별 검수, 출력 직전 물리 파일 해시 재대조.
- 유일한 두 출력 `--out-json`(신규 JSON) + `--out-html`(신규 정적 HTML)만 명시적으로 생성. 2차 생성 실패 시 1차 신규 파일만 정리; 기존 사용자 파일 덮어쓰지 않음.
- HTML은 파일 단독 열람, 스크립트 없음(`script-src 'none'; connect-src 'none'; img-src 'none'`), 세 티어 PDF 페이지/SHA/ZIP 멤버 수를 표시. 한국어 **사람 검토 7개 항목은 전부 NOT_VERIFIED**. 고객 원본·패키지·모델·절대 경로를 HTML이나 JSON에 포함하지 않음.

```powershell
python -m scripts.p6e51_owner_three_tier_review `
  --basic "C:\Private\BASIC.zip" --basic-sha256 "<64자리>" `
  --standard "C:\Private\STANDARD.zip" --standard-sha256 "<64자리>" `
  --premium "C:\Private\PREMIUM.zip" --premium-sha256 "<64자리>" `
  --out-json "C:\Private\THREE-REVIEW-NEW.json" `
  --out-html "C:\Private\THREE-REVIEW-NEW.html"
```

### P6E52 실제 기존 3종 엔진 통합

`tests/test_p6e52_real_three_tier_delivery.py`는 기존 `build_basic_zip`, `build_standard_zip`, `build_premium_zip`를 사용해 **150행 합성 데이터**에서 분류 CV3으로 세 ZIP을 실제 생성하고, P6E51로 세 결과를 다시 읽어 PDF 페이지·ZIP manifest·물리 해시와 모든 승인 HOLD를 확인. 실제 고객 자료, 서명, 구매자 PC 없음. 테스트 코드/데이터는 ZIP·학습 모델을 GitHub artifact로 올리지 않음.

## 검증된 범위 / CI

- 최초 P6E50 SHA `3e53a5726ae88c68c18a7746a7adfab1bb624576`: [Actions #43110693053](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/43110693053) Ubuntu24.04·Windows2025 2/2 성공, **각 39 PASS / 경고1**. 물리 ZIP·PDF/manifest 훼손·압축비·파일 중복·기존 출력 보존·경로 등을 실제 Py3.11+reportlab+pypdf로 테스트.
- P6E51–52 통합 기능 SHA `2704fd0d1ecb56e6092a918514d93412c3533ffb`: [Actions #43111584813](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/43111584813) **3/3 JOBS COMPLETED SUCCESS**: Ubuntu ZIP+3티어·기존 Shipping Policy 회귀 **53 PASS / 1 WARNING**; Windows2025 **52 PASS / 1 SKIP / 1 WARNING**(OS symlink 권한 차이 명시); Ubuntu Python3.11에 원본 `requirements-verified-py311.txt`+Nanum/Arphic 폰트 설치, **실제 기존 BASIC/STANDARD/PREMIUM 생성→검수 1 PASS / 6 warnings**.
- 범위 외: 전체 기존 `pytest tests` 273+를 이번 SHA에서 다시 돌린 것 아님; UI 브라우저/PowerShell 실제 Windows GUI/실제 고객 CSV/XLSX/실제 재예측 수용 테스트 아님; Python 3.13 제품 런타임 승인 아님; PDF 모든 페이지 실제 눈으로 훑거나 설치된 실사용 폰트 원문·의존성/유통권·고객 개인정보 수집동의 확인하지 않음. 상용 승인/실제 거래와 근본적으로 분리.

## 범위 점수 / 남은 기준

- 기존 해총 **71%**는 엄격한 원본 `P0–P6` 인수 기준 **5/7 승인을 통한 점수**. 이 승인 카운트는 **여전히 5/7**, P1 일부/ P6 구매자·폰트·권리·검수 **NOT APPROVED**.
- 이번 구현으로 별도로 평가 가능한 엔지니어링 납품 범위 추정: +4p P6E50 물리 ZIP/PDF 경계 검증, +4p P6E51 3종 독립+소유자 정적 검토 인터페이스, +4p P6E52 실제 원본 3종 생성기 SHA 연계 E2E, +2p Windows/Linux 실제 회귀/보안 부정 시나리오 = **71→85% 잠정 엔지니어링 지표**. 이 신규 지표는 법적·고객 수락 5/7과 별개이며 두 지표를 동일 승인률로 혼용하지 말 것.
- **BASIC/STANDARD/PREMIUM 모두 SALE NO-GO / RELEASE HOLD**. 85%라는 엔지니어링 추정만으로 출시 금지. 다음은 소유자가 허락한 로컬 환경에서 각 상품 PDF/ZIP 전체 페이지 및 글꼴·원본 라이선스/NOTICE 실검수, Windows 브라우저·인쇄 및 구매자 전달·반품·정정 범위 3종 실제 조작 후 상품별 명시적 GO; 소유자 명시 승인 전 고객자료 사용/제3자 제공 금지.

## 복구·보안

원본 `feature/kmong-v1` 및 `main`의 분석 엔진과 데이터는 변경하지 않음. 변경은 새 feature `feature/kmong-p6e50-owner-delivery-20261112`에 신규 스크립트·신규 테스트·새 Action·문서로만 이루어짐. 원본 checkout/파일은 Git 커밋 부모에서 복구 가능. 프로덕션/Vercel은 로컬 분석 상품이므로 미적용; API 사용·외부 업로드·결제·권한·환경변수 변경 없음.
