"""인스타그램 Content Publishing API로 캐러셀(여러 장) 게시

흐름: 이미지마다 child 컨테이너 생성 -> 캐러셀 컨테이너 생성 -> 처리 완료 대기 -> media_publish
※ 이미지는 인터넷에서 열리는 공개 URL(JPEG)이어야 해요.
"""
import os
import time

import requests

# 'Instagram 로그인' 방식(페이스북 페이지 연결 불필요)이 기본값.
# 'Facebook 로그인' 방식이라면 IG_GRAPH_BASE=https://graph.facebook.com/v26.0 로 지정하세요.
DEFAULT_BASE = "https://graph.instagram.com/v26.0"


class InstagramError(RuntimeError):
    pass


class InstagramPublisher:
    def __init__(self, user_id=None, token=None, base=None):
        # 비워두면 "me" = 토큰 주인 계정 (Instagram 로그인 방식에서 동작)
        self.user_id = user_id or os.getenv("IG_USER_ID") or "me"
        self.token = token or os.environ["IG_ACCESS_TOKEN"]
        self.base = (base or os.getenv("IG_GRAPH_BASE") or DEFAULT_BASE).rstrip("/")

    def _request(self, method, path, **params):
        params["access_token"] = self.token
        kw = {"params": params} if method == "GET" else {"data": params}
        resp = requests.request(method, f"{self.base}/{path}", timeout=60, **kw)
        if not resp.ok:
            raise InstagramError(f"{method} {path} 실패 ({resp.status_code}): {resp.text}")
        return resp.json()

    def whoami(self):
        return self._request("GET", "me", fields="user_id,username,account_type")

    @staticmethod
    def wait_for_url(url, timeout=180):
        """방금 올린 이미지가 공개 URL로 실제로 열릴 때까지 기다린다."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                r = requests.head(url, timeout=15, allow_redirects=True)
                if r.status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(5)
        raise InstagramError(f"이미지 URL이 열리지 않아요: {url}")

    def _wait_container(self, container_id, timeout=300):
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self._request("GET", container_id, fields="status_code").get("status_code")
            if status in ("FINISHED", "PUBLISHED"):
                return
            if status in ("ERROR", "EXPIRED"):
                raise InstagramError(f"컨테이너 {container_id} 상태: {status}")
            time.sleep(5)
        raise InstagramError(f"컨테이너 {container_id} 처리 시간 초과")

    def publish_carousel(self, image_urls, caption):
        if not 2 <= len(image_urls) <= 10:
            raise ValueError("캐러셀은 2~10장이어야 해요")
        for url in image_urls:
            self.wait_for_url(url)

        children = [
            self._request("POST", f"{self.user_id}/media", image_url=url, is_carousel_item="true")["id"]
            for url in image_urls
        ]
        for cid in children:
            self._wait_container(cid)

        parent = self._request("POST", f"{self.user_id}/media", media_type="CAROUSEL",
                               children=",".join(children), caption=caption)["id"]
        self._wait_container(parent)
        return self._request("POST", f"{self.user_id}/media_publish", creation_id=parent)["id"]
