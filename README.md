# Apartment Data Analysis Dashboard

`uv`와 `Streamlit`을 사용한 아파트 상세 데이터 분석 대시보드 프로젝트입니다. 공공데이터포털의 아파트 정보를 수집하고 시각화합니다.

## 프로젝트 구성
- `get_list.py`: 아파트 목록 API 데이터 수집
- `get_detail.py`: 아파트 상세 정보 API 데이터 수집
- `main.py`: Streamlit 기반 데이터 시각화 대시보드
- `apt_list.csv`, `apt_detail.csv`: 수집된 데이터 파일

## 설치 및 실행 방법

### 1. 필수 조건
- [uv](https://github.com/astral-sh/uv)가 설치되어 있어야 합니다.

### 2. 가상환경 구축 및 패키지 설치
프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 의존성을 설치합니다:
```bash
uv sync
```

### 3. 대시보드 실행
설치 완료 후 다음 명령어로 Streamlit 대시보드를 실행할 수 있습니다:
```bash
uv run streamlit run main.py
```

### 4. 데이터 수집 (필요시)
데이터를 새로 수집해야 하는 경우:
```bash
uv run get_list.py
uv run get_detail.py
```

## 주요 기능
- 행정구역(구) 및 준공 연도별 필터링
- 아파트 유형 및 난방 방식 분포 시각화
- 연도별 준공 현황 및 최고 층수 분포 분석
- 주요 건설사별 아파트 수 통계
