"""표지·마지막 장 배경 이미지

피그마 템플릿의 배경 자리(사진 칸)를 채운다.
- 저장소 맨 위에 bg_ 로 시작하는 사진(bg_1.jpg, bg_cafe.png 등)을 올리면 그걸 돌아가며 사용
- 없으면 부드러운 색 번짐 배경을 자동으로 만들어 사용
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
W, H = 1080, 1440  # 마지막 장 이미지 칸(1080x1440)에 맞춤. 표지는 위아래를 잘라 씀

# 템플릿 포인트 색(#567d45 초록)과 어울리는 차분한 팔레트: (바탕, 번짐 색들)
PALETTES = [
    ("#2f4a2a", ["#567d45", "#8fb07a", "#c9d8b6", "#3c5f34"]),   # 숲 초록
    ("#1f3340", ["#3f6a7d", "#8db3c2", "#d7e3e6", "#567d45"]),   # 청록
    ("#3b2f26", ["#8a6a4c", "#c9a87f", "#ead9c0", "#567d45"]),   # 웜 베이지
    ("#26283a", ["#4a5180", "#9aa3d1", "#dcdff0", "#6b8f5a"]),   # 남색
    ("#3a2a33", ["#7d4f63", "#c895a8", "#efd8df", "#567d45"]),   # 로즈
]


def _generated(number):
    rnd = random.Random(number * 7919)
    base, blobs = PALETTES[number % len(PALETTES)]
    img = Image.new("RGB", (W, H), base)
    layer = Image.new("RGB", (W, H), base)
    d = ImageDraw.Draw(layer)
    for i in range(7):
        color = blobs[i % len(blobs)]
        r = rnd.randint(260, 560)
        cx, cy = rnd.randint(-100, W + 100), rnd.randint(-100, int(H * 0.75))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(170))
    img = Image.blend(img, layer, 0.92)
    # 필름 그레인
    noise = Image.effect_noise((W, H), 18).convert("RGB")
    img = Image.blend(img, noise, 0.05)
    return img


def background_for(number, out_path):
    """number번째 게시물용 배경을 out_path(JPEG)로 저장하고 경로를 돌려준다."""
    photos = sorted(p for p in ROOT.glob("bg_*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    if photos:
        img = Image.open(photos[number % len(photos)]).convert("RGB")
        # 1080x1440 비율로 가운데 맞춰 자르기
        scale = max(W / img.width, H / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        left, top = (img.width - W) // 2, (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
    else:
        img = _generated(number)
    img.save(out_path, "JPEG", quality=92)
    return Path(out_path)
