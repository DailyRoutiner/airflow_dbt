"""DART OPEN API 클라이언트 """
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError
import os
import xml.etree.ElementTree as ET
import time


BASE_URL = "https://opendart.fss.or.kr/api"
MAX_ATTEMPTS = 3 # 최대 시도 횟수

RETRYABLE_STATUS = {
    "800": "시스템 점검으로 인한 정지",
    "900": "정의되지 않은 오류",
}
RETRYABLE_HTTP = {
    429 : "Too Many Requests",
    503 : "Service Unavailable",
    504 : "Gateway Timeout",
    502 : "Bad Gateway",
    500 : "Internal Server Error",
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

        for attempt in range(0, MAX_ATTEMPTS):
            try:
                resp = self.session.get(url=api_url, params=params, timeout=(5,30))
                resp.raise_for_status()
                return resp
            except HTTPError as e :
                code = e.response.status_code
                if attempt == MAX_ATTEMPTS -1  or code not in RETRYABLE_HTTP:
                    # 400/500 번대 HTTP 에러 발생
                    print(f"[HTTP Error]- {code} : {e}")
                    raise
                
                wait = 2 ** attempt 
                print(f"[Retry] {code}, {wait} 초 후 재시도 {attempt + 1 }/{MAX_ATTEMPTS}")
                time.sleep(wait)
            except (Timeout, ConnectionError) as e:
                if attempt == MAX_ATTEMPTS - 1:
                    print(f"Time Out or Connection Error: {e}" )
                    raise
                wait = 2 ** attempt
                print(f"[Retry] {type(e).__name__} {wait} 초 후 재시도 {attempt + 1 }/{MAX_ATTEMPTS}" )
                time.sleep(wait)    


    def _raise_for_status(self, status:str, message:str, endpoint:str) -> None:
        if status in FATAL_STATUS:
            raise DartApiError(status, message, endpoint, retry=False)
        if status in RETRYABLE_STATUS:
            raise DartApiError(status, message, endpoint, retry=True)
        raise DartApiError(status, message, endpoint )

    
    # get_json, get_dict 을 위한 공통 함수
    def _get_payload(self, endpoint: str, **params) -> dict | None:
        """ 요청+status 확인. 정상이면 응답 dict 전체, 데이터 없으면 None"""
        resp= self._request(endpoint=endpoint, **params)
        payload = resp.json()
        status = payload.get("status")

        # status 체크
        if status == SUCCESS_STATUS:
            return payload
        if status == NO_DATA_STATUS:
            return None                 # 데이터 없음
        self._raise_for_status(status, payload.get("message", ""), endpoint)


    def get_json(self, endpoint:str, **params) -> list[dict]:
        """JSON 응답 파싱, status 확인하고 list 리턴"""
        payload = self._get_payload(endpoint, **params)

        if payload is None:
            return []
        
        return payload.get("list", [])

    def get_dict(self, endpoint: str, **params) -> dict | None:
        """ 단건 응답"""
        payload = self._get_payload(endpoint, **params)

        return payload


  

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

    from pathlib import Path
    from include.dart.corp_code import parse_corp_zip, filter_listed    
    client = DartClient(os.environ['DART_API_KEY']) # os.environ['DART_API_KEY']
    # resp = client.get_json(endpoint="list.json", bgn_de="20260803", end_de="20260807", page_count="10")

    # print(client.get_dict('company.json', corp_code="00126380"))

    
    resp = client.get_zip(endpoint='corpCode.xml')
    Path("data").mkdir(parents=True, exist_ok=True) 
    path = Path("data") / "corpCode.zip"
    print( path)


    with open(path, "wb") as f:
        f.write(resp)


    list_corp = parse_corp_zip(path.read_bytes())
    filtered_list  = filter_listed(list_corp)
    print(len(list_corp), len(filtered_list ))

    #print(resp[:300])


