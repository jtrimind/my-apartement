import os
import requests
import csv
import time
from dotenv import load_dotenv
from urllib.parse import unquote

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

def fetch_apt_list(page_no=1, num_of_rows=100):
    """
    공공데이터포털 API를 호출하여 아파트 목록을 가져옵니다.
    """
    url = "https://apis.data.go.kr/1613000/AptListService3/getTotalAptList3"
    
    # .env에 저장된 서비스키는 이미 인코딩되어 있을 수 있으므로 디코딩하여 사용합니다.
    # requests가 파라미터를 다시 인코딩하기 때문입니다.
    service_key = unquote(os.getenv("SERVICE_KEY"))
    
    params = {
        "serviceKey": service_key,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "_type": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching page {page_no}: {e}")
        return None

def main():
    print("Starting apartment list crawling...", flush=True)
    
    all_items = []
    page_no = 1
    num_of_rows = 100
    
    # 첫 번째 페이지를 가져와 전체 개수를 확인합니다.
    first_page = fetch_apt_list(page_no, num_of_rows)
    if not first_page or 'response' not in first_page:
        print("Failed to fetch the initial data.")
        return
    
    body = first_page.get('response', {}).get('body', {})
    total_count = body.get('totalCount', 0)
    print(f"Total apartments to fetch: {total_count}", flush=True)
    
    items = body.get('items', [])
    if isinstance(items, dict):
        items = items.get('item', [])
    
    all_items.extend(items)
    
    # 나머지 페이지들을 가져옵니다.
    while len(all_items) < total_count:
        page_no += 1
        print(f"Fetching page {page_no}... ({len(all_items)}/{total_count})", flush=True)
        
        data = fetch_apt_list(page_no, num_of_rows)
        if not data:
            break
            
        items = data.get('response', {}).get('body', {}).get('items', [])
        if isinstance(items, dict):
            items = items.get('item', [])
            
        if not items:
            break
            
        all_items.extend(items)
        time.sleep(0.1)

    print(f"Successfully fetched {len(all_items)} items.")
    
    # CSV 파일로 저장합니다.
    if all_items:
        filename = "apt_list.csv"
        keys = all_items[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_items)
            
        print(f"Data saved to {filename}")
    else:
        print("No data to save.")

if __name__ == "__main__":
    main()
