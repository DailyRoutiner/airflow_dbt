import pytest
import time
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

# session 503, 200 test
def test_fake_session():
    session = FakeSession([FakeResponse(503), FakeResponse(200)])
    
    assert session.get(url="x").status_code == 503
    assert session.get(url="x").status_code == 200
    assert session.calls ==2

# 200 test
def test_request_success_first_try():
    # 준비
    client = make_client([FakeResponse(200)])

    # 활동 실행
    resp = client._request(endpoint="list.json")

    # 확인
    assert resp.status_code == 200
    assert client.session.calls == 1

# 404 test
def test_request_404_no_retry():
    client = make_client([FakeResponse(404)])

    with pytest.raises(HTTPError):
        client._request(endpoint="list.json")

    assert client.session.calls == 1

# 반복 줄이기. monkeypatch는 time.sleep 기능 바꿔치기
@pytest.fixture
def fake_sleep(monkeypatch):
    waits = [] 
    monkeypatch.setattr(time, "sleep", lambda x: waits.append(x))

    return waits


# 503 -> 200 test
def test_request_retry_then_success(fake_sleep):
    # 준비: sleep 가짜로 바꾸기

    client = make_client([FakeResponse(503), FakeResponse(200)])

    # 실행
    resp = client._request(endpoint="list.json")

    # 결과 확인
    assert resp.status_code == 200
    assert client.session.calls == 2
    assert fake_sleep == [1]

def test_request_503_give_up_after_max_attempts(fake_sleep):

    client = make_client([FakeResponse(503),FakeResponse(503),FakeResponse(503) ])

    with pytest.raises(HTTPError):
        client._request(endpoint="list.json")

    assert client.session.calls == 3
    assert fake_sleep == [1, 2,]


def test_request_timeout(fake_sleep):


    client = make_client([Timeout(), FakeResponse(200)])

    resp = client._request(endpoint="list.json")

    assert resp.status_code == 200
    assert client.session.calls == 2
    assert fake_sleep == [1]

    