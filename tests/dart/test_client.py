import pytest
from include.dart.client import DartClient, DartApiError
from requests.exceptions import HTTPError, Timeout

class FakeResponse:
    """ requests.Response 대역"""
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(response= self)

class FakeSession:
    """ session.get() 대역, 준비된 응답을 순서대로 돌려준다"""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, **kwargs):
        self.calls += 1
        item = self.responses.pop(0)
        # 예외인지 체크 
        if isinstance(item, Exception):
            raise item
        return item

def make_client(responses):
    """주어진 responses를 돌려주는 클라이언트"""
    client= DartClient(api_key="dummy")
    client.session = FakeSession(responses=responses)

    return client

def test_fake_response():
    ok = FakeResponse(200, {"status": "000"})
    ok.raise_for_status()

    bad = FakeResponse(503)
    with pytest.raises(HTTPError) as exc:
        bad.raise_for_status()

    assert exc.value.response.status_code == 503

def test_fake_session():
    session = FakeSession([FakeResponse(503), FakeResponse(200)])
    
    assert session.get(url="x").status_code == 503
    assert session.get(url="x").status_code == 200
    assert session.calls ==2
    

