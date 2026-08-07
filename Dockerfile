FROM astrocrpublic.azurecr.io/runtime:3.3-2-python-3.12

# dbt는 airflow와 분리된 가상환경으로 설치
RUN python -m venv dbt_venv && \
    source dbt_venv/bin/activate && \
    pip install --no-cache-dir dbt-databricks && \
    deactivate
