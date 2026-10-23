"""오늘의 용어 선택 + 사회초년생용 쉬운 설명(카드 문구) 생성"""
import json
import os
import random
import re
from pathlib import Path

import requests

ROOT = Path(__file__).parent
TERMS_PATH = ROOT / "terms.json"
STATE_PATH = ROOT / "state.json"
BANK_PATH = ROOT / "content_bank.json"

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL") or "claude-sonnet-5-5"
API_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """너는 사회초년생에게 금융을 알려주는 친절한 인스타그램 카드뉴스 작가야.
한국은행 『경제금융용어 800선』의 원문 설명을 받아 카드뉴스용 문구로 다시 써줘.

[규칙]
1. 원문에 있는 사실·개념만 사용해. 원문에 없는 최신 수치, 금리, 세율, 통계, 날짜를 새로 만들지 마.
2. 비유와 예시는 '가상의 상황'이어야 하고, 예시에 숫자를 쓰면 가상의 숫자임이 드러나게 써('예를 들어').
3. 말투는 부드러운 해요체. 어려운 한자어와 영어 약어는 쉬운 말로 풀어 써.
4. 특정 상품·종목 추천, 투자 권유, 수익 보장 표현은 절대 금지.
5. 이모지는 쓰지 마(제목 아이콘은 템플릿이 넣어줘). 줄바꿈 문자도 넣지 마.
6. 꼭 기억할 핵심 표현은 **이렇게** 감싸서 굵게 표시해. 한 문단에 1~2번만.
7. 글자 수 제한을 반드시 지켜. 카드 칸이 정해져 있어서 넘치면 글씨가 작아져.
8. 사회초년생의 일상(월급, 첫 통장, 적금, 대출, 전월세, 카드, 연말정산 등)과 연결되는 예시를 우선해.
9. 중앙은행 내부 제도나 통계 작성 실무처럼 너무 전문적이라 사회초년생의 일상과 연결하기 어려운 용어라면 skip을 true로 하고 이유를 적어.

[출력] 설명 없이 아래 JSON 한 개만 출력해.
{
 "skip": false,
 "skip_reason": "",
 "term_display": "표지와 사전 칸에 크게 쓸 용어명(괄호·영문 병기 제외, 9자 이내 권장)",
 "term_alias": "영문명이나 다른 이름(예: '스프레드 · Spread'), 없으면 빈 문자열",
 "cover_top": "표지 첫 줄, 궁금증을 부르는 짧은 말(공백 포함 10자 이내, 예: '내 대출 금리가 왜?')",
 "one_line": "한 줄 요약(35자 이내)",
 "definition": "이게 뭐예요? 칸의 쉬운 설명 2~3문장(공백 포함 115자 이내)",
 "analogy_title": "비유 장 제목(10자 이내, 예: '쉽게 비유하면')",
 "analogy": "일상 비유 한 문단(110자 이내)",
 "example": "'예를 들어'로 시작하는 사회초년생 상황 예시 한 문단(140자 이내)",
 "key_points": ["핵심 1(28자 이내)", "핵심 2(28자 이내)", "핵심 3(28자 이내)"],
 "hashtags": ["표지에 앞의 3개가 들어가니 짧은 것부터", "#금융상식", "#사회초년생", "...총 6~8개"]
}"""

REQUIRED = ("term_display", "cover_top", "one_line", "definition", "analogy_title",
            "analogy", "example", "key_points", "hashtags")


def load_terms():
    return json.loads(TERMS_PATH.read_text(encoding="utf-8"))


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"used": [], "skipped": [], "cycle": 1, "posted": 0}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def pick_term(state, terms, term_id=None, term_name=None):
    """아직 쓰지 않은 용어 중 무작위로 하나. 다 쓰면 새 사이클 시작."""
    if term_id is not None:
        return next(t for t in terms if t["id"] == term_id)
    if term_name:
        return next(t for t in terms if term_name in t["term"])
    blocked = set(state["used"]) | set(state["skipped"])
    remaining = [t for t in terms if t["id"] not in blocked]
    if not remaining:
        state["used"] = []
        state["cycle"] = state.get("cycle", 1) + 1
        remaining = [t for t in terms if t["id"] not in set(state["skipped"])]
    return random.choice(remaining)


def load_bank():
    if BANK_PATH.exists():
        return json.loads(BANK_PATH.read_text(encoding="utf-8"))
    return []


def next_bank_card(state, terms, term_id=None, term_name=None, exclude=()):
    """미리 써둔 문구 중 아직 안 쓴 것을 순서대로 하나 꺼낸다. 없으면 None.
    exclude: 같은 날 다른 시간대에 이미 만들어 두고 아직 못 올린 용어 (중복 방지)"""
    by_id = {t["id"]: t for t in terms}
    used = set(state["used"]) | set(exclude)
    for entry in load_bank():
        tid = entry["term_id"]
        term = by_id.get(tid)
        if term is None:
            continue
        if term_id is not None and tid != term_id:
            continue
        if term_name and term_name not in term["term"]:
            continue
        if tid in used and term_id is None and not term_name:
            continue
        return term, entry["card"]
    return None


def bank_remaining(state):
    used = set(state["used"])
    return sum(1 for e in load_bank() if e["term_id"] not in used)


def _extract_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("JSON을 찾지 못했어요")
    return json.loads(text[start:end + 1])


def _clean(card):
    """이모지 등 폰트에 없는 문자를 제거한다."""
    emoji = re.compile("[\U0001F000-\U0001FAFF☀-➿️]")
    for k, v in card.items():
        if isinstance(v, str):
            card[k] = emoji.sub("", v).replace("\n", " ").strip()
        elif isinstance(v, list):
            card[k] = [emoji.sub("", x).strip() for x in v]
    card["hashtags"] = [h if h.startswith("#") else "#" + h for h in card.get("hashtags", [])]
    return card


def _validate(card):
    if card.get("skip"):
        return
    for key in REQUIRED:
        if not card.get(key):
            raise ValueError(f"누락된 필드: {key}")
    if len(card["key_points"]) != 3:
        raise ValueError("key_points는 3개여야 해요")


def generate_card_text(term, retries=2):
    """Claude API로 카드 문구 생성."""
    api_key = os.environ["ANTHROPIC_API_KEY"]
    user_msg = (f"용어: {term['term']}\n연관검색어: {term.get('related') or '없음'}\n\n"
                f"[한국은행 원문]\n{term['body']}")
    last_err = None
    for _ in range(retries + 1):
        resp = requests.post(
            API_URL,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": CLAUDE_MODEL, "max_tokens": 1500, "system": SYSTEM_PROMPT,
                  "messages": [{"role": "user", "content": user_msg}]},
            timeout=120,
        )
        if not resp.ok:
            raise RuntimeError(f"Claude API 오류 ({resp.status_code}): {resp.text}")
        text = "".join(b.get("text", "") for b in resp.json()["content"])
        try:
            card = _extract_json(text)
            _validate(card)
            return card if card.get("skip") else _clean(card)
        except (ValueError, json.JSONDecodeError) as e:
            last_err = e
    raise RuntimeError(f"카드 문구 생성 실패: {last_err}")


def mock_card_text(term):
    """API 없이 레이아웃·파이프라인 테스트용 (원문 앞부분 사용)."""
    sentences = re.split(r"(?<=다\.)\s", term["body"])
    name = re.sub(r"\(.*?\)", "", term["term"]).strip()[:12]
    alias = re.findall(r"\((.*?)\)", term["term"])
    return {
        "skip": False, "skip_reason": "",
        "term_display": name,
        "term_alias": alias[0] if alias else "",
        "cover_top": "이게 뭘까요?",
        "one_line": sentences[0][:35],
        "definition": " ".join(sentences[:2])[:115],
        "analogy_title": "쉽게 비유하면",
        "analogy": "(테스트용) 실제 실행에서는 Claude가 **일상 비유**를 만들어요.",
        "example": "(테스트용) 실제 실행에서는 사회초년생 상황 예시가 들어가요.",
        "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
        "hashtags": ["#금융용어", "#금융상식", "#사회초년생", "#재테크기초", "#경제공부"],
    }


def _strip(text):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text or "")


def build_caption(card, number):
    lines = [
        f"[오늘의 금융용어 #{number}] {card['term_display']}",
        "",
        _strip(card["one_line"]),
        "",
        f"쉽게 말하면: {_strip(card['analogy'])}",
        "",
        "나중에 다시 보고 싶다면 저장해두세요.",
        "팔로우하고 매일 금융상식 하나씩 챙겨가세요.",
        "",
        "출처: 한국은행 『경제금융용어 800선』을 바탕으로 쉽게 재구성했어요.",
        "이 콘텐츠는 정보 제공 목적이며 투자 권유가 아니에요.",
        "",
        " ".join(card["hashtags"][:8]),
    ]
    return "\n".join(lines)[:2200]
