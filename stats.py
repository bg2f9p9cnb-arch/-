"""인스타 계정·게시물 성과를 GitHub 실행 화면(주석)에 출력"""
import os
import requests

BASE = os.getenv("IG_GRAPH_BASE") or "https://graph.instagram.com/v26.0"
TOK = os.environ["IG_ACCESS_TOKEN"]


def get(path, **p):
    p["access_token"] = TOK
    r = requests.get(f"{BASE}/{path}", params=p, timeout=60)
    return r.json() if r.ok else {"error": r.text[:300]}


me = get("me", fields="username,followers_count,follows_count,media_count")
print(f"::notice title=계정::{me}")
media = get("me/media", fields="id,caption,media_type,like_count,comments_count,timestamp", limit=50)
rows = []
for m in media.get("data", []):
    ins = get(f"{m['id']}/insights", metric="reach,views,saved,shares,total_interactions")
    vals = {d["name"]: d["values"][0]["value"] for d in ins.get("data", [])} if "data" in ins else {"insights": "권한없음"}
    title = (m.get("caption") or "").splitlines()[0][:30]
    rows.append(f"{m['timestamp'][:10]} | {title} | 좋아요 {m.get('like_count')} 댓글 {m.get('comments_count')} | {vals}")
print(f"::notice title=게시물 {len(rows)}개::" + " %0A".join(rows))
if "error" in media:
    print(f"::warning::{media['error']}")
