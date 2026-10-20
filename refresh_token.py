"""인스타그램 장기 토큰(60일 유효)을 갱신해 새 토큰을 출력한다.
'Instagram 로그인' 방식 토큰 전용. 발급 후 24시간이 지난 토큰만 갱신돼요."""
import os
import sys

import requests

r = requests.get(
    "https://graph.instagram.com/refresh_access_token",
    params={"grant_type": "ig_refresh_token", "access_token": os.environ["IG_ACCESS_TOKEN"]},
    timeout=30,
)
if not r.ok:
    sys.exit(f"토큰 갱신 실패 ({r.status_code}): {r.text}")
data = r.json()
print(f"새 토큰 유효기간: {data.get('expires_in', 0) // 86400}일", file=sys.stderr)
print(data["access_token"])
