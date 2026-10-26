""" 
client.get_json()          loader (5-2)                 loader (5-3)
  응답 dict  ──▶  JSON 파일로 Volume에 업로드  ──▶  REPLACE WHERE  ──▶  raw_dart_* 테이블
                 /Volumes/.../company/2026-10-22/...jsonl


"""
import json
import io
from databricks.sdk import WorkspaceClient

# Volume Root는 상수
VOLUME_ROOT = "/Volumes/workspace/analytics_raw/dart_landing"

def build_volume_path(endpoint: str,  *parts) -> str:
    """ endpoint는 확장자 없이 ('company'), parts는 하위 폴더/파일명 """
    path = "/".join([VOLUME_ROOT, endpoint, *parts])
    path += ".jsonl"
    return path

def to_jsonl(rows) -> bytes:
    json_list = []
    for row in rows:
        row_str = json.dumps(row, ensure_ascii=False)
        json_list.append(row_str)
    
    json_bytes = "\n".join(json_list).encode("utf-8")

    return json_bytes

def upload_to_volume(client, data:bytes, path:str):
    # 1. Data 0건인지 확인 -> 비었으면 로그 남기고 False
    file = io.BytesIO(data)
    client.files.upload(file_path=path, contents=file, overwrite=True)

    

if __name__ == "__main__":
    print(build_volume_path("company", "2026-10-22", "00126380"))