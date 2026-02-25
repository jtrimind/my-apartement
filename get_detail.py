import os
import requests
import csv
import time
import argparse
# from tqdm import tqdm
from dotenv import load_dotenv
from urllib.parse import unquote

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

def fetch_apt_basic(kapt_code):
    """
    공공데이터포털 API를 호출하여 아파트 기본 정보를 가져옵니다.
    """
    url = "https://apis.data.go.kr/1613000/AptBasisInfoServiceV4/getAphusBassInfoV4"
    service_key = unquote(os.getenv("SERVICE_KEY"))
    params = {"serviceKey": service_key, "kaptCode": kapt_code, "_type": "json"}
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        item = data.get('response', {}).get('body', {}).get('item', {})
        return item if item else None
    except Exception as e:
        print(f"Error fetching basic info for {kapt_code}: {e}")
        return None

def fetch_apt_detail(kapt_code):
    """
    공공데이터포털 API를 호출하여 아파트 상세 정보를 가져옵니다.
    """
    url = "https://apis.data.go.kr/1613000/AptBasisInfoServiceV4/getAphusDtlInfoV4"
    service_key = unquote(os.getenv("SERVICE_KEY"))
    params = {"serviceKey": service_key, "kaptCode": kapt_code, "_type": "json"}
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        item = data.get('response', {}).get('body', {}).get('item', {})
        return item if item else None
    except Exception as e:
        print(f"Error fetching detailed info for {kapt_code}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Fetch apartment details from Public Data Portal API.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of apartments to fetch.")
    args = parser.parse_args()

    input_filename = "apt_list.csv"
    basic_filename = "apt_basic.csv"
    detail_filename = "apt_detail.csv"
    
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return

    # 이미 처리된 kaptCode 목록 (기본/상세 각각 관리)
    processed_basic = set()
    if os.path.exists(basic_filename):
        with open(basic_filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader: processed_basic.add(row['kaptCode'])
            
    processed_detail = set()
    if os.path.exists(detail_filename):
        with open(detail_filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader: processed_detail.add(row['kaptCode'])
    
    # 아파트 목록 읽기 (둘 중 하나라도 안 되어 있으면 수집 대상)
    apt_list = []
    with open(input_filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['kaptCode'] not in processed_basic or row['kaptCode'] not in processed_detail:
                apt_list.append(row)

    if not apt_list:
        print("All items are already processed or the list is empty.")
        return

    if args.limit:
        apt_list = apt_list[:args.limit]
        print(f"Limiting to {args.limit} items.")

    print(f"Starting to fetch data for {len(apt_list)} apartments...")
    
    # 기본 정보 필드 리스트 (Spec 기준)
    BASIC_FIELDS = [
        "kaptCode", "kaptName", "kaptAddr", "codeSaleNm", "codeHeatNm", "kaptTarea", 
        "kaptDongCnt", "kaptdaCnt", "kaptBcompany", "kaptAcompany", "kaptTel", 
        "kaptUrl", "codeAptNm", "doroJuso", "codeMgrNm", "codeHallNm", "kaptUsedate", 
        "kaptFax", "hoCnt", "kaptMarea", "kaptMparea60", "kaptMparea85", 
        "kaptMparea135", "kaptMparea136", "privArea", "bjdCode", "kaptTopFloor", 
        "ktownFlrNo", "kaptBaseFloor", "kaptdEcntp", "zipcode"
    ]

    # 파일 열기 (Append 모드)
    with open(basic_filename, 'a' if os.path.exists(basic_filename) else 'w', newline='', encoding='utf-8-sig') as fb, \
         open(detail_filename, 'a' if os.path.exists(detail_filename) else 'w', newline='', encoding='utf-8-sig') as fd:
        
        basic_writer = None
        detail_writer = None
        
        for i, apt in enumerate(apt_list):
            kapt_code = apt['kaptCode']
            if (i + 1) % 10 == 0 or i == 0:
                print(f"Processing {i+1}/{len(apt_list)}: {kapt_code}...", flush=True)
            
            # 기본 정보 수집
            if kapt_code not in processed_basic:
                basic_info = fetch_apt_basic(kapt_code)
                if basic_info:
                    if basic_writer is None:
                        basic_writer = csv.DictWriter(fb, fieldnames=BASIC_FIELDS, extrasaction='ignore')
                        if fb.tell() == 0: basic_writer.writeheader()
                    basic_writer.writerow(basic_info)
            
            # 상세 정보 수집
            if kapt_code not in processed_detail:
                detail_info = fetch_apt_detail(kapt_code)
                if detail_info:
                    if detail_writer is None:
                        # 상세 정보는 API 결과의 키를 헤더로 사용 (기존 방식 유지하되 유연하게)
                        detail_writer = csv.DictWriter(fd, fieldnames=list(detail_info.keys()), extrasaction='ignore')
                        if fd.tell() == 0: detail_writer.writeheader()
                    detail_writer.writerow(detail_info)
                
            time.sleep(0.05)

    print(f"Finished. Data saved to {basic_filename} and {detail_filename}")

if __name__ == "__main__":
    main()
