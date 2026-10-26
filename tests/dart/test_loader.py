import json
from include.dart.loader import build_volume_path, to_jsonl


ROWS = [
 {"corp_code": "00126380", "corp_name": "삼성전자"},
  {"corp_code": "99999999", "corp_name": "unknown"}
]


def test_build_volume_path():
    """ parts 있을 때와 없을 때 잘 동작 하는가"""
    
    result1 = build_volume_path("company", "2026-10-22", "00126380")
    result2 = build_volume_path("company")

    assert result1 == "/Volumes/workspace/analytics_raw/dart_landing/company/2026-10-22/00126380.jsonl"
    assert result2 == "/Volumes/workspace/analytics_raw/dart_landing/company.jsonl"


def test_to_jsonl():
    """ bytes파일 decode로 읽어보기"""

    rows = ROWS
    result = to_jsonl(rows)

    assert to_jsonl([]) == b""
    assert isinstance(result, bytes)

    json_list = result.decode("utf-8").splitlines() 

    decoded_rows = [json.loads(row) for row in json_list]
    
    assert  decoded_rows == ROWS
    assert "삼성전자" in result.decode("utf-8")

