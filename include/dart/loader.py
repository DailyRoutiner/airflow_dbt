""" 
1. API 응답(zip)을 JSONL 으로 변환
2. JSONL을 Volume에 적재

- 적재 전략: 날짜 단위 delete-insert 항상 덮어쓴다.
- 0건이여도 빈 파일을 올리는 이유

"""
import json
import io


# Volume Root는 상수
VOLUME_ROOT = "/Volumes/workspace/analytics_raw/dart_landing"

def build_volume_path(endpoint: str,  *parts) -> str:
    """ endpoint는 확장자 없이 ('company'), parts는 하위 폴더/파일명 """
    path = "/".join([VOLUME_ROOT, endpoint, *parts])
    path += ".jsonl"
    return path

def to_jsonl(rows) -> bytes:
    
    json_list = [json.dumps(row, ensure_ascii=False) for row in rows]
    
    json_bytes = "\n".join(json_list).encode("utf-8")

    return json_bytes

def upload_to_volume(client, data:bytes, path:str, overwrite: bool = True):
    file = io.BytesIO(data)

    client.files.upload(file_path=path, contents=file, overwrite=overwrite)


