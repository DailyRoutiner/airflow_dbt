from unittest.mock import MagicMock, call

from include.dart.collect import fetch_companies, fetch_fin_stmts

def test_fetch_companies():
    #준비
    client = MagicMock()
    corp_codes = ["00126380", "00164779", "01695300"]
    client.get_dict.side_effect = [{'corp_code': '00126380', 'corp_name': '삼성전자'}, None, { 'corp_code': '01695300', 'corp_name': '하이닉스'}]

    # 실행
    result = fetch_companies(client, corp_codes)

    # 확인
    assert len(result) == 2
    assert client.get_dict.call_count == 3
    assert client.get_dict.call_args_list[1] == call("company.json", corp_code="00164779")

    assert [r["corp_code"] for r in result] == ["00126380", "01695300"]

def test_fetch_fin_stmts():
    #준비
    client = MagicMock()
    corp_codes = ["00266961", "00164779", "01695300"]
    client.get_json.side_effect = [[{'corp_code': '00266961', 'account_nm': '매출액'}, {'corp_code': '00266961', 'account_nm': '영업이익'}], [], [{'corp_code': '01695300', 'account_nm': '매출액'}, {'corp_code': '01695300', 'account_nm': '영업이익'}]]
    bsns_year = '2025'
    reprt_code = '11011'
    fs_div = "OFS"

    # 실행
    result = fetch_fin_stmts(client, corp_codes, bsns_year, reprt_code, fs_div)

    # 확인
    assert len(result) == 4
    assert client.get_json.call_count == 3
    assert client.get_json.call_args_list[0] == call("fnlttSinglAcntAll.json", corp_code="00266961", bsns_year= "2025" , reprt_code= "11011", fs_div="OFS")

    assert all( r["_fs_div"] == fs_div for r in result )


