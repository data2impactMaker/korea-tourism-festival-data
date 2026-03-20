"""한국관광공사 TourAPI - 지역별 관광행사 정보 수집 스크립트"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

BASE_URL = os.environ.get(
    "TOUR_API_BASE_URL",
    "https://apis.data.go.kr/B551011/KorService2/searchFestival2",
)
SERVICE_KEY = os.environ.get("TOUR_API_KEY", "")

# 법정동 시도코드 → 지역명 매핑 (lDongRegnCd 기준)
LDONG_CODES = {
    "11": "서울", "26": "부산", "27": "대구", "28": "인천", "29": "광주",
    "30": "대전", "31": "울산", "36": "세종", "36110": "세종",
    "41": "경기", "42": "강원", "43": "충북", "44": "충남",
    "45": "전북", "46": "전남", "47": "경북", "48": "경남",
    "50": "제주", "51": "강원", "52": "전북",
}

NUM_OF_ROWS = 100


def fetch_page(event_start_date: str, page_no: int) -> dict:
    params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalCollector",
        "_type": "json",
        "eventStartDate": event_start_date,
        "arrange": "A",
        "numOfRows": str(NUM_OF_ROWS),
        "pageNo": str(page_no),
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_festivals(event_start_date: str) -> list:
    items = []
    page = 1
    while True:
        try:
            data = fetch_page(event_start_date, page)
        except Exception as e:
            print(f"  [ERROR] page={page}: {e}")
            break

        body = data.get("response", {}).get("body", {})
        total = body.get("totalCount", 0)
        if total == 0:
            break

        raw_items = body.get("items", {}).get("item", [])
        if isinstance(raw_items, dict):
            raw_items = [raw_items]
        items.extend(raw_items)

        print(f"  {len(items)}/{total}건 수집...")
        if len(items) >= total:
            break
        page += 1
        time.sleep(0.3)

    return items


def enrich_area_name(items: list) -> list:
    for item in items:
        code = item.get("lDongRegnCd", "")
        item["areaName"] = LDONG_CODES.get(code, "기타")
    return items


def main():
    if not SERVICE_KEY:
        print("ERROR: TOUR_API_KEY 환경변수를 설정해주세요.")
        sys.exit(1)

    today = datetime.now()
    event_start_date = today.strftime("%Y%m%d")

    print(f"=== 관광행사 정보 수집 ({today.strftime('%Y-%m-%d')}) ===")

    festivals = fetch_all_festivals(event_start_date)
    festivals = enrich_area_name(festivals)

    print(f"\n총 {len(festivals)}건 수집 완료")

    # 지역별 통계
    area_counts = {}
    for f in festivals:
        name = f["areaName"]
        area_counts[name] = area_counts.get(name, 0) + 1
    for name, count in sorted(area_counts.items()):
        print(f"  [{name}] {count}건")

    # 날짜별 디렉토리에 저장
    output_dir = os.path.join(os.path.dirname(__file__), "data", today.strftime("%Y"), today.strftime("%m"))
    os.makedirs(output_dir, exist_ok=True)

    result = {
        "collectedAt": today.isoformat(),
        "eventStartDate": event_start_date,
        "totalCount": len(festivals),
        "items": festivals,
    }

    output_file = os.path.join(output_dir, f"festivals_{today.strftime('%Y%m%d')}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n저장: {output_file}")

    latest_file = os.path.join(os.path.dirname(__file__), "data", "latest.json")
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
