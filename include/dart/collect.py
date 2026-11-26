"""
    무엇을 수집할지(공시검색, 기업개황, 재무제표)
"""

def fetch_companies(client, corp_codes:list[str]) -> list[dict]:

    companies = []
    for corp_code in corp_codes:
        corp_dict = client.get_dict("company.json", corp_code=corp_code)
        if corp_dict is not None:
            companies.append(corp_dict)

    return companies

def fetch_fin_stmts(client, corp_codes:list[str],
                    bsns_year:str , reprt_code:str, fs_div:str) -> list[dict]:
    fnl_list = []
    for corp_code in corp_codes:
        fnl = client.get_json("fnlttSinglAcntAll.json", corp_code=corp_code, bsns_year=bsns_year, reprt_code=reprt_code, fs_div=fs_div)

        for acnt in fnl:
            acnt['_fs_div'] = fs_div
        fnl_list.extend(fnl)

    return fnl_list