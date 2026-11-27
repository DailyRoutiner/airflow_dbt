create table if not exists workspace.analytics_raw.raw_fin_stmt(
    rcept_no string, 
    reprt_code string, 
    bsns_year string, 
    corp_code string, 
    sj_div string, 
    sj_nm string,
    account_id string, 
    account_nm string, 
    account_detail string, 
    thstrm_nm string,
    thstrm_amount string,
    thstrm_add_amount string, 
    frmtrm_nm string, 
    frmtrm_amount string, 
    frmtrm_q_nm	string,         --전기명(분/반기)	ex) 제 18 기 반기
    frmtrm_q_amount	string,     --전기금액(분/반기)	9,999,999,999 ※ 분/반기 보고서이면서 (포괄)손익계산서 일 경우 [3개월] 금액
    frmtrm_add_amount string,   --전기누적금액
    bfefrmtrm_nm string,
    bfefrmtrm_amount string, 
    ord string, 
    currency string, 
    _fs_div string not null,
    _logical_date date not null,
    _file_path string
)