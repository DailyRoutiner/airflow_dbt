""" 
1. API 응답 행(list[dict]) -> JSONL으로 변환
2. JSONL을 Volume에 적재

- 적재 전략: delete 단위 = 파일 단위 항상 덮어씀
- 0건이여도 파일을 올려야 하는 이유는 수행했는데, 건너뛰면 이전 데이터가 남아있어 원천과 달라진다.

"""
import json
import io


# Volume Root는 상수
VOLUME_ROOT = "/Volumes/workspace/analytics_raw/dart_landing"

def build_volume_path(table: str,  *parts: str) -> str:
    """ table은 확장자 없이 ('disclosure'), parts는 하위 폴더/파일명 """
    path = "/".join([VOLUME_ROOT, table, *parts])
    path += ".jsonl"
    return path

def to_jsonl(rows: list[dict]) -> bytes:
    
    json_list = [json.dumps(row, ensure_ascii=False) for row in rows]
    
    json_bytes = "\n".join(json_list).encode("utf-8")

    return json_bytes

def upload_to_volume(client, data:bytes, path:str, overwrite: bool = True):
    file = io.BytesIO(data)

    client.files.upload(file_path=path, contents=file, overwrite=overwrite)


def get_workspace_client(conn_id: str = "dbt-db"):
    # 함수 안에서 import 
    from airflow.sdk import BaseHook    # 3 버전
    from databricks.sdk import WorkspaceClient

    conn = BaseHook.get_connection(conn_id)
    return WorkspaceClient(host=conn.host, token=conn.password)


def load_to_volume(client, rows:list[dict], table:str, *parts: str):
    """ rows -> JSONL -> Volume 업로드. 업로드한 경로를 반환"""
    path = build_volume_path(table, *parts) # 펼쳐서 넘겨?
    data = to_jsonl(rows)
    upload_to_volume(client, data, path)
    return path
