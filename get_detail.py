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

def fetch_apt_detail(kapt_code):
    """
    공공데이터포털 API를 호출하여 아파트 상세 정보를 가져옵니다.
    """
    url = "https://apis.data.go.kr/1613000/AptBasisInfoServiceV4/getAphusBassInfoV4"
    
    service_key = unquote(os.getenv("SERVICE_KEY"))
    
    params = {
        "serviceKey": service_key,
        "kaptCode": kapt_code,
        "_type": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # API 응답 구조 확인
        item = data.get('response', {}).get('body', {}).get('item', {})
        if not item:
            return None
        return item
    except Exception as e:
        print(f"Error fetching kaptCode {kapt_code}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Fetch apartment details from Public Data Portal API.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of apartments to fetch.")
    args = parser.parse_args()

    input_filename = "apt_list.csv"
    output_filename = "apt_detail.csv"
    
    # 입력 파일 확인
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return

    # 이미 처리된 kaptCode 목록 가져오기
    processed_codes = set()
    if os.path.exists(output_filename):
        with open(output_filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_codes.add(row['kaptCode'])
    
    # 아파트 목록 읽기
    apt_list = []
    with open(input_filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['kaptCode'] not in processed_codes:
                apt_list.append(row)

    if not apt_list:
        print("All items in apt_list.csv are already processed or the list is empty.")
        return

    # 리미트 적용
    if args.limit:
        apt_list = apt_list[:args.limit]
        print(f"Limiting to {args.limit} items.")

    print(f"Starting to fetch details for {len(apt_list)} apartments...")
    
    results = []
    
    # 파일 쓰기 모드 결정 (이미 있으면 추가, 없으면 새로 생성)
    file_exists = os.path.exists(output_filename)
    
    with open(output_filename, 'a' if file_exists else 'w', newline='', encoding='utf-8-sig') as f:
        writer = None
        
        for i, apt in enumerate(apt_list):
            kapt_code = apt['kaptCode']
            if (i + 1) % 10 == 0 or i == 0:
                print(f"Processing {i+1}/{len(apt_list)}: {kapt_code}...", flush=True)
            detail = fetch_apt_detail(kapt_code)
            
            if detail:
                # 필드가 없으면 초기화
                if writer is None:
                    # 헤더 생성을 위해 detail의 키들을 사용
                    # 만약 파일이 이미 존재하면 헤더를 다시 쓰지 않음
                    keys = list(detail.keys())
                    writer = csv.DictWriter(f, fieldnames=keys)
                    if not file_exists:
                        writer.writeheader()
                    else:
                        # 기존 파일이 있는 경우, 필드명이 일치하는지 확인하거나
                        # 헤더를 정적으로 정의하는 것이 안전할 수 있음.
                        # 여기서는 단순화를 위해 첫 번째 성공한 item의 keys 사용.
                        pass
                
                try:
                    writer.writerow(detail)
                except ValueError:
                    # 가끔 API 응답 필드가 다를 수 있으므로 예외 처리
                    # 새로운 필드가 발견되면 대응하기 어렵기 때문에 pass 하거나 로깅
                    pass
                
            # API 부하 및 전송 속도 제한 고려
            time.sleep(0.05)

    print(f"Finished fetching details. Results saved to {output_filename}")

if __name__ == "__main__":
    main()
