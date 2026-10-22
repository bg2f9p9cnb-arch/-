"""매일 실행되는 메인 스크립트
용어 선택 -> 미리 써둔 문구(또는 Claude로 생성) -> 카드 5장 렌더링 -> 이미지 공개 URL 업로드 -> 인스타 게시

사용 예
  python run_daily.py --mock --dry-run       # API 키 없이 레이아웃만 테스트
  python run_daily.py --dry-run              # Claude로 문구까지 생성, 게시는 안 함
  python run_daily.py --term 가산금리 --dry-run
  python run_daily.py                        # 실제 게시 (GitHub Actions가 매일 실행)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import content
from render import render_cards

ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
KEEP_DAYS = 14  # 저장소 용량 관리: 최근 N일치 이미지만 남김


def sh(*cmd, check=True):
    r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} 실패:\n{r.stderr}")
    return r


def git_push(message):
    sh("git", "config", "user.name", "cardnews-bot")
    sh("git", "config", "user.email", "cardnews-bot@users.noreply.github.com")
    sh("git", "add", "-A", "output", "state.json")
    if sh("git", "diff", "--cached", "--quiet", check=False).returncode == 0:
        return
    sh("git", "commit", "-m", message)
    sh("git", "pull", "--rebase", "--autostash", check=False)
    sh("git", "push")


def image_urls(date_str, count):
    base = os.getenv("IMAGE_BASE_URL")
    if not base:
        repo = os.environ["GITHUB_REPOSITORY"]
        branch = os.getenv("GITHUB_REF_NAME", "main")
        base = f"https://raw.githubusercontent.com/{repo}/{branch}/output"
    return [f"{base.rstrip('/')}/{date_str}/slide_{i}.jpg" for i in range(1, count + 1)]


def cleanup_old(keep=KEEP_DAYS):
    days = sorted(p for p in OUTPUT.glob("*") if p.is_dir())
    for p in days[:-keep]:
        shutil.rmtree(p, ignore_errors=True)


def wait_until(hhmm):
    """한국시간 hhmm 까지 기다린다. 이미 지났으면 바로 돌아온다."""
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    h, m = map(int, hhmm.split(":"))
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target - now > timedelta(hours=3):   # 자정 근처 오작동 방지
        return
    if now < target:
        secs = (target - now).total_seconds()
        print(f"{hhmm}까지 {int(secs // 60)}분 {int(secs % 60)}초 기다렸다가 게시해요.")
        time.sleep(secs)


def choose_card(state, terms, args):
    """오늘의 용어와 카드 문구를 정한다.

    - 미리 써둔 문구(content_bank.json)가 있으면 API 없이 그걸 순서대로 사용 (무료)
    - 다 떨어졌는데 ANTHROPIC_API_KEY 가 있으면 Claude로 새로 생성
    """
    if args.mock:
        term = content.pick_term(state, terms, args.id, args.term)
        return term, content.mock_card_text(term)

    banked = content.next_bank_card(state, terms, args.id, args.term)
    if banked:
        return banked
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("미리 써둔 카드 문구가 다 떨어졌어요. Claude에게 'content_bank.json 채워줘'라고 부탁하거나, "
                 "ANTHROPIC_API_KEY 를 등록하면 자동으로 새로 만들어요.")

    for _ in range(8):
        term = content.pick_term(state, terms, args.id, args.term)
        card = content.generate_card_text(term)
        if not card.get("skip"):
            return term, card
        print(f"건너뜀: {term['term']} ({card.get('skip_reason')})")
        state["skipped"].append(term["id"])
        if args.id or args.term:
            sys.exit("직접 지정한 용어가 사회초년생용으로 너무 전문적이라 건너뛰었어요.")
    sys.exit("적절한 용어를 찾지 못했어요.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="이미지만 만들고 게시하지 않음")
    ap.add_argument("--mock", action="store_true", help="레이아웃 테스트용 가짜 문구 사용")
    ap.add_argument("--term", help="용어 이름 일부로 직접 지정")
    ap.add_argument("--id", type=int, help="용어 번호로 직접 지정")
    ap.add_argument("--publish-at", help="이 시각(한국시간 HH:MM)까지 기다렸다가 게시. 이미 지났으면 바로 게시")
    ap.add_argument("--check-token", action="store_true", help="인스타 토큰이 제대로 되는지만 확인")
    args = ap.parse_args()

    if args.check_token:
        from instagram import InstagramPublisher
        me = InstagramPublisher().whoami()
        print(f"토큰 정상! 연결된 계정: @{me.get('username')} ({me.get('account_type')}) / 사용자 ID {me.get('user_id')}")
        return

    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    terms = content.load_terms()
    state = content.load_state()

    out_dir = OUTPUT / today
    if (out_dir / "posted.txt").exists() and not args.dry_run:
        print("오늘은 이미 게시했어요. 종료합니다.")
        return

    saved = out_dir / "content.json"
    if saved.exists() and not (args.dry_run or args.id or args.term):
        # 앞선 실행이 카드는 만들고 게시에 실패했다면, 같은 카드를 그대로 다시 올린다
        data = json.loads(saved.read_text(encoding="utf-8"))
        term, card, caption = data["term"], data["card"], data["caption"]
        paths = sorted(out_dir.glob("slide_*.jpg"))
        number = data.get("number", state.get("posted", 0) + 1)
        print("오늘 만들어 둔 카드를 다시 사용해요.")
    else:
        term, card = choose_card(state, terms, args)
        number = state.get("posted", 0) + 1
        caption = content.build_caption(card, number)
        paths = render_cards(card, number, out_dir)
        saved.write_text(
            json.dumps({"term": term, "card": card, "caption": caption, "number": number},
                       ensure_ascii=False, indent=1),
            encoding="utf-8")
    print(f"[{today}] 오늘의 용어: {term['term']} -> {out_dir}")
    print("-" * 40 + f"\n{caption}\n" + "-" * 40)

    if args.dry_run:
        print("dry-run: 게시하지 않고 종료합니다.")
        return

    from instagram import InstagramPublisher

    # 이미지를 공개 저장소에 커밋해서 raw URL로 열리게 한다
    if not os.getenv("IMAGE_BASE_URL"):
        content.save_state(state)  # 건너뛴 용어 기록도 함께 저장
        git_push(f"cardnews {today}: {term['term']}")

    if args.publish_at:
        wait_until(args.publish_at)

    media_id = InstagramPublisher().publish_carousel(image_urls(today, len(paths)), caption)
    print(f"게시 완료! media id = {media_id}")

    # 게시에 성공했을 때만 '사용한 용어'로 기록
    if term["id"] not in state["used"]:
        state["used"].append(term["id"])
    state["posted"] = number
    content.save_state(state)
    (out_dir / "posted.txt").write_text(f"{media_id}\n", encoding="utf-8")
    cleanup_old()
    left = content.bank_remaining(state)
    if left <= 7 and not os.getenv("ANTHROPIC_API_KEY"):
        print(f"::warning::미리 써둔 카드 문구가 {left}개 남았어요. Claude에게 더 채워달라고 하세요.")
    if not os.getenv("NO_GIT"):
        git_push(f"posted {today}: {term['term']}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # 실패 원인을 GitHub 화면(주석)에 남긴다
        msg = str(e).replace("\n", " ")[:1500]
        print(f"::error title=카드뉴스 실패::{type(e).__name__}: {msg}")
        raise
