"""한국관광공사 TourAPI - 지역별 관광행사 정보 수집 스크립트"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

BASE_URL = os.environ.get(
    "TOUR_API_BASE_URL",
    "https://apis.data.go.kr/B551011/KorService2/searchFestival2",
)
SERVICE_KEY = os.environ.get("TOUR_API_KEY", "")

AREA_CODES = {
    "1": "서울",
    "2": "인천",
    "3": "대전",
    "4": "대구",
    "5": "광주",
    "6": "부산",
    "7": "울산",
    "8": "세종",
    "31": "경기",
    "32": "강원",
    "33": "충북",
    "34": "충남",
    "35": "경북",
    "36": "경남",
    "37": "전북",
    "38": "전남",
    "39": "제주",
}

NUM_OF_ROWS = 100


def fetch_page(event_start_date: str, area_code: str, page_no: int) -> dict:
    params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalCollector",
        "_type": "json",
        "eventStartDate": event_start_date,
        "areaCode": area_code,
        "arrange": "A",
        "numOfRows": str(NUM_OF_ROWS),
        "pageNo": str(page_no),
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_festivals(event_start_date: str, area_code: str) -> list:
    items = []
    page = 1
    while True:
        try:
            data = fetch_page(event_start_date, area_code, page)
        except Exception as e:
            print(f"  [ERROR] area={area_code}, page={page}: {e}")
            break

        body = data.get("response", {}).get("body", {})
        total = body.get("totalCount", 0)
        if total == 0:
            break

        raw_items = body.get("items", {}).get("item", [])
        if isinstance(raw_items, dict):
            raw_items = [raw_items]
        items.extend(raw_items)

        if len(items) >= total:
            break
        page += 1
        time.sleep(0.3)

    return items


def main():
    if not SERVICE_KEY:
        print("ERROR: TOUR_API_KEY 환경변수를 설정해주세요.")
        sys.exit(1)

    today = datetime.now()
    event_start_date = today.strftime("%Y%m%d")
    date_label = today.strftime("%Y-%m-%d")

    print(f"=== 관광행사 정보 수집 ({date_label}) ===")

    all_festivals = []
    for code, name in sorted(AREA_CODES.items(), key=lambda x: x[1]):
        print(f"  [{name}] 수집 중...")
        festivals = fetch_all_festivals(event_start_date, code)
        for f in festivals:
            f["areaName"] = name
        all_festivals.extend(festivals)
        print(f"  [{name}] {len(festivals)}건")
        time.sleep(0.5)

    print(f"\n총 {len(all_festivals)}건 수집 완료")

    # 날짜별 디렉토리에 저장
    output_dir = os.path.join(os.path.dirname(__file__), "data", today.strftime("%Y"), today.strftime("%m"))
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"festivals_{today.strftime('%Y%m%d')}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "collectedAt": today.isoformat(),
                "eventStartDate": event_start_date,
                "totalCount": len(all_festivals),
                "items": all_festivals,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"저장 완료: {output_file}")

    # 최신 데이터 심볼릭 파일 (latest.json)
    latest_file = os.path.join(os.path.dirname(__file__), "data", "latest.json")
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "collectedAt": today.isoformat(),
                "eventStartDate": event_start_date,
                "totalCount": len(all_festivals),
                "items": all_festivals,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    main()
