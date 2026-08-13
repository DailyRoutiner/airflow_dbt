import pytest
from include.dart.client import DartClient, DartApiError

class FakeResponse:
    """ requests.Response 대역. json() 만 있으면 충분"""
    def __init__(self, payload):
        ...
    def json(self):
        ...


def make_client(payload):
    """주어진 payload를 돌려주는 클라이언트"""
    client= DartClient(api_key="dumm")

    return client

