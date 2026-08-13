""" CorpCode.xml 파싱 후 CSV 생성(기업 고유번호)"""
import io
import csv
import zipfile
import xml.etree.ElementTree as ET

def parse_corp_zip(raw:bytes) -> list[dict]:
    """ ZIP 바이트 를 list로 변환 """
    # io.BytesIO 로 감싸 zipfile.ZipFile 열기
    file = io.BytesIO(raw)
    corp = zipfile.ZipFile(file)
    # zf.namelist()[0] 읽기
    # ET.fromstring(bytes) 후 root.iter("list") 순회
    ...

def filter_listed(rows: list[dict]) -> list[dict]:
    """ 상장사만 추출 (stock_code Not null)"""
    ...


def write_target_csv(rows: list[dict],  stock_codes: list[str], path:str) -> None:
    """ 관심 종목만 골라 CSV로 저장"""
    ...


