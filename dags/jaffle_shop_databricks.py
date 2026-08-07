from datetime import datetime
from pathlib import Path

from cosmos import (
    DbtDag,
    ProjectConfig,
    ProfileConfig,
    ExecutionConfig,
    RenderConfig,
    TestBehavior,
)
from cosmos.profiles import DatabricksTokenProfileMapping

# 컨테이너 안에서 경로
DBT_PROJECT_PATH = Path("/usr/local/airflow/include/dbt/jaffle_shop")
DBT_EXECUTABLE_PATH = "/usr/local/airflow/dbt_venv/bin/dbt"

profile_config = ProfileConfig(
    profile_name='jaffle_shop',
    target_name="dev",
    profile_mapping=DatabricksTokenProfileMapping(
        conn_id="dbt-db",
        profile_args={
            "catalog": "workspace",
            "schema": "analytics"
        }
    )
)

# 모델 하나하나를 읽어 airflow task로 자동 변환?!
jaffle_shop_databricks = DbtDag(
    dag_id = "jaffle_shop_databricks",
    project_config=ProjectConfig(DBT_PROJECT_PATH),
    profile_config=profile_config,
    execution_config=ExecutionConfig(dbt_executable_path=DBT_EXECUTABLE_PATH),
    render_config=RenderConfig(test_behavior=TestBehavior.AFTER_ALL),  # test는 모델 다 생성하고 수행(기본값:AFTER_EACH)
    operator_args={"install_deps": True}, # package.yml dbt_utils 자동설치
    schedule=None,
    start_date= datetime(2026, 8, 1),
    catchup=False,
    tags=['dbt', 'databricks'],
)

