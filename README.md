\# AI AutoML Analyst



AI AutoML Analyst는 로컬 폴더 안의 CSV 파일을 탐색하고, 사용자가 선택한 CSV와 target 컬럼을 기준으로 여러 머신러닝 모델을 자동 실험하여 결과를 비교해주는 FastAPI 기반 AutoML 분석 보조 도구입니다.



이 프로젝트는 특정 데이터셋 하나만 분석하는 노트북이 아니라, 다양한 CSV 데이터셋을 빠르게 훑어보고 머신러닝 실험 가능성을 확인하기 위한 도구입니다.



\---



\## 주요 기능



\- 로컬 폴더 내 CSV 파일 자동 탐색

\- CSV 컬럼 구조 기준 schema group 생성

\- schema group별 대표 CSV 파일 표시

\- CSV별 컬럼 목록 및 예측 대상 후보 확인

\- 선택한 CSV 파일 1개 기준 AutoML 분석 실행

\- Classification / Regression 실험 지원

\- 데이터 크기에 따른 모델 후보 자동 선택

\- 여러 ML 모델 Cross Validation 평가

\- 모델 성능 랭킹 생성

\- 결과 해석 및 Markdown 리포트 생성

\- 분석 결과 JSON / Markdown 저장

\- 저장된 분석 이력 조회

\- 간단한 웹 프론트엔드 제공



\---



\## 기술 스택



\- Python

\- pandas

\- scikit-learn

\- FastAPI

\- Uvicorn

\- HTML / CSS / JavaScript

\- Git



\---



\## 프로젝트 구조



```text

AI\_AutoML\_Analyst/

├─ backend/

│  └─ app/

│     ├─ main.py

│     ├─ models/

│     │  └─ registry.py

│     └─ services/

│        ├─ profiler.py

│        ├─ task\_detector.py

│        ├─ preprocessor.py

│        ├─ evaluator.py

│        ├─ trainer.py

│        ├─ ranker.py

│        ├─ automl\_runner.py

│        ├─ model\_selector.py

│        ├─ folder\_scanner.py

│        ├─ ai\_analyst.py

│        ├─ recommendation.py

│        ├─ report\_generator.py

│        └─ storage.py

├─ frontend/

│  └─ index.html

├─ data/

├─ experiments/

├─ tests/

├─ pyproject.toml

├─ .gitignore

└─ README.md

