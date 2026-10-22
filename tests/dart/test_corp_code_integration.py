"""
전체 건수: > 100_000
종목코드 보유 건수: 예를 들어 3_000 <= n <= 5_000처럼 범위로
8자리, 6자리, 중복 없음, 삼성전자 대조
파일이 없으면 skipif로 건너뛰기

현재 실제 상장사는 코스피, 코스닥, 코넥스를 합쳐 약 2,700~2,800개 정도입니다.
1,000개 넘게 차이가 나는 이유는 아마 상장폐지된 회사도 stock_code가 남아 있어서일 거예요.
"""

import pytest
from pathlib import Path
from include.dart.corp_code import parse_corp_zip, filter_listed


ZIP_PATH = Path(__file__).parents[2] / "data" / "corpCode.zip"

pytestmark = pytest.mark.skipif(not ZIP_PATH.exists(), reason="파일이 없어 건너뜀")

@pytest.fixture(scope="module")
def rows():
    return parse_corp_zip(ZIP_PATH.read_bytes())


def test_total_count(rows): 
    assert len(rows) > 100_000


def test_listed_count_in_range(rows):
    listed = filter_listed(rows)
    assert 3_000 <= len(listed) <= 5_000


def test_corp_code_is_8_digits(rows): 
    bad = [row for row in rows if len(row['corp_code']) != 8 or not row["corp_code"].isdigit()]
    assert bad == []


def test_stock_code_is_6_digits(rows): 
    pytest.skip("TODO")


def test_corp_code_unique(rows):  
    pytest.skip("TODO")


def test_samsung(rows):  
    pytest.skip("TODO")
