""" 
client.get_json()          loader (5-2)                 loader (5-3)
  응답 dict  ──▶  JSON 파일로 Volume에 업로드  ──▶  REPLACE WHERE  ──▶  raw_dart_* 테이블
                 /Volumes/.../company/2026-10-22/...json

"""

# Volume Root는 상수
VOLUME_ROOT = "/Volumes/workspace/analytics_raw/dart_landing"

def build_volume_path(endpoint: str,  *parts) -> str:
    path = "/".join([VOLUME_ROOT, endpoint, *parts])
    path += ".jsonl"
    return path


if __name__ == "__main__":
    print(build_volume_path("company", "2026-10-22", "00126380"))