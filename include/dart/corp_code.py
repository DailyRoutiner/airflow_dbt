""" CorpCode.xml 파싱 후 CSV 생성(기업 고유번호)"""
import io
import csv
import zipfile 
import xml.etree.ElementTree as ET

def parse_corp_zip(raw:bytes) -> list[dict]:
    """ ZIP 바이트 를 list로 변환. corp_code, corp_name, stock_code 딕셔너리 리스트 """
    # io.BytesIO 로 감싸 zipfile.ZipFile 열기
    file = io.BytesIO(raw)
    with zipfile.ZipFile(file) as zf:
        xml_bytes = zf.read(zf.namelist()[0])
    
    # ET.fromstring(bytes) 파싱 후 root.iter("list") 순회
    root = ET.fromstring(xml_bytes)
    rows = []
    for item in root.iter("list"):
        corp_dict = {
            "corp_code" : item.findtext("corp_code", default="").strip(),
            "corp_name" : item.findtext("corp_name", default="").strip(),
            "stock_code" : item.findtext("stock_code", default="").strip(), # 공백 제거
        }
        
        rows.append(corp_dict)

    return rows

def filter_listed(rows: list[dict]) -> list[dict]:
    """  종목코드 보유(상장폐지 포함 가능)"""

    # row에 "" 이면 False로 인식
    results = [row for row in rows if row['stock_code']]

    return results


def write_target_csv(rows: list[dict], roles: dict[str, str], path:str) -> None:
    """ 관심 종목만 골라 CSV로 저장"""

    targets = []
    for row in rows:
        if row['stock_code'] in roles:
            role = roles[row['stock_code']]
            targets.append({**row, "role": role})

    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["corp_code", "corp_name", "stock_code", "role"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(targets)

