# 설정 · 설계 노트 · 트러블슈팅

프로젝트 개요와 아키텍처는 [README](../README.md) 를 참고하세요.

---

## 사전 요구사항

- Docker Desktop
- [Astro CLI](https://www.astronomer.io/docs/astro/cli/install-cli)
- Databricks 워크스페이스 (Unity Catalog 사용)
- **OpenDART API 인증키** — [발급 페이지](https://opendart.fss.or.kr/) 에서 무료 발급 (이메일 인증)

---

## 초기 설정

### 1. Databricks 준비

**SQL Warehouse 생성** — `SQL → SQL Warehouses → Create`
- Type: **Serverless** 권장 (기동이 빠름)
- Size: `2X-Small`, Auto stop: `10 minutes`

**접속 정보 확인** — `Connection details` 탭에서 `Server hostname`, `HTTP path`

**액세스 토큰(PAT) 발급** — `Settings → Developer → Access tokens` (생성 직후 한 번만 표시)

**카탈로그 / 스키마 / Volume 준비**
```sql
CREATE CATALOG IF NOT EXISTS workspace;
CREATE SCHEMA  IF NOT EXISTS workspace.analytics;
CREATE SCHEMA  IF NOT EXISTS workspace.analytics_raw;

-- DART 원본 파일이 떨어지는 랜딩 존
CREATE VOLUME IF NOT EXISTS workspace.analytics_raw.dart_landing;
```

### 2. Airflow Connection 등록

| conn_id | 용도 | Conn Type |
|---|---|---|
| `dart_api` | OpenDART API 인증 | `Generic` |
| `dbt-db` | Databricks 접속 | `Databricks` |

`.env` 파일에 추가합니다 (각각 줄바꿈 없이 한 줄).

```
AIRFLOW_CONN_DART_API='{"conn_type": "generic", "host": "https://opendart.fss.or.kr", "password": "<DART 인증키>"}'
AIRFLOW_CONN_DBT_DB='{"conn_type": "databricks", "host": "https://<서버호스트명>", "password": "<PAT 토큰>", "extra": {"http_path": "<HTTP path>"}}'
```

| 항목 | 주의사항 |
|---|---|
| 환경변수명 | `AIRFLOW_CONN_` + conn_id 대문자 (`dbt-db` → `DBT_DB`) |
| `password` | **API 키·토큰은 반드시 `password` 필드에** — Airflow가 로그에서 자동 마스킹 |
| `dart_api` 의 `conn_type` | `generic` 으로 충분. `http` 타입은 `apache-airflow-providers-http` 설치 시에만 선택 가능하며, 이 프로젝트는 `requests` 를 직접 쓰므로 불필요 |

**등록 확인**
```powershell
astro dev bash
```
```bash
airflow connections list
airflow connections get dart_api
```

> `.env` 는 컨테이너 기동 시점에만 주입되므로 수정 후 **`astro dev restart`** 가 필요합니다. 또한 이 방식으로 만든 Connection은 **Airflow UI의 Connections 목록에 표시되지 않습니다** (정상 동작).
>
> 따옴표 파싱 문제로 값이 깨지는 경우 CLI 등록이 확실합니다.
> ```bash
> airflow connections add dart_api --conn-type generic \
>   --conn-host https://opendart.fss.or.kr --conn-password '<인증키>'
> ```
> 단, CLI/UI 등록은 메타DB에 저장되므로 `astro dev kill` 시 사라집니다.

### 3. 실행

```powershell
astro dev start
astro dev run dags unpause dart_ingest
astro dev run dags trigger dart_ingest
```

> **일시정지(paused) 상태에서 trigger하면 DAG Run이 `queued`에 머문 채 실행되지 않습니다.**

---

## 설계 노트

### OpenDART API의 함정 — 에러가 HTTP 상태코드로 오지 않는다

키가 틀려도, 한도를 넘겨도 서버는 **`200 OK`** 를 반환합니다. 실제 결과는 **응답 본문의 `status` 필드**에 있습니다.

```json
{ "status": "013", "message": "조회된 데이터가 없습니다." }
```

`response.raise_for_status()` 만 믿으면 에러를 정상으로 착각하고 빈 데이터를 적재하게 됩니다. status는 **3가지 부류로 나눠서** 처리합니다.

| status | 의미 | 처리 |
|---|---|---|
| `000` | 정상 | 데이터 반환 |
| **`013`** | **조회된 데이터 없음** | **예외 아님. 빈 리스트 반환** |
| `800` `900` | 시스템 점검 / 정의되지 않은 오류 | 재시도 대상 |
| `010` `011` `012` | 등록 안 된 키 / 사용 불가 키 / 접근 불가 IP | 즉시 실패 |
| `020` `021` | 요청 제한 초과 / 조회 가능 회사 수 초과 | 즉시 실패 |
| `100` `101` | 잘못된 파라미터 | 즉시 실패 (코드 버그) |

> `013`을 예외로 던지면 **공시가 없는 주말마다 DAG이 실패**합니다. 가장 자주 발생하는 사고입니다.

### 재시도는 2계층으로 나눈다

```
┌─ Airflow 태스크 재시도 (retries, retry_delay=30분) ─┐   ← 긴 장애: status 800/900
│   ┌─ _request 내부 재시도 (3회, 지수 백오프) ─┐      │   ← 짧은 글리치: 네트워크, 5xx
│   └──────────────────────────────────────┘      │
└────────────────────────────────────────────────────┘
```

`800`(시스템 점검)은 복구에 수십 분이 걸리므로 코드 안에서 몇 초 기다려봐야 의미가 없습니다. **Airflow가 이미 재시도 엔진**이므로 긴 장애는 태스크 재시도에 위임합니다.

| 계층 | 보는 것 | 재시도 |
|---|---|---|
| `_request` | HTTP 레벨 (네트워크 예외, 5xx) | ✅ 짧게 3회 |
| `get_json` | 본문 `status` 필드 | ❌ 분류해서 raise |

`_request` 가 본문을 건드리지 않아야 `get_zip`(ZIP 바이너리)에서도 재사용할 수 있습니다.

`010` 같은 치명적 오류는 재시도가 낭비이므로, 예외에 `retryable` 플래그를 실어 보내고 태스크 계층에서 `AirflowFailException` 으로 변환합니다. 변환을 태스크에서 하는 이유는 아래와 같습니다.

### Airflow 의존성을 클라이언트 밖으로 밀어낸다

```python
class DartClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        ...                                  # 순수 Python. Airflow 를 모름

    @classmethod
    def from_conn(cls, conn_id: str = "dart_api"):
        from airflow.sdk import BaseHook     # ← 함수 안에서 import
        ...
```

| 상황 | 사용법 |
|---|---|
| 로컬 셸에서 테스트 | `DartClient(api_key="...")` — Airflow 없이 동작 |
| DAG 태스크 안 | `DartClient.from_conn()` |

Airflow 3의 `airflow.sdk.BaseHook` 은 **태스크 실행 컨텍스트 안에서만** Connection을 조회할 수 있습니다. 최상단에서 import하면 로컬 테스트가 불가능해집니다.

### 경로는 `AIRFLOW_HOME` 기준으로

```python
AIRFLOW_HOME = Path(os.environ.get("AIRFLOW_HOME", "/usr/local/airflow"))
DBT_PROJECT_PATH = AIRFLOW_HOME / "include" / "dbt" / "dart"
```

| 환경 | `AIRFLOW_HOME` |
|---|---|
| Astro Runtime (`astro dev`) | `/usr/local/airflow` |
| apache/airflow (자체 호스팅) | `/opt/airflow` |

Airflow가 항상 설정하는 변수라, 이렇게 두면 **코드 수정 없이 양쪽에서 동작**합니다. 자체 호스팅으로 이관할 때 `Dockerfile` 한 개만 교체하면 됩니다.

---

## 개발 워크플로

### DART 클라이언트 로컬 테스트

Airflow 컨테이너 없이 로컬 venv에서 검증할 수 있습니다 (리포지토리 루트에서 실행).

```powershell
$env:DART_API_KEY = "<인증키>"

.venv\Scripts\python.exe -c "import os; from include.dart.client import DartClient; c=DartClient(api_key=os.environ['DART_API_KEY']); r=c.get_json('list.json', bgn_de='20260803', end_de='20260807', page_count='10'); print(len(r))"
```

**반드시 확인할 3가지**

| 테스트 | 방법 | 기대 결과 |
|---|---|---|
| 정상 (`000`) | 평일 구간 조회 | 리스트 반환 |
| 데이터 없음 (`013`) | 미래 날짜로 조회 | **예외 아님, `[]`** |
| 잘못된 키 (`010`) | `api_key="wrongkey"` | `DartApiError` |

### dbt 모델 개발

DAG 전체 실행보다 컨테이너에서 dbt를 직접 실행하는 편이 빠릅니다.

```powershell
astro dev bash
```
```bash
source /usr/local/airflow/dbt_venv/bin/activate
cd /usr/local/airflow/include/dbt/dart

dbt debug                                # 연결 확인
dbt run  --select stg_dart__disclosure   # 모델 1개만
dbt test --select fct_disclosure         # 테스트 1개만
dbt compile --select stg_dart__fin_stmt  # 매크로가 풀린 SQL 확인

deactivate
```

> dbt 수동 실행에는 `profiles.yml` 이 필요합니다. Cosmos는 Airflow Connection에서 프로파일을 **실행 시점에 생성 후 폐기**하므로 저장소에는 존재하지 않습니다. 직접 만들 경우 `.gitignore` 에 추가하세요.

### 자주 쓰는 명령

| 명령 | 용도 |
|---|---|
| `astro dev start` / `restart` / `stop` | 환경 기동 / 재시작 / 중지 |
| `astro dev parse` | DAG 문법·import 오류만 빠르게 검사 |
| `astro dev bash` | 컨테이너 접속 |
| `astro dev run dags list-import-errors` | DAG이 UI에 보이지 않을 때 원인 확인 |
| `astro dev run dags list-runs <dag_id>` | 실행 이력 조회 |

---

## 트러블슈팅

### DART 수집

| 증상 | 원인 / 해결 |
|---|---|
| 모든 요청이 `010` 으로 실패 | `requests.get()` 에 `params=` 를 전달하지 않아 `crtfc_key` 가 빠짐 |
| 주말·공휴일에만 DAG 실패 | `013`(데이터 없음)을 예외로 처리함. 빈 리스트를 반환해야 함 |
| `KeyError: 'list'` | status 분기를 타지 않고 바로 `payload["list"]` 접근. `company.json` 은 `list` 키가 없음 |
| `AirflowNotFoundException: conn_id 'dart_api' isn't defined` | `.env` 수정 후 `astro dev restart` 누락, 또는 태스크 밖에서 `airflow.sdk.BaseHook` 호출 |
| `ModuleNotFoundError: No module named 'include'` | 리포지토리 루트가 아닌 곳에서 실행 |
| `ModuleNotFoundError: No module named 'airflow'` (로컬) | airflow import가 파일 최상단에 있음. `from_conn` 안으로 옮길 것 |
| 요청이 응답 없이 멈춤 | `requests` 에 `timeout` 미지정. `timeout=(5, 30)` 권장 |
| `020` 요청 제한 초과 | 일일 한도 소진. 당일 재시도 무의미 — 수집 범위를 줄일 것 |

### Airflow / dbt / Databricks

| 증상 | 원인 / 해결 |
|---|---|
| `401 Credential was not sent...` | PAT 만료 또는 오기입. Connection의 `password` 확인 |
| `TABLE_OR_VIEW_NOT_FOUND` (테스트 단계) | `RenderConfig(test_behavior=TestBehavior.AFTER_ALL)` 미적용 |
| `Got N results, configured to fail if != 0` | 시스템 오류가 아닌 **데이터 검증 실패**. 테스트가 정상 동작한 것 |
| DAG Run이 `queued`에서 멈춤 | DAG이 paused 상태. `dags unpause` 실행 |
| `dbt: command not found` (컨테이너 내) | `source /usr/local/airflow/dbt_venv/bin/activate` |
| `Could not find a version that satisfies...` | Python 버전 비호환. 이미지 태그의 `-python-3.xx` 확인 |
| 첫 쿼리가 오래 멈춤 | SQL Warehouse가 auto-stop에서 기동 중 |

### 실패 원인을 찾는 순서

1. Airflow UI → 해당 DAG → **Graph** 뷰
2. 색상으로 구분
   - 🔴 **failed** → **실제 원인**
   - 🟠 **upstream_failed** → 상위 실패의 연쇄. 로그를 봐도 의미 없음
   - 🟢 success
3. 빨간 Task 클릭 → **Logs** 탭

> 에러 메시지에 등장하는 **테이블 이름이 아니라, 빨간 Task의 이름**을 먼저 확인해야 합니다.

---

## 알려진 제약

- **DART 재무제표는 2015년 이후** 데이터만 제공됩니다.
- **API 일일 한도 20,000건** — 수집 대상을 확대할 경우 분할 실행 로직이 필요합니다.
- **유닛 테스트 미실행** — dbt `unit_tests` 는 Cosmos가 Airflow Task로 변환하지 않습니다. `dbt test --select "test_type:unit"` 로 직접 실행해야 합니다.
- **스케줄 미설정** — 현재 `schedule=None`(수동 실행 전용)입니다. 정기 실행 시 `pendulum` 으로 타임존을 지정하세요 (Airflow 기본 타임존은 UTC, DART 공시는 KST 기준).

---

## 참고 자료

- [OpenDART 개발가이드](https://opendart.fss.or.kr/guide/main.do) — 엔드포인트·파라미터·status 코드 전체 목록
- [Astronomer Cosmos 문서](https://astronomer.github.io/astronomer-cosmos/)
- [dbt-databricks 설정](https://docs.getdbt.com/docs/core/connect-data-platform/databricks-setup)
- [Databricks COPY INTO](https://docs.databricks.com/aws/en/sql/language-manual/delta-copy-into)
- [Astro CLI 명령어 레퍼런스](https://www.astronomer.io/docs/astro/cli/reference)
