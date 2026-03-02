# 📋 Spec: 아파트 데이터 분석 대시보드

## 개요

공공데이터포털(data.go.kr)의 아파트 정보 API를 활용하여 전국 아파트 데이터를 수집하고,  
Streamlit 기반의 인터랙티브 대시보드로 시각화하는 프로젝트입니다.

---

## 구성 모듈

### 1. 데이터 수집

#### `get_list.py` — 아파트 목록 수집
- 공공데이터포털 `AptListService3/getTotalAptList3` API 호출
- 전국 아파트의 단지 코드(`kaptCode`), 단지명, 법정동 코드, 주소(시/구/동) 수집
- 페이지네이션 자동 처리 (전체 데이터 완전 수집)
- 결과를 `apt_list.csv`로 저장 (약 21,900개 단지)

#### `get_detail.py` — 아파트 상세 정보 수집
- 공공데이터포털 API를 사용하여 아파트의 기본 정보와 상세 정보를 모두 수집
- **기본 정보 수집**: `AptBasisInfoServiceV4/getAphusBassInfoV4` API 호출
  - 결과를 `apt_basic.csv`에 저장
- **상세 정보 수집**: `AptBasisInfoServiceV4/getAphusDtlInfoV4` API 호출
  - 결과를 `apt_detail.csv`에 저장
- `apt_list.csv`의 각 단지 코드를 기준으로 수집
- **이미 수집된 단지는 자동으로 건너뜀** (각 파일별로 개별 체크)
- `--limit N` 옵션으로 수집 개수 제한 가능 (테스트용)

#### `extract_price.py` — 공시가격 정보 추출
- **데이터 소스**: [국토교통부_주택 공시가격 정보](https://www.data.go.kr/data/3073746/fileData.do)
- 원본 대용량 CSV (약 3.4GB)를 `duckdb`를 이용해 메모리 효율적으로 처리
- `apt_basic.csv`의 주소(`doroJuso`) 및 법정동코드(`bjdCode`)를 기준으로 매핑
- 필터링된 결과를 `apt_price_mapped.csv`로 저장하여 용량 최적화 (약 280MB)

수집되는 기본 필드 (`apt_basic.csv`):
| 필드명 | 설명 |
|--------|------|
| `kaptCode` | 단지코드 |
| `kaptName` | 단지명 |
| `kaptAddr` | 주소 |
| `codeSaleNm` | 분양형태 |
| `codeHeatNm` | 난방방식 |
| `kaptTarea` | 관리비부과면적 |
| `kaptDongCnt` | 동수 |
| `kaptdaCnt` | 세대수 |
| `kaptBcompany` | 시공사 |
| `kaptAcompany` | 시행사 |
| `kaptTel` | 단지전화번호 |
| `kaptUrl` | 단지홈페이지 |
| `codeAptNm` | 아파트 종류 |
| `doroJuso` | 도로명주소 |
| `codeMgrNm` | 관리방식 |
| `codeHallNm` | 복도유형 |
| `kaptUsedate` | 사용승인일 |
| `kaptFax` | 단지팩스번호 |
| `hoCnt` | 호수 |
| `kaptMarea` | 주거전용면적합계 |
| `kaptMparea60` | 전용면적별 세대현황(60㎡ 이하) |
| `kaptMparea85` | 전용면적별 세대현황(60㎡ ~ 85㎡ 이하) |
| `kaptMparea135` | 전용면적별 세대현황(85㎡ ~ 135㎡ 이하) |
| `kaptMparea136` | 전용면적별 세대현황(135㎡ 초과) |
| `privArea` | 주거전용면적 |
| `bjdCode` | 법정동코드 |
| `kaptTopFloor` | 최고층 |
| `ktownFlrNo` | 건수(?) |
| `kaptBaseFloor` | 최저층 |
| `kaptdEcntp` | 승강기대수 |
| `zipcode` | 우편번호 |

수집되는 상세 필드 (`apt_detail.csv`):
| 필드명 (API 키) | 설명 |
|----------------|------|
| `kaptCode` | 단지코드 |
| `codeMgr` | 일반관리방식 |
| `kaptMgrCnt` | 일반관리인원 |
| `kaptCcompany` | 일반관리 계약업체 |
| `codeSec` | 경비관리방식 |
| `kaptdScnt` | 경비관리인원 |
| `kaptdSecCom` | 경비관리 계약업체 |
| `codeClean` | 청소관리방식 |
| `kaptdClcnt` | 청소관리인원 |
| `codeGarbage` | 음식물처리방법 |
| `codeDisinf` | 소독관리방식 |
| `kaptdDcnt` | 소독관리 연간소독횟수 |
| `disposalType` | 소독방법 |
| `codeStr` | 건물구조 |
| `kaptdEcapa` | 수전용량 |
| `codeEcon` | 세대전기계약방식 |
| `codeEmgr` | 전기안전관리자법정선임여부 |
| `codeFalarm` | 화재수신반방식 |
| `codeWsupply` | 급수방식 |
| `codeElev` | 승강기관리형태 |
| `kaptdEcnt` | 승강기대수 |
| `kaptdPcnt` | 주차대수(지상) |
| `kaptdPcntu` | 주차대수(지하) |
| `codeNet` | 주차관제·홈네트워크 |
| `kaptdCccnt` | CCTV대수 |
| `welfareFacility` | 부대·복리시설 |
| `kaptdWtimebus` | 버스정류장 거리 |
| `subwayLine` | 지하철호선 |
| `subwayStation` | 지하철역명 |
| `kaptdWtimesub` | 지하철역 거리 |
| `convenientFacility` | 편의시설 |
| `educationFacility` | 교육시설 |
| `groundElChargerCnt` | 지상 전기차 충전기 대수 |
| `undergroundElChargerCnt` | 지하 전기차 충전기 대수 |
| `useYn` | 사용여부 |

---

### 2. 대시보드 (`main.py`)

`uv run streamlit run main.py`로 실행하는 웹 대시보드입니다.

#### 사이드바 필터
- **시/도** 다중 선택 필터 (1단계)
- **행정구역(구/군)** 다중 선택 필터 (2단계 - 선택된 시/도에 종속됨)
- **지하철 호선** 다중 선택 필터 (데이터셋에 존재하는 모든 호선 대상 필터 작동)
- **준공 연도 범위** 슬라이더
- **세대 수 범위** 슬라이더
- **전용면적 범위 (㎡)** 슬라이더 (`apt_price_mapped.csv` 연동)
   - 빠른 선택 버튼 지원 (`전체`, `초소형(~40㎡)`, `소형(40~60㎡)`, `중소형(60~85㎡)`, `중대형(85~135㎡)`, `대형(135㎡~)`)
- **공시가격 범위 (억원)** 슬라이더 (`apt_price_mapped.csv` 연동)
   - 빠른 선택 버튼 지원 (`전체`, `6억 이하`, `12억 이하` - 세제 혜택 툴팁 제공)
   - **필터 동작 방식**:
     - **단독 사용 시**: 해당 단지 전체 평형 중에서 **최고 공시가격**이 필터 범위에 포함되는지 확인합니다.
     - **전용면적 필터와 동시 사용 시**: 선택한 전용면적 범위에 속하는 평형들 각각의 최고 공시가격 중 하나라도 필터 범위에 포함되는지 확인합니다.

모든 차트와 통계는 필터 결과에 실시간으로 반응합니다.

#### 상단 요약 지표 (KPI 카드)
| 지표 | 설명 |
|------|------|
| 총 아파트 수 | 필터 조건에 해당하는 단지 수 |
| 평균 세대 수 | 단지당 평균 세대 수 |
| 연식 중앙값 | 준공연도 기준 중앙값으로 계산한 평균 연식 |

#### 탭별 시각화

**🎯 탭 1 — 아파트 비교**
- 단지명 텍스트 검색으로 특정 아파트 선택
- 선택한 아파트의 주요 지표가 전체 데이터 대비 몇 번째 백분위(percentile)에 위치하는지 레이더 차트로 시각화
- 레이더 차트 축 항목:
  | 축 | 설명 |
  |----|------|
  | 연식 (신축도) | 준공연도 기준 — 새로울수록 높은 백분위 |
  | 세대 수 | 단지 세대 수 백분위 |
  | 세대당 주차대수 | (지상+지하 주차대수) ÷ 세대수 백분위 |
  | 브랜드 점수 | 시공사/브랜드 가치 점수 백분위 (`apt_brand.csv` 연동) |
  | 역세권 점수 | 도보 소요시간 기반 기본 점수 × 지하철 노선 가치 가중치 백분위 (`subway_score.csv` 연동) |
  | 초품아 점수 | 초등학교까지의 보행 거리(m) 기반 접근성 점수 백분위 (`초등학교_도보통학권_아파트_정보.csv` 연동) |
- 각 축의 값은 0~100 사이의 백분위 점수로 표시
- 선택 아파트 정보(단지명, 주소, 준공연도, 세대수, 브랜드 점수, 역세권, 초품아 접근성)를 카드형 요약으로 함께 표시
- 각 지표별 실제 값과 백분위를 보여주는 상세 데이터 표 제공

**📅 탭 2 — 연도별 준공 현황**
- Fun Fact 카드: 가장 오래된 아파트 / 가장 새로운 아파트 / 중간 연식 아파트
- 이중 축 차트: 연도별 준공 아파트 수(꺾은선) + 세대 수(막대)

**🏢 탭 3 — 단지 규모 현황**
- Fun Fact 카드: 가장 큰 단지 / 가장 작은 단지 / 중간 규모 단지
- 세대수 구간별(200세대 이하, 200~500세대 등) 아파트 단지 분포를 막대 차트로 표시

**📄 탭 4 — 필터링 데이터 목록**
- 현재 사이드바 필터 조건에 해당하는 아파트 데이터 전체 목록을 데이블 형태로 제공

#### 원본 데이터 조회
- `📄 원본 데이터 보기` 확장 패널에서 필터된 데이터 테이블 조회 가능

#### `apt_brand.csv` — 브랜드 점수 데이터
- 주요 아파트 브랜드별 선호도/가치 점수를 저장한 기준 데이터
- **필드 구성**: `brand_name` (브랜드명), `score` (점수, 1~5점)
- 단지명(`kaptName`)에 해당 브랜드명이 포함되어 있을 경우 해당 점수를 부여 (기본값: 2점)

#### `subway_score.csv` — 지하철 노선 가중치 데이터
- 호선별 선호도 및 노선 가치를 점수화한 가중치 데이터 (예: 2/9/신분당선은 1.5배, 경의중앙선은 0.8배)
- 역세권 점수 계산 시, 선택 아파트 인근에 여러 노선이 겹칠 경우 가장 높은 가중치(`max_multiplier`)를 기본 점수(도보 시간 기준)에 곱하여 최종 산출합니다.

#### 역세권 점수 (Station Area Score)
- `apt_detail.csv`의 `kaptdWtimesub` (지하철역 소요시간) 필드 및 추가 검증 데이터의 직선거리를 기반으로 점수화
  - '5분이내' 또는 직선거리 250m 이내: 5점
  - '5~10분이내' 또는 직선거리 500m 이내: 4점
  - '10~15분이내' 또는 직선거리 750m 이내: 3점
  - '15~20분이내' 또는 직선거리 1000m 이내: 2점
  - 기타/정보없음: 1점

#### 역세권 공동주택 실거래정보 (`SUBSTAREA_APHUS_ACTRANSCT_INFO`) [추가 검증 데이터]
- **데이터 소스**: [국가교통 데이터 오픈마켓 - 역세권 공동주택 실거래정보](https://www.bigdata-transportation.kr/frn/prdt/detail?prdtId=PRDTNUM_000000020052)
- **목적**: 기존 `apt_detail.csv`의 역세권 정보를 추가 검증하고, 실제 실거래가(매매/전세/월세)와 인접 지하철역 간의 직선거리 등을 종합적으로 분석하기 위한 보조 데이터로 활용.
- **주요 필드 구성**:
  | 필드명 (영문) | 필드명 (한글) | 설명 |
  |---------------|---------------|------|
  | `SIGNGU_CD` | 시군구코드 | 시군구 코드 |
  | `EMDL_CD` | 읍면동리코드 | 법정동 기준 읍면동리 코드 |
  | `ADRES_NM` | 주소명 | 법정동 기준 주소명 |
  | `HOUSE_TYPE` | 주택유형 | 아파트, 연립, 다세대, 오피스텔 |
  | `HSMP_NM` | 단지명 | 건물/단지 명칭 |
  | `TRNS_CLSF` | 거래구분 | 매매, 전세, 월세 |
  | `TRAMT` | 거래금액 | 매매금액 (만원 단위) |
  | `ASSRNC_AMT` | 보증금액 | 보증금액 (만원 단위) |
  | `MTHT_AMT` | 월세금액 | 월세금액 (만원 단위) |
  | `NRB_SWST_NM` | 인접지하철역명 | 인접한 지하철역 명칭 |
  | `NRB_SWST_DSTNC`| 인접지하철역거리 | 인접 지하철역까지의 직선거리(m) |

#### 초등학교 도보통학권 아파트 정보 [초품아 데이터]
- **데이터 소스**: [국가교통 데이터 오픈마켓 - 초등학교 도보통학권 아파트 정보](https://www.bigdata-transportation.kr/frn/prdt/detail?prdtId=PRDTNUM_000000020278)
- **목적**: 아파트에서 가장 가까운 초등학교까지의 보행 거리 데이터를 활용하여, 학군 접근성(초품아 점수)을 산출하고 백분위 비교 레이더 차트 등에 활용.
- **주요 필드 구성**:
  | 필드명 | 설명 |
  |--------|------|
  | `apt_cd` | 아파트 단지 자체 코드 |
  | `apt_nm` | 아파트 단지명 |
  | `pnu` | 필지 고유번호 (19자리) |
  | `tllbadd` | 지번 주소 |
  | `schul_nm` | 초등학교명 |
  | `schul_dstnc` | 초등학교까지의 보행 거리 (단위: m) |

#### 초품아 점수 (Elementary School Proximity Score)
- `초등학교_도보통학권_아파트_정보.csv`의 `schul_dstnc` (초등학교 보행 거리) 필드를 기반으로 1~5점으로 점수화:
  - 도보 250m 이내: 5점
  - 도보 500m 이내: 4점
  - 도보 750m 이내: 3점
  - 도보 1000m 이내: 2점
  - 기타/비매핑/거리가 더 먼 경우: 1점

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.12+ |
| 패키지 관리 | `uv` |
| 데이터 처리 | `pandas` |
| 시각화 | `plotly` |
| 대시보드 | `streamlit` |
| 데이터 소스 | 공공데이터포털 API (아파트 정보), 국토교통부 (주택 공시가격 정보) |

---

## 데이터 흐름

```
 공공데이터포털 API
        │
        ▼
  get_list.py  ──→  apt_list.csv   (~21,900 단지)
                          │
                          ▼
   get_detail.py ──┬→ apt_basic.csv   (기본 정보)
                  └→ apt_detail.csv  (상세 정보)
  apt_brand.csv  ───→ (브랜드 점수 매핑)
  주택공시가격(CSV) ─→ extract_price.py ──→ apt_price_mapped.csv
                                           │
  역세권 실거래정보 ───────────────────────┤ (역세권 정보 추가 검증)
  초등학교 도보통학권 정보 ────────────────┤ (초품아 점수 산출)
                                           ▼
 ### Brand & Station Area Score Implementation
- Created [apt_brand.csv](file:///c:/Users/trimi/my-apartement/apt_brand.csv) with defined scores for major Korean apartment brands.
- Updated [main.py](file:///c:/Users/trimi/my-apartement/main.py) to:
    - Automatically assign brand scores by matching `kaptName` with the brand list.
    - Implement "**Station Area Score**" (역세권 점수) by mapping subway proximity (`kaptdWtimesub`) to 1-5 points.
    - Include both Brand and Station Area scores as new axes in the radar chart.
    - Display scores in the apartment information card and percentile table.
         main.py (Streamlit 대시보드)
```

---

## 실행 방법

```bash
# 1. 의존성 설치
uv sync

# 2. 데이터 수집 (최초 1회 또는 갱신 시)
uv run get_list.py
uv run get_detail.py

# 3. 대시보드 실행
uv run streamlit run main.py
```

> **환경 변수**: 공공데이터포털 서비스키를 `.env` 파일의 `SERVICE_KEY`에 설정해야 합니다.
