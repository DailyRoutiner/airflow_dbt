"""DART OPEN API 클라이언트 """
import requests
import os


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
    def __init__(self, status:str, message:str="", endpoint:str=""):
        self.status = status
        self.endpoint = endpoint
        super().__init__(f"[{status}] {message} (endpoint={endpoint})")
    


class DartClient:
    def __init__(self, base_url: str=BASE_URL):
        
        self.session = requests.Session() #  연결 재사용
        self.api_key = os.environ['DART_API_KEY']

    # @classmethod
    # def from_conn(cls, conn_id:str="dart_api"):
    #     from airflow.sdk import BaseHook
    #     conn = BaseHook.get_connection(conn_id)
    #     return cls(api_key=conn.password, base_url=conn.host or BASE_URL)

    def _request(self, endpoint: str, **params) -> requests.Response:
        """ Status 거쳐가는 응답, 키 주입 + 재시도 처리"""

        api_url = f"{BASE_URL}/{endpoint}"
        
        params["crtfc_key"] = self.api_key
        
        return self.session.get(url=api_url, params=params, timeout=30)

        

    def get_json(self, endpoint:str, **params) -> list[dict]:
        """JSON 응답 파싱, status 확인하고 list 리턴"""

        response= self._request(endpoint=endpoint, **params)

    def get_zip(self, endpoint:str, **params) -> bytes:
        """ CorpCode.xml 처럼 ZIP 바이너리로 주는 용"""


if __name__ == "__main__":
    client = DartClient()
    resp = client._request("list.json", bgn_de="20260803", end_de="20260807", page_count="10")
    print(resp.url)
    print(resp.json())


