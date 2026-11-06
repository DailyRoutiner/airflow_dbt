from unittest.mock import MagicMock, call

from include.dart.collect import fetch_companies

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

