import json
import pytest
from unittest.mock import MagicMock 

from include.dart.loader import build_volume_path, to_jsonl, load_to_volume, build_copy_sql


ROWS = [
 {"corp_code": "00126380", "corp_name": "삼성전자"},
  {"corp_code": "99999999", "corp_name": "unknown"}
]
VOLUME_ROOT = "/Volumes/workspace/analytics_raw/dart_landing"

@pytest.mark.parametrize(
        "args, expected",
        [
            (("disclosure", "2026-10-22"), f"{VOLUME_ROOT}/disclosure/2026-10-22.jsonl"),
            (("company", "2026-10-22"), f"{VOLUME_ROOT}/company/2026-10-22.jsonl"),
            (("fin_stmt", "00126380", "2025", "11011"), f"{VOLUME_ROOT}/fin_stmt/00126380/2025/11011.jsonl"),
            (("company",), f"{VOLUME_ROOT}/company.jsonl"),
        ],
)
def test_build_volume_path(args, expected):
    """ parts 있을 때와 없을 때 잘 동작 하는가"""

    # 케이스 1,2,3,4
    assert build_volume_path(*args) == expected


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


def test_load_to_volume():
    client = MagicMock()
    rows = [{"corp_code": "00126380"}]

    path = load_to_volume(client, rows, "company", "2026-10-28")

    assert path == "/Volumes/workspace/analytics_raw/dart_landing/company/2026-10-28.jsonl"

    client.files.upload.assert_called_once()
    kwargs = client.files.upload.call_args.kwargs
    assert kwargs["file_path"] == path

    assert kwargs['contents'].read() == to_jsonl(rows)
    # 0건이여도 호출되나?
    load_to_volume(client, [], "company", "x")
    assert client.files.upload.call_count == 2

def test_build_copy_sql():
    table = 'company'
    path = build_volume_path(table)

    sql = build_copy_sql(table, path)

    assert "COPY INTO workspace.analytics_raw.company" in sql
    assert "FROM '/Volumes/workspace/analytics_raw/dart_landing/company.jsonl'" in sql
    assert "FILEFORMAT = JSON" in sql
    assert "force" not in sql
