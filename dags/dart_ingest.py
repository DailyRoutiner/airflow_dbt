import os
from pathlib import Path
from airflow.sdk import task, dag
from include.dart.collect import fetch_companies
from include.dart.loader import load_to_volume, get_workspace_client
from include.dart.corp_code import get_corp_code_list
from include.dart.client import DartClient
from pendulum import datetime, duration


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

    @task()
    def load_company(path, ds):
        print(path, ds)
        
    volume_path = extract_company()
    load_company(volume_path)

dart_ingest()
