from airflow.sdk import dag, task
from include.dart.loader import get_workspace_client
from pendulum import datetime

@dag(
    schedule=None, # manual
    start_date= datetime(2026,10,26, tz="Asia/Seoul"),
)
def check_databricks_conn():

    @task
    def print_current_user():
        client = get_workspace_client("dbt-db")
        print(client.current_user.me())

    print_current_user()

check_databricks_conn()
