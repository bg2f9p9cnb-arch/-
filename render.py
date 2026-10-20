"""피그마 템플릿(googogogo011 카드뉴스)을 그대로 옮긴 HTML로 카드 이미지를 만든다.

피그마 원본 프레임 (1080x1350)
  1:67 썸네일   -> slide_cover
  1:35 본문 1   -> slide_body_image   (위쪽 이미지 칸 + 제목 + 본문 5줄)
  1:30 본문 2   -> slide_body_text    (제목 + 본문 12줄)  * 두 번 사용
  1:17 마지막장 -> slide_outro

브라우저(Chromium, Playwright)로 HTML을 찍어 JPEG로 저장합니다. (인스타그램 API는 JPEG만 받아요)
"""
import html
import os
import re
from pathlib import Path

from backgrounds import background_for

ROOT = Path(__file__).parent
FONTS = ROOT  # Pretendard 폰트 파일은 저장소 맨 위에 그대로 둬요
PROFILE = ROOT / "profile.jpg"

W, H = 1080, 1350
HANDLE = os.getenv("IG_HANDLE") or "@googogogo011"
PROFILE_NAME = os.getenv("PROFILE_NAME") or "지안"
ACCENT = "#567d45"      # 썸네일 태그 초록
FOLLOW_BLUE = "#3e5fff"  # 마지막장 팔로우 버튼

# 본문 제목 앞 아이콘 (템플릿처럼 제목 앞에 이모지 하나)
ICON_DEFINITION = "📌"
ICON_ANALOGY = "💡"
ICON_POINTS = "✅"


def _uri(path):
    return Path(path).resolve().as_uri()


def _rich(text):
    """HTML 이스케이프 후 **강조** 를 굵게 바꾼다."""
    text = html.escape(text or "")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def _plain(text):
    return html.escape(re.sub(r"\*\*(.+?)\*\*", r"\1", text or ""))


BASE_CSS = f"""
@font-face {{ font-family: 'Pretendard'; font-weight: 400; src: url('{_uri(FONTS / "Pretendard-Regular.otf")}'); }}
@font-face {{ font-family: 'Pretendard'; font-weight: 600; src: url('{_uri(FONTS / "Pretendard-SemiBold.otf")}'); }}
@font-face {{ font-family: 'Pretendard'; font-weight: 700; src: url('{_uri(FONTS / "Pretendard-Bold.otf")}'); }}
@font-face {{ font-family: 'Pretendard'; font-weight: 800; src: url('{_uri(FONTS / "Pretendard-ExtraBold.otf")}'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; }}
body {{ font-family: 'Pretendard', 'Noto Color Emoji', sans-serif; -webkit-font-smoothing: antialiased; word-break: keep-all; }}
.frame {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; }}
.abs {{ position: absolute; }}
.handle {{ position: absolute; left: 0; width: {W}px; text-align: center; font-weight: 700; font-size: 29px; line-height: normal; }}
b {{ font-weight: 700; }}
"""

# 글이 칸을 넘치면 글자 크기를 줄이는 스크립트
#  data-fit="height": 고정 높이 칸 안에 들어갈 때까지 / data-fit="width": 한 줄 폭에 맞을 때까지
FIT_JS = """
async () => {
  await document.fonts.ready;
  for (const el of document.querySelectorAll('[data-fit]')) {
    const mode = el.dataset.fit;
    const min = parseFloat(el.dataset.min || '20');
    let size = parseFloat(getComputedStyle(el).fontSize);
    const lhRatio = parseFloat(getComputedStyle(el).lineHeight) / size;
    const over = () => mode === 'width'
      ? el.scrollWidth > parseFloat(el.dataset.max)
      : el.scrollHeight > el.clientHeight + 1;
    while (over() && size > min) {
      size -= 1;
      el.style.fontSize = size + 'px';
      if (!isNaN(lhRatio)) el.style.lineHeight = (size * lhRatio) + 'px';
    }
  }
}
"""


def _page(body, extra_css=""):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS}{extra_css}</style></head><body>{body}</body></html>"


# ---------- 1:67 썸네일 ----------
def slide_cover(card, number, bg_path):
    title_top = _plain(card.get("cover_top", ""))
    title_main = _plain(card["term_display"])
    tags = " ".join(html.escape(t) for t in card["hashtags"][:3])
    css = f"""
    .bg {{ inset: 0; width: 100%; height: 100%; object-fit: cover; }}
    .grad {{ left: 0; bottom: 0; width: {W}px; height: 573px;
             background: linear-gradient(to top, rgba(5,5,5,0.84), rgba(107,107,107,0)); }}
    .tag {{ left: 86px; top: 853px; background: {ACCENT}; padding: 0 28px; color: #fff;
            font-weight: 600; font-size: 34px; letter-spacing: 0.68px; line-height: 60px; white-space: nowrap; }}
    .title {{ left: 84px; top: 936px; color: #fff; font-weight: 800; font-size: 95px; line-height: normal; }}
    .title div {{ white-space: nowrap; }}
    .tags {{ left: 84px; top: 1191px; color: #fff; font-weight: 400; font-size: 46px; line-height: normal; white-space: nowrap; }}
    """
    body = f"""
    <div class="frame">
      <img class="abs bg" src="{_uri(bg_path)}">
      <div class="abs grad"></div>
      <p class="handle" style="top:46px;color:#fff">{html.escape(HANDLE)}</p>
      <div class="abs tag">오늘의 금융용어 No.{number}</div>
      <div class="abs title">
        <div data-fit="width" data-max="912" data-min="54">{title_top}</div>
        <div data-fit="width" data-max="912" data-min="54">{title_main} ✷</div>
      </div>
      <p class="abs tags" data-fit="width" data-max="912" data-min="30">{tags}</p>
    </div>"""
    return _page(body, css)


# ---------- 1:35 본문 1 (이미지 칸 + 제목 + 본문) ----------
def slide_body_image(card, number):
    alias = _plain(card.get("term_alias", ""))
    css = f"""
    .frame {{ background: #edeef1; }}
    .box {{ left: 68px; top: 73px; width: 944px; height: 620px; background: #f0f0f0; border: 1px solid #000; }}
    .box .label {{ left: 48px; top: 44px; font-weight: 600; font-size: 28px; color: {ACCENT}; letter-spacing: 0.5px; }}
    .box .no {{ right: 48px; top: 44px; font-weight: 600; font-size: 28px; color: #8a8a8a; }}
    .box .word {{ left: 48px; right: 48px; top: 200px; text-align: center; font-weight: 800; font-size: 118px;
                  line-height: 1.15; color: #000a00; white-space: nowrap; }}
    .box .alias {{ left: 48px; right: 48px; top: 350px; text-align: center; font-weight: 400; font-size: 38px; color: #555; }}
    .box .rule {{ left: 48px; right: 48px; bottom: 112px; height: 1px; background: #000; }}
    .box .src {{ left: 48px; bottom: 50px; font-weight: 400; font-size: 26px; color: #6b6b6b; }}
    .title {{ left: 59px; top: 778px; width: 968px; height: 60px; display: flex; align-items: center;
              font-weight: 700; font-size: 42px; color: #000; white-space: nowrap; }}
    .text {{ left: 59px; top: 863px; width: 968px; height: 340px; overflow: hidden; color: #000a00;
             font-weight: 400; font-size: 39px; line-height: 65px; letter-spacing: -0.585px; }}
    """
    body = f"""
    <div class="frame">
      <div class="abs box">
        <p class="abs label">금융용어 사전</p>
        <p class="abs no">No.{number}</p>
        <p class="abs word" data-fit="width" data-max="848" data-min="60">{_plain(card["term_display"])}</p>
        <p class="abs alias">{alias}</p>
        <div class="abs rule"></div>
        <p class="abs src">한국은행 『경제금융용어 800선』</p>
      </div>
      <p class="abs title" data-fit="width" data-max="968" data-min="30">{ICON_DEFINITION} {_plain(card["term_display"])}, 이게 뭐예요?</p>
      <div class="abs text" data-fit="height" data-min="30">{_rich(card["definition"])}</div>
      <p class="handle" style="top:1265px;color:#000">{html.escape(HANDLE)}</p>
    </div>"""
    return _page(body, css)


# ---------- 1:30 본문 2 (제목 + 글) ----------
def slide_body_text(title, paragraphs):
    css = """
    .frame { background: #edeef1; }
    .title { left: 59px; top: 110px; width: 962px; height: 60px; display: flex; align-items: center;
             font-weight: 700; font-size: 50px; color: #000; white-space: nowrap; }
    .text { left: 59px; top: 235px; width: 915px; height: 975px; overflow: hidden; color: #000a00;
            font-weight: 400; font-size: 39px; line-height: 65px; letter-spacing: -0.585px; }
    .text p + p { margin-top: 65px; }   /* 템플릿의 빈 줄 한 칸 */
    """
    paras = "".join(f"<p>{_rich(p)}</p>" for p in paragraphs if p)
    body = f"""
    <div class="frame">
      <p class="abs title" data-fit="width" data-max="962" data-min="32">{title}</p>
      <div class="abs text" data-fit="height" data-min="30">{paras}</div>
      <p class="handle" style="top:1265px;color:#000">{html.escape(HANDLE)}</p>
    </div>"""
    return _page(body, css)


# ---------- 1:17 마지막장 ----------
def slide_outro(bg_path):
    css = f"""
    .bg {{ left: 0; top: -58px; width: 1080px; height: 1440px; object-fit: cover; }}
    .dim {{ inset: 0; background: rgba(0,0,0,0.34); }}
    .cta {{ left: 0; width: 1066px; top: 549px; text-align: center; color: #fff; font-weight: 400; font-size: 43px;
            line-height: normal; white-space: nowrap; }}
    .pill {{ left: 272px; top: 631px; width: 521px; height: 142px; border-radius: 71px; background: #fff; }}
    .avatar {{ left: 300px; top: 654px; width: 96px; height: 96px; border-radius: 50%; object-fit: cover; }}
    .who {{ left: 419px; top: 677px; color: #000; line-height: normal; white-space: nowrap; }}
    .who .name {{ font-weight: 700; font-size: 24px; }}
    .who .id {{ font-weight: 400; font-size: 18px; }}
    .btn {{ left: 571px; top: 680px; width: 173px; height: 44px; border-radius: 12px; background: {FOLLOW_BLUE};
            color: #fff; font-weight: 600; font-size: 18px; display: flex; align-items: center; justify-content: center; }}
    """
    body = f"""
    <div class="frame">
      <img class="abs bg" src="{_uri(bg_path)}">
      <div class="abs dim"></div>
      <p class="handle" style="top:46px;color:#fff">{html.escape(HANDLE)}</p>
      <p class="abs cta"><b>팔로우</b>하고 <b>금융상식</b> 얻어가세요!</p>
      <div class="abs pill"></div>
      <img class="abs avatar" src="{_uri(PROFILE)}">
      <div class="abs who"><p class="name">{html.escape(PROFILE_NAME)}</p><p class="id">{html.escape(HANDLE)}</p></div>
      <div class="abs btn">팔로우</div>
    </div>"""
    return _page(body, css)


def build_slides(card, number, bg_path):
    return [
        slide_cover(card, number, bg_path),
        slide_body_image(card, number),
        slide_body_text(f"{ICON_ANALOGY} {_plain(card['analogy_title'])}",
                        [card["analogy"], card["example"]]),
        _points_slide(card),
        slide_outro(bg_path),
    ]


def _points_slide(card):
    # 번호는 굵게, 내용은 **강조** 규칙 그대로
    paras = [f"**{i}.** {p}" for i, p in enumerate(card["key_points"][:3], 1)]
    paras.append(f"**한 줄 요약** {card['one_line']}")
    return slide_body_text(f"{ICON_POINTS} 이것만 기억해요", paras)


def render_cards(card, number, out_dir):
    """카드 5장을 out_dir/slide_1.jpg ~ slide_5.jpg 로 저장하고 경로 목록을 돌려준다."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    bg = background_for(number, out_dir / "_background.jpg")
    pages = build_slides(card, number, bg)

    paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, doc in enumerate(pages, 1):
            html_path = out_dir / f"_slide_{i}.html"
            html_path.write_text(doc, encoding="utf-8")
            page.goto(html_path.resolve().as_uri())
            page.evaluate(FIT_JS)
            out = out_dir / f"slide_{i}.jpg"
            page.screenshot(path=str(out), type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": W, "height": H})
            html_path.unlink()
            paths.append(out)
        browser.close()
    (out_dir / "_background.jpg").unlink(missing_ok=True)
    return paths
