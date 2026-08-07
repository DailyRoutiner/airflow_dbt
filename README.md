# airflow_dbt

Apache Airflow와 dbt를 [Astronomer Cosmos](https://astronomer.github.io/astronomer-cosmos/)로 연결하여, **dbt 모델을 Airflow Task로 자동 변환해 Databricks 위에서 실행**하는 프로젝트입니다.


---

## 아키텍처

```
┌─────────────────────────────────────────────┐
│  Astro Runtime 3.3-2-python-3.12            │
│  (Airflow 3.3.0 / Python 3.12)              │
│                                             │
│  ┌───────────────┐   ┌────────────────────┐ │
│  │ Airflow       │   │ dbt_venv           │ │
│  │ + Cosmos      │──▶│ dbt-databricks     │ │
│  │               │   │ (독립 가상환경)      │ │
│  └───────┬───────┘   └─────────┬──────────┘ │
│          │                     │            │
│  Connection: dbt-db            │            │
└──────────┼─────────────────────┼────────────┘
           │                     │
           └──────────┬──────────┘
                      ▼
        ┌───────────────────────────┐
        │  Databricks SQL Warehouse │
        │  catalog: workspace       │
        │  schema : analytics       │
        └───────────────────────────┘
```

Cosmos가 dbt 프로젝트를 파싱해 **모델 1개 = Airflow Task 1개**로 자동 변환합니다. DAG의 의존 관계는 dbt의 `{{ ref() }}`에서 자동으로 계산됩니다.

현재 DAG은 **총 19개 Task**로 구성됩니다.

| 구분 | 개수 | Task 예시 |
|---|---|---|
| Seed (CSV 적재) | 6 | `raw_customers_seed`, `raw_orders_seed` … |
| 모델 (view/table 생성) | 12 | `stg_orders_run`, `orders_run`, `customers_run` … |
| 데이터 테스트 | 1 | `jaffle_shop_test` (30개 테스트를 한 번에 실행) |

---

## 프로젝트 구조

```
airflow_dbt/
├── Dockerfile                  # Astro Runtime 이미지 + dbt 전용 venv 정의
├── requirements.txt            # Airflow 쪽 Python 패키지 (Cosmos 등)
├── packages.txt                # OS 패키지 (apt) — 현재 비어 있음
├── .env                        # 로컬 환경변수 / Connection (Git 제외)
├── airflow_settings.yaml       # 로컬 전용 Connection·Variable 정의 (Git 제외)
│
├── dags/
│   └── jaffle_shop_databricks.py   # Cosmos DbtDag 정의
│
├── include/
│   └── dbt/
│       └── jaffle_shop/         # dbt 프로젝트
│           ├── dbt_project.yml  # 프로젝트 설정 (materialized 기본값 등)
│           ├── packages.yml     # dbt 패키지 (dbt_utils)
│           ├── macros/
│           │   └── cents_to_dollars.sql   # Cent를 달러로 변환
│           ├── models/
│           │   ├── staging/     # stg_* (view)
│           │   └── marts/       # customers, orders 등 (table)
│           └── seeds/           # 원본 CSV 6개
│
├── plugins/                    # 커스텀 플러그인 (미사용)
└── tests/                      # DAG 무결성 테스트
```

### 데이터가 생성되는 위치

| Databricks 스키마 | 내용 | 생성 주체 |
|---|---|---|
| `workspace.analytics_raw` | `raw_customers`, `raw_orders` 등 6개 | seed (CSV 업로드) |
| `workspace.analytics` | `stg_*` 뷰 6개 + 마트 테이블 6개 | 모델 |

> seed가 `_raw` 접미사 스키마에 들어가는 것은 `dbt_project.yml`의 `seeds: +schema: raw` 설정 때문입니다.

---

## 사전 요구사항

- Docker Desktop
- [Astro CLI](https://www.astronomer.io/docs/astro/cli/install-cli)
- Databricks 워크스페이스 (Unity Catalog 사용)

---

## 초기 설정

### 1. Databricks 준비

**SQL Warehouse 생성** — `SQL → SQL Warehouses → Create`
- Type: **Serverless** 권장 (기동이 빠름)
- Size: `2X-Small`, Auto stop: `10 minutes`

**접속 정보 확인** — 생성한 Warehouse의 `Connection details` 탭
- `Server hostname` → 예: `dbc-xxxxxxxx-xxxx.cloud.databricks.com`
- `HTTP path` → 예: `/sql/1.0/warehouses/xxxxxxxxxxxx`

**액세스 토큰(PAT) 발급** — `Settings → Developer → Access tokens → Generate new token`
- 생성 직후 한 번만 표시되므로 즉시 복사

**카탈로그/스키마 준비** — SQL Editor에서 실행
```sql
CREATE CATALOG IF NOT EXISTS workspace;
CREATE SCHEMA  IF NOT EXISTS workspace.analytics;
```

### 2. Airflow Connection 등록

DAG이 `conn_id="dbt-db"`를 참조하므로 **정확히 이 이름**으로 등록해야 합니다.

`.env` 파일에 아래 한 줄을 추가합니다 (줄바꿈 없이 한 줄).

```
AIRFLOW_CONN_DBT_DB='{"conn_type": "databricks", "host": "https://<서버호스트명>", "password": "<PAT 토큰>", "extra": {"http_path": "<HTTP path>"}}'
```

| 항목 | 주의사항 |
|---|---|
| 환경변수명 | `AIRFLOW_CONN_` + conn_id 대문자 (`dbt-db` → `DBT_DB`) |
| `host` | **`https://` 포함** (Cosmos가 dbt로 넘길 때 자동으로 제거) |
| `password` | 토큰을 여기에 넣습니다 (Databricks Provider 규칙) |
| `http_path` | `extra` 안에 넣습니다 |

> Airflow UI(`Admin → Connections`)에서 직접 등록해도 동작하지만, `astro dev kill` 시 사라집니다. **재현 가능하도록 `.env` 사용을 권장합니다.**
>
> `.env`는 `.gitignore`에 포함되어 있어 Git에 올라가지 않습니다.

### 3. 실행

```powershell
astro dev start
```

Airflow UI 접속 후 DAG을 활성화하고 실행합니다.

```powershell
astro dev run dags unpause jaffle_shop_databricks
astro dev run dags trigger jaffle_shop_databricks
```

> **일시정지(paused) 상태에서 trigger하면 DAG Run이 `queued`에 머문 채 실행되지 않습니다.** 반드시 `unpause`를 먼저 하세요.

UI 포트는 `astro dev start` 출력에 표시됩니다(기본 8080, 충돌 시 자동 변경).

---

## 주요 설정 설명

### Dockerfile — dbt를 별도 가상환경에 설치

```dockerfile
FROM astrocrpublic.azurecr.io/runtime:3.3-2-python-3.12

RUN python -m venv dbt_venv && \
    source dbt_venv/bin/activate && \
    pip install --no-cache-dir dbt-databricks && \
    deactivate
```

- dbt를 Airflow와 **같은 환경에 설치하면 의존성이 충돌**하므로 `dbt_venv`로 분리합니다.
- 이미지 태그의 `-python-3.12`가 Python 버전을 결정합니다. 기본 태그(`3.3-2`)는 **Python 3.14**이며, 이 버전은 `dbt-metricflow` 등 일부 패키지를 아직 지원하지 않습니다.
- `dbt_venv`는 PATH에 없으므로, 수동 실행 시 전체 경로 또는 활성화가 필요합니다(아래 참고).

### DAG — `TestBehavior.AFTER_ALL`

```python
render_config=RenderConfig(test_behavior=TestBehavior.AFTER_ALL),
```

Cosmos 기본값은 `AFTER_EACH`(모델마다 즉시 테스트)입니다. 그런데 `jaffle_shop`에는 **아직 생성되지 않은 하위 모델을 참조하는 `relationships` 테스트**가 있어, 기본값으로 실행하면 다음 오류가 발생합니다.

```
[TABLE_OR_VIEW_NOT_FOUND] The table or view `workspace`.`analytics`.`orders` cannot be found.
```

`AFTER_ALL`로 설정하면 **모든 모델을 생성한 뒤 테스트를 일괄 실행**하므로 참조 대상이 모두 존재하게 됩니다.

### 매크로 — `databricks__cents_to_dollars`

`macros/cents_to_dollars.sql`에 Databricks 전용 구현을 추가했습니다.

```sql
{% macro databricks__cents_to_dollars(column_name) %}
    cast({{ column_name }} as decimal(16, 2)) / 100
{% endmacro %}
```

**추가 이유**: `dbt-databricks`는 `dbt-spark`를 상속하므로, 전용 매크로가 없으면 `spark__cents_to_dollars`(`round(col / 100, 2)`)가 선택됩니다. Spark에서 `정수 / 정수`는 **DOUBLE**을 반환하고, 부동소수점 누적 오차 때문에 다음 테스트가 실패합니다.

```
lifetime_spend_pretax + lifetime_tax_paid = lifetime_spend
→ Got 35 results, configured to fail if != 0
```

`decimal`로 캐스팅하면 합산 시에도 오차가 발생하지 않습니다.

> 매크로 이름은 반드시 `{어댑터}__{매크로명}` 형식이어야 합니다. 오타가 있으면 **에러 없이 조용히 상위 어댑터 구현이 사용**되므로 주의가 필요합니다.

---

## 개발 워크플로

DAG 전체 실행은 약 3분이 걸립니다. 모델을 수정하며 개발할 때는 컨테이너에서 dbt를 직접 실행하는 편이 빠릅니다.

```powershell
astro dev bash
```

```bash
source /usr/local/airflow/dbt_venv/bin/activate
cd /usr/local/airflow/include/dbt/jaffle_shop

dbt debug                              # 연결 확인
dbt run  --select stg_orders           # 모델 1개만 실행
dbt test --select customers            # 테스트 1개만 실행
dbt compile --select stg_orders        # 매크로가 풀린 SQL 확인
dbt test --select "test_type:unit"     # 유닛 테스트 (Cosmos는 실행하지 않음)

deactivate
exit
```

> dbt를 수동 실행하려면 `include/dbt/jaffle_shop/profiles.yml`이 필요합니다. Cosmos는 Airflow Connection에서 프로파일을 **실행 시점에 생성 후 폐기**하므로, 저장소에는 존재하지 않습니다.

`profiles.yml` 예시 (생성 시 `.gitignore`에 추가할 것):

```yaml
jaffle_shop:
  target: dev
  outputs:
    dev:
      type: databricks
      host: <서버호스트명>            # https:// 없이
      http_path: <HTTP path>
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
      catalog: workspace
      schema: analytics
      threads: 4
```

### 자주 쓰는 명령

| 명령 | 용도 |
|---|---|
| `astro dev start` / `restart` / `stop` | 환경 기동 / 재시작 / 중지 |
| `astro dev parse` | DAG 문법·import 오류만 빠르게 검사 |
| `astro dev bash` | 컨테이너 접속 |
| `astro dev run dags list-import-errors` | DAG이 UI에 보이지 않을 때 원인 확인 |
| `astro dev run dags list-runs <dag_id>` | 실행 이력 조회 |
| `astro dev run tasks list <dag_id>` | Task 목록 조회 |

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `401 Credential was not sent...` | 토큰이 잘못되었거나 만료됨. Connection의 `password` 필드에 PAT가 들어 있는지 확인 |
| `TABLE_OR_VIEW_NOT_FOUND` (테스트 단계) | `TestBehavior.AFTER_ALL` 미적용 |
| `Got N results, configured to fail if != 0` | 시스템 오류가 아닌 **데이터 검증 실패**. 테스트가 정상 동작한 것 |
| DAG Run이 `queued`에서 멈춤 | DAG이 paused 상태. `dags unpause` 실행 |
| `dbt: command not found` (컨테이너 내) | `dbt_venv`가 PATH에 없음. `source /usr/local/airflow/dbt_venv/bin/activate` |
| `Could not find a version that satisfies...` `from versions: none` | Python 버전 비호환. 이미지 태그의 `-python-3.xx` 확인 |
| Task가 `upstream_failed`뿐이고 `failed`가 없음 | `dags test`로 실행한 경우. **`dags trigger`를 사용할 것** |
| 첫 쿼리가 오래 멈춤 | SQL Warehouse가 auto-stop에서 기동 중 |

### 실패 원인을 찾는 순서

1. Airflow UI → 해당 DAG → **Graph** 뷰
2. 색상으로 구분
   - 🔴 **failed** → **실제 원인**
   - 🟠 **upstream_failed** → 상위 실패로 인한 연쇄. 로그를 봐도 의미 없음
   - 🟢 success
3. 빨간 Task 클릭 → **Logs** 탭 → `Completed with N error` 부분 확인

> 에러 메시지에 등장하는 **테이블 이름이 아니라, 빨간 Task의 이름**을 먼저 확인해야 합니다.

---

## 알려진 제약

- **유닛 테스트 미실행** — `orders.yml` 등에 정의된 `unit_tests` 3개는 Cosmos가 Airflow Task로 변환하지 않습니다. 실행하려면 컨테이너에서 `dbt test --select "test_type:unit"`를 직접 실행해야 합니다.
- **스케줄 미설정** — 현재 `schedule=None`(수동 실행 전용)입니다. 정기 실행이 필요하면 cron 표현식과 함께 `pendulum`으로 타임존을 지정하세요(Airflow 기본 타임존은 UTC).
- **재시도/알림 미설정** — 정기 실행 전에 `default_args`로 `retries`와 실패 알림을 추가하는 것이 좋습니다.

---

## 참고 자료

- [Astronomer Cosmos 문서](https://astronomer.github.io/astronomer-cosmos/)
- [dbt-databricks 설정](https://docs.getdbt.com/docs/core/connect-data-platform/databricks-setup)
- [Astro CLI 명령어 레퍼런스](https://www.astronomer.io/docs/astro/cli/reference)
