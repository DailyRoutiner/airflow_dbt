import io
import zipfile
from include.dart.corp_code import parse_corp_zip, filter_listed, write_target_csv
import csv

XML = """ 
<result>
  <list>
    <corp_code>00126380</corp_code>
    <corp_name>삼성전자</corp_name>
    <stock_code>005930</stock_code>
  </list>
  <list>
    <corp_code>00000001</corp_code>
    <corp_name>비상장회사</corp_name>
    <stock_code> </stock_code>
  </list>
</result>
"""

# 가짜 데이터 만들기
def make_zip(xml: str) -> bytes:
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("CORPCODE.xml", xml)

    return buf.getvalue()

# 방법2 진짜 파일을 한번만 받아서 저장.

def test_parse_corp_zip():

    rows = parse_corp_zip(make_zip(XML))

    assert len(rows) == 2
    assert rows[0]['corp_code'] == '00126380'
    assert rows[1]['stock_code'] == ''

def test_filter_listed():
    listed = filter_listed(parse_corp_zip(make_zip(XML)))

    assert len(listed) == 1
    assert listed[0]['corp_name'] == '삼성전자'

def test_write_target_csv(tmp_path):
    path = tmp_path / "target.csv"

    rows = parse_corp_zip(make_zip(XML))

    write_target_csv(rows, ['005930', '999999'], str(path))

    with open(path, encoding='utf-8') as f:
        target = list(csv.DictReader(f))

    # 확인
    assert len(target) == 1
    assert target[0]['stock_code'] == "005930"
    assert target[0]['corp_code'] == "00126380"

