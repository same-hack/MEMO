import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any

DOC_URL = "https://www.data.jma.go.jp/developer/xml/data/20260206002624_0_VXSE53_010000.xml"

# 名前空間（JMA XMLは名前空間が多いので必須）
NS = {
    "j": "http://xml.kishou.go.jp/jmaxml1/",
    "ib": "http://xml.kishou.go.jp/jmaxml1/informationBasis1/",
    "seis": "http://xml.kishou.go.jp/jmaxml1/body/seismology1/",
    "eb": "http://xml.kishou.go.jp/jmaxml1/elementBasis1/",
}

def fetch_xml(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JMA-XML-fetch/1.0)",
        "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text

def text_at(root: ET.Element, path: str) -> Optional[str]:
    el = root.find(path, NS)
    return el.text.strip() if el is not None and el.text else None

def parse_coordinate(coord_text: Optional[str]) -> Dict[str, Any]:
    """
    例: "+36.8+138.6-10000/" をパース
    - lat: 36.8
    - lon: 138.6
    - depth_m: 10000 (正の深さとして返す)
    """
    if not coord_text:
        return {}
    s = coord_text.strip().rstrip("/")  # "+36.8+138.6-10000"
    # 形式: +lat +lon -depth
    # lat: 先頭の'+'から次の'+'まで
    try:
        # '+36.8+138.6-10000'
        # 2つ目の'+'位置
        p2 = s.find("+", 1)
        # depthの'-'位置（lonの後）
        p3 = s.find("-", p2 + 1)
        lat = float(s[1:p2])
        lon = float(s[p2+1:p3])
        depth_m = abs(int(float(s[p3:])))  # "-10000" -> 10000
        return {"lat": lat, "lon": lon, "depth_m": depth_m}
    except Exception:
        return {"raw": coord_text}

def main():
    xml = fetch_xml(DOC_URL)
    root = ET.fromstring(xml)

    # Control
    control_title = text_at(root, "j:Control/j:Title")
    control_dt = text_at(root, "j:Control/j:DateTime")

    # Head
    report_dt = text_at(root, "ib:Head/ib:ReportDateTime")
    target_dt = text_at(root, "ib:Head/ib:TargetDateTime")
    event_id = text_at(root, "ib:Head/ib:EventID")
    info_type = text_at(root, "ib:Head/ib:InfoType")
    headline = text_at(root, "ib:Head/ib:Headline/ib:Text")

    # Body (Earthquake)
    origin_time = text_at(root, "seis:Body/seis:Earthquake/seis:OriginTime")
    area_name = text_at(root, "seis:Body/seis:Earthquake/seis:Hypocenter/seis:Area/seis:Name")
    coord_raw = text_at(root, "seis:Body/seis:Earthquake/seis:Hypocenter/seis:Area/eb:Coordinate")
    mag = text_at(root, "seis:Body/seis:Earthquake/eb:Magnitude")

    coord = parse_coordinate(coord_raw)

    # アプリで使いやすい形にまとめる（ここが重要）
    data = {
        "source": "JMA",
        "type": "earthquake",
        "title": control_title,
        "control_datetime": control_dt,
        "report_datetime": report_dt,
        "target_datetime": target_dt,
        "event_id": event_id,
        "info_type": info_type,
        "headline": headline,
        "earthquake": {
            "origin_time": origin_time,
            "hypocenter": {
                "name": area_name,
                **coord,
            },
            "magnitude": mag,
        },
        "raw_xml_url": DOC_URL,
    }

    # コンソールにJSONっぽく表示（本番はAPIレスポンスにする）
    import json
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
