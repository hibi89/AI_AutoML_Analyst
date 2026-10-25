# P6 NanumGothic licensing note — authoritative source review (2026-10-26)

## Official primary source
- NAVER customer center: https://help.naver.com/service/30016/contents/18088?lang=ko&osType=PC
- NAVER states that the Nanum font family is owned by NAVER/NAVER Cultural Foundation, is available for individuals and businesses including commercial usage other than **selling fonts on their own**, and is licensed under **SIL Open Font License 1.1**.
- NAVER's license permits embedding in documents and software; it explicitly states the font-license terms do **not** apply to documents created using the font.
- Redistribution/bundling the **font program** with software carries notice/license inclusion and reserved-name conditions, so **do not include standalone TTF files in product ZIPs by default**. PDF reports may contain embedded subsets as normal ReportLab output.
- Recommended simple attribution in customer-facing documentation: '본 보고서에는 네이버에서 제공한 나눔글꼴이 적용되었습니다.' For font binaries distributed separately, include copyright notice and actual OFL text; do not substitute this note.

## Observed product state and remaining verification
- CI uses `apt-get install fonts-nanum` on Linux; PDF font is embedded as a TrueType subset via ReportLab. Existing PDF raster/extraction tests verify Korean glyph display on Linux-generated synthetic reports.
- Windows manual local run still needs a locally installed, properly obtained NanumGothic. `AUTOML_KOREAN_FONT_PATH` may point at it; neither TTF nor another proprietary font should be committed/re-shared.
- Source audit confirms **font licensing only**, not package dependency security compliance, legal advice, model copyright, advertising claims or final release go/no-go. Keep commercial release gated until the rest of P6 is complete.
