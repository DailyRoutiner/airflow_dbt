"""DART OPEN API 클라이언트 """
import requests
import os
import xml.etree.ElementTree as ET

BASE_URL = "https://opendart.fss.or.kr/api"


RETRYABLE_STATUS = {
    "800": "시스템 점검으로 인한 정지",
    "900": "정의되지 않은 오류",
}
FATAL_STATUS= {
    # 010, 011, 012 
    "010": "등록되지 않은 키",
    "011": "사용할 수 없는 키",
    "012": "접근할 수 없는 IP",
    "020": "요청 제한 초과(일일 한도 소진)",
    "021": "조회 가능한 회사 개수 초과",
    "100": "필드의 부적절한 값",
    "101": "부적절한 접근",
}
SUCCESS_STATUS = "000"
NO_DATA_STATUS = "013"


class DartApiError(Exception):
    def __init__(self, status:str, message:str="", endpoint:str="", retry:bool =False):
        self.status = status
        self.endpoint = endpoint
        self.retry = retry
        super().__init__(f"[{status}] {message} (endpoint={endpoint})")


class DartClient:
    def __init__(self, api_key:str, base_url: str=BASE_URL):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()  # 연결 재사용


    @classmethod
    def from_conn(cls, conn_id:str="dart_api"):

        from airflow.sdk import BaseHook
        conn = BaseHook.get_connection(conn_id)

        # 이부분을 잘 모르겠음.
        return cls(api_key=conn.password)

    
    def _request(self, endpoint: str, **params) -> requests.Response:
        """ Status 거쳐가는 응답 URL, 키 주입 """

        api_url = f"{self.base_url}/{endpoint}"
        
        params["crtfc_key"] = self.api_key
        
        return self.session.get(url=api_url, params=params, timeout=30)


    def _raise_for_status(self, status:str, message:str, endpoint:str) -> None:
        if status in FATAL_STATUS:
            raise DartApiError(status, message, endpoint, retry=False)
        if status in RETRYABLE_STATUS:
            raise DartApiError(status, message, endpoint, retry=True)
        raise DartApiError(status, message, endpoint )    


    def get_json(self, endpoint:str, **params) -> list[dict]:
        """JSON 응답 파싱, status 확인하고 list 리턴"""
        resp= self._request(endpoint=endpoint, **params)
        payload = resp.json()
        status = payload.get("status")

        # status 체크
        if status == SUCCESS_STATUS:
            return payload.get("list", [])  # resp.json()['list'] 이렇게 쓰지 말것
        if status == NO_DATA_STATUS:
            return []
        self._raise_for_status(status, payload.get("message", ""), endpoint)
  

    def get_zip(self, endpoint:str, **params) -> bytes:
        """ CorpCode.xml 처럼 ZIP 바이너리로 주는 용"""
        resp = self._request(endpoint=endpoint, **params)

        # ZIP인지 확인
        if resp.content.startswith(b"PK"):
            return resp.content

        # ZIP이 아니면 raise
        root = ET.fromstring(resp.content)
        status = root.findtext("status")
        message = root.findtext("message") or ""
        self._raise_for_status(status, message, endpoint)


if __name__ == "__main__":
    client = DartClient(os.environ['DART_API_KEY']) # os.environ['DART_API_KEY']
    # resp = client.get_json(endpoint="list.json", bgn_de="20260803", end_de="20260807", page_count="10")
    # print(resp)

    resp = client.get_zip(endpoint='corpCode.xml')
    print(resp[:300])

