# 한국관광공사 지역별 관광행사 정보

한국관광공사 TourAPI의 **행사정보조회(searchFestival2)** API를 사용하여 전국 17개 시도의 관광행사/축제 정보를 매일 자동 수집합니다.

## 데이터 구조

```
data/
├── latest.json          # 최신 수집 데이터
└── 2026/
    └── 03/
        └── festivals_20260320.json
```

## 수집 항목

- 행사명, 주소, 기간, 이미지, 연락처 등
- 전국 17개 시도별 분류

## 데이터 출처

- [한국관광공사 TourAPI](https://api.visitkorea.or.kr/)
- [공공데이터포털](https://www.data.go.kr/data/15101578/openapi.do)
