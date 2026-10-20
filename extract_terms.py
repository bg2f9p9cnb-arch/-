"""한국은행 경제금융용어 800선 PDF -> terms.json (처음 한 번만 실행)

사용법: python extract_terms.py 경제금융용어800선.pdf
필요 패키지: pip install pdfplumber

PDF 구조(2026년 개정판 기준)
- 용어 제목: SUIT-ExtraBold 14pt
- 본문: KoPubBatang 10.5pt (수식은 KoPubDotumLight)
- 연관검색어: KoPubDotumMedium 9pt, '연관검색어'로 시작
"""
import json
import re
import sys

import pdfplumber


def cluster_rows(chars, tol=5):
    """세로 위치가 비슷한 글자를 한 줄로 묶는다 (영문/한글 폰트 높이 차이 보정)."""
    rows, cur, cur_top = [], [], None
    for c in sorted(chars, key=lambda c: (c["top"], c["x0"])):
        if cur and c["top"] - cur_top > tol:
            rows.append(cur)
            cur = []
        if not cur:
            cur_top = c["top"]
        cur.append(c)
    if cur:
        rows.append(cur)
    return rows


def line_text(chars):
    chars = sorted(chars, key=lambda c: c["x0"])
    out, prev = "", None
    for c in chars:
        if (prev is not None and prev["text"] != " " and c["text"] != " "
                and c["x0"] - prev["x1"] > c["size"] * 0.6):
            out += " "
        out += c["text"]
        prev = c
    return out


def is_title(cs):
    return any("SUIT-ExtraBold" in c["fontname"] and abs(c["size"] - 14) < 0.6 for c in cs)


def main(path, out="terms.json"):
    terms, cur, last_was_title = [], None, False
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for cs in cluster_rows(page.chars):
                raw = line_text(cs)
                text = raw.strip()
                if not text:
                    continue
                if is_title(cs):
                    if last_was_title and cur is not None and not cur["body"]:
                        cur["term"] += " " + text  # 두 줄짜리 제목 병합
                    else:
                        cur = {"term": text, "body": [], "related": ""}
                        terms.append(cur)
                    last_was_title = True
                    continue
                last_was_title = False
                if cur is None:
                    continue
                kor = [c for c in cs if "가" <= c["text"] <= "힣"] or cs
                font = kor[0]["fontname"]
                if "KoPubDotumMedium" in font and text.startswith("연관검색어"):
                    cur["related"] = text.replace("연관검색어", "").strip()
                elif "KoPubBatang" in font or "KoPubDotumLight" in font:
                    # 줄 끝에 공백이 있으면 단어 경계, 없으면 단어가 다음 줄로 이어짐
                    cur["body"].append(raw if raw.endswith(" ") else raw + "\u0000")

    for t in terms:
        body = "".join(t["body"]).replace("\u0000", "")
        t["body"] = re.sub(r"\s+", " ", body).strip()
        t["term"] = re.sub(r"\s+", " ", t["term"]).strip()
    terms = [t for t in terms if len(t["body"]) > 30]
    for i, t in enumerate(terms, 1):
        t["id"] = i
    with open(out, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=1)
    print(f"추출된 용어: {len(terms)}개 -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
