import json
import pytest
from unittest.mock import MagicMock 
from databricks.sdk.service.sql import StatementState

from include.dart.loader import build_volume_path, to_jsonl, load_to_volume, copy_into, run_sql


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

def test_copy_into():
    table = 'company'
    path = build_volume_path(table)

    sql = copy_into(table, path)

    assert "COPY INTO workspace.analytics_raw.raw_company" in sql
    assert "FROM '/Volumes/workspace/analytics_raw/dart_landing/company.jsonl'" in sql
    assert "FILEFORMAT = JSON" in sql
    assert "force" not in sql

def test_run_sql_failed():

    client = MagicMock()
    chain = client.statement_execution.execute_statement
    chain.return_value.status.state = StatementState.FAILED

    with pytest.raises(RuntimeError, match="FAILED"):
        run_sql(client, "test-wh", "select 1")

    kwargs = chain.call_args.kwargs
    assert kwargs["warehouse_id"] == "test-wh"
    assert kwargs["statement"] == "select 1"


def test_run_sql_success():

    client = MagicMock()
    chain = client.statement_execution.execute_statement
    chain.return_value.status.state = StatementState.SUCCEEDED

    
    run_sql(client, "test-wh", "select 1")

    kwargs = chain.call_args.kwargs
    assert kwargs["warehouse_id"] == "test-wh"
    assert kwargs["statement"] == "select 1"


def test_run_sql_timeout():

    client = MagicMock()
    chain = client.statement_execution.execute_statement
    chain.return_value.status.state = StatementState.RUNNING

    chain.return_value.status.error = None # Error 상황 가정

    with pytest.raises(RuntimeError, match="RUNNING"):
        run_sql(client, "test-wh", "select 1")


    kwargs = chain.call_args.kwargs
    assert kwargs["warehouse_id"] == "test-wh"
    assert kwargs["statement"] == "select 1"