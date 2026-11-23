import os
from pendulum import datetime, duration
from pathlib import Path
from airflow.sdk import task, dag
from airflow.sdk.exceptions import AirflowFailException
from airflow.sdk import Asset

from include.dart.collect import fetch_companies
from include.dart.loader import load_to_volume, get_workspace_client, build_insert_sql, run_sql
from include.dart.corp_code import get_corp_code_list
from include.dart.client import DartClient


DATABRICKS_HOST_URI = os.environ.get("DATABRICKS_HOST_URI", "")
WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", None)
AIRFLOW_HOME = Path(os.environ.get("AIRFLOW_HOME", "/usr/local/airflow"))
DBT_PROJECT_PATH  = AIRFLOW_HOME / "include" / "dbt" / "dart"

@dag(
    schedule=None,
    start_date= datetime(2025, 11, 5),
    default_args={"retries" : 1, 
                  "retry_delay": duration(minutes=1)},
)
def dart_ingest():

    @task()
    def extract_company(ds=None):
        path = f"{AIRFLOW_HOME}/data/target_corps.csv"
        corp_codes = get_corp_code_list(path)
        dart = DartClient.from_conn()
        rows = fetch_companies(dart, corp_codes)
        ws = get_workspace_client()
        return load_to_volume(ws, rows, "company", ds)

    @task(outlets=[Asset(f"databricks://{DATABRICKS_HOST_URI}/workspace/analytics_raw/raw_company")])
    def load_company(path, ds=None):
        if not WAREHOUSE_ID:    
            raise AirflowFailException("WAREHOUSE_ID 환경변수가 없습니다. .env 확인하세요")
        ws = get_workspace_client()
        sql = build_insert_sql('company', path, ds)
        print(sql)
        resp = run_sql(ws, WAREHOUSE_ID, sql)
        print([col.name for col in resp.manifest.schema.columns])
        print(resp.result.data_array)
      
        
    volume_path = extract_company()
    load_company(volume_path)

dart_ingest()
