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