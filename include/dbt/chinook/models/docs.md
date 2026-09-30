{% docs customer_id %}
Chinook 원본 'customer.customer_id' 고객을 식별하는 대리키 입니다.
고객이 탈퇴해도 재사용되지 않습니다.
{% enddocs%}

{% docs region_classification %}
'seed/country_region.csv 에 정의된 자체 분류입니다. 표준 지역 코드가 아님, 
분류 기준을 바꾸려면 CSV를 수정하고 PR을 올리세요 - 변경 이력이 git에 남습니다.
매핑에 없는 국가는 NULL이 되니 accepted_values가 실패하거나 Warn을 출력해야 합니다.
{% enddocs %}