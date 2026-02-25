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
- **준공 연도 범위** 슬라이더
- **세대 수 범위** 슬라이더

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
  | 역세권 점수 | 지하철역 도보 소요시간 기반 점수 백분위 |
- 각 축의 값은 0~100 사이의 백분위 점수로 표시
- 선택 아파트 정보(단지명, 주소, 준공연도, 세대수, 브랜드 점수, 역세권)를 카드형 요약으로 함께 표시
- 각 지표별 실제 값과 백분위를 보여주는 상세 데이터 표 제공

**📅 탭 2 — 연도별 준공 현황**
- Fun Fact 카드: 가장 오래된 아파트 / 가장 새로운 아파트 / 중간 연식 아파트
- 이중 축 차트: 연도별 준공 아파트 수(꺾은선) + 세대 수(막대)

**🏢 탭 3 — 단지 규모 현황**
- 세대수 구간별(200세대 이하, 200~500세대 등) 아파트 단지 분포를 막대 차트로 표시

#### 원본 데이터 조회
- `📄 원본 데이터 보기` 확장 패널에서 필터된 데이터 테이블 조회 가능

#### `apt_brand.csv` — 브랜드 점수 데이터
- 주요 아파트 브랜드별 선호도/가치 점수를 저장한 기준 데이터
- **필드 구성**: `brand_name` (브랜드명), `score` (점수, 1~5점)
- 단지명(`kaptName`)에 해당 브랜드명이 포함되어 있을 경우 해당 점수를 부여 (기본값: 2점)

#### 역세권 점수 (Station Area Score)
- `apt_detail.csv`의 `kaptdWtimesub` (지하철역 소요시간) 필드를 기반으로 점수화
  - '5분이내': 5점
  - '5~10분이내': 4점
  - '10~15분이내': 3점
  - '15~20분이내': 2점
  - 기타/정보없음: 1점

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.12+ |
| 패키지 관리 | `uv` |
| 데이터 처리 | `pandas` |
| 시각화 | `plotly` |
| 대시보드 | `streamlit` |
| 데이터 소스 | 국토교통부 공공데이터포털 API |

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
                          │
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
