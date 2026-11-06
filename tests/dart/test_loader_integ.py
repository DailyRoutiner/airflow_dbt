from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import AlreadyExists
from include.dart.loader import build_volume_path, to_jsonl, upload_to_volume
import pytest
import os

TEST_PATH =  build_volume_path("_test", "overwrite")
ROWS = [
 {"corp_code": "00126380", "corp_name": "삼성전자"},
  {"corp_code": "99999999", "corp_name": "unknown"}
]

ADD_ROW= [
    {"corp_code": "00164779", "corp_name": "SK하이닉스"}
]

pytestmark = pytest.mark.skipif(not os.environ.get("DATABRICKS_HOST") or not os.environ.get("DATABRICKS_TOKEN"), reason="DATABRICKS_HOST, DATABRICKS_TOKEN 환경변수 필요")


def test_upload_to_volume():
    
    client = WorkspaceClient()

    # 2건 업로드 
    upload_to_volume(client, to_jsonl(ROWS), TEST_PATH)
    assert client.files.download(TEST_PATH).contents.read() == to_jsonl(ROWS)

    # 1건 덮어쓰기
    upload_to_volume(client, to_jsonl(ADD_ROW), TEST_PATH)
    assert client.files.download(TEST_PATH).contents.read() == to_jsonl(ADD_ROW)

    # OverWrite = False 에러? 
    with pytest.raises(AlreadyExists) as e: # 예외 발생시키는 코드 테스트
        upload_to_volume(client, to_jsonl(ROWS), TEST_PATH, overwrite=False)
    


    
    # except AlreadyExists as e:
        # print(" Overwrite 실패: ", type(e).__name__, e )
        
    assert client.files.download(TEST_PATH).contents.read() == to_jsonl(ADD_ROW)

    # 빈 bytes
    upload_to_volume(client, b'', TEST_PATH)

    assert client.files.download(TEST_PATH).contents.read() == b''

    client.files.delete(TEST_PATH)