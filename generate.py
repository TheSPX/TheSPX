"""Builds dark_mode.svg and light_mode.svg (neofetch-style profile card). Run: python generate.py"""
import io, json, urllib.request
from datetime import date
from xml.sax.saxutils import escape
from PIL import Image, ImageOps

USER = "TheSPX"
BIRTHDAY = None  # e.g. date(2005, 1, 31) to show your age as Uptime; None shows GitHub account age
INFO = [
    ("OS", "Windows, Android"),
    ("Host", "Morocco"),
    ("Kernel", "Mobile & Web Developer"),
    ("IDE", "Claude Code, VS Code"),
    None,
    ("Languages.Programming", "TypeScript, JavaScript"),
    ("Languages.Real", "Arabic, French, English"),
    ("Hobbies", "Motorcycles"),
]
CONTACT = [("GitHub", f"github.com/{USER}")]

WIDTH = 56  # characters per info line, key + dots + value
THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", art="#8b949e", head="#58a6ff", key="#ffa657", dots="#484f58", val="#c9d1d9"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", art="#57606a", head="#0969da", key="#953800", dots="#afb8c1", val="#24292f"),
}
RAMP = " .:-=+*#%@"


def get(url):
    with urllib.request.urlopen(url) as r:
        return r.read()


def uptime(start):
    t = date.today()
    y, m, d = t.year - start.year, t.month - start.month, t.day - start.day
    if d < 0:
        m, d = m - 1, d + 30
    if m < 0:
        y, m = y - 1, m + 12
    return f"{y} years, {m} months, {d} days"


def ascii_art(png, invert, cols=48, rows=28):
    img = ImageOps.autocontrast(Image.open(io.BytesIO(png)).convert("L"), cutoff=2).resize((cols, rows))
    px = list(img.getdata())
    if invert:
        px = [255 - p for p in px]
    lines = ["".join(RAMP[p * (len(RAMP) - 1) // 255] for p in px[r * cols:(r + 1) * cols]) for r in range(rows)]
    return [l.rstrip() for l in lines]


def span(text, color):
    return f'<tspan fill="{color}">{escape(text)}</tspan>'


def line(key, val, c):
    dots = "." * max(1, WIDTH - len(key) - len(val) - 3)
    return span(f"{key}: ", c["key"]) + span(f"{dots} ", c["dots"]) + span(val, c["val"])


def header(title, c):
    return span(f"{title} ", c["head"]) + span("─" * max(1, WIDTH - len(title) - 1), c["dots"])


def svg(theme, art, rows_right):
    c = THEMES[theme]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="500" viewBox="0 0 840 500" font-family="Consolas, Menlo, monospace" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="839" height="499" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>',
    ]
    out += [f'<text x="25" y="{40 + i * 15}" fill="{c["art"]}" xml:space="preserve">{escape(l)}</text>' for i, l in enumerate(art)]
    y = 45
    for row in rows_right:
        if row is not None:
            out.append(f'<text x="390" y="{y}" xml:space="preserve">{row(c)}</text>')
        y += 21
    out.append("</svg>")
    return "\n".join(out)


def main():
    user = json.loads(get(f"https://api.github.com/users/{USER}"))
    repos = json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100"))
    stars = sum(r["stargazers_count"] for r in repos)
    start = BIRTHDAY or date.fromisoformat(user["created_at"][:10])
    avatar = get(user["avatar_url"] + "&s=200")

    info = list(INFO)
    info.insert(1, ("Uptime", uptime(start)))
    rows = [lambda c: header(f"{USER.lower()}@github", c), None]
    rows += [None if r is None else (lambda c, r=r: line(*r, c)) for r in info]
    rows += [None, lambda c: header("─ Contact", c)]
    rows += [lambda c, r=r: line(*r, c) for r in CONTACT]
    rows += [None, lambda c: header("─ GitHub Stats", c)]
    rows += [
        lambda c: line("Repos", str(user["public_repos"]), c),
        lambda c: line("Stars", str(stars), c),
        lambda c: line("Followers", str(user["followers"]), c),
    ]
    for theme in THEMES:
        with open(f"{theme}_mode.svg", "w", encoding="utf-8") as f:
            f.write(svg(theme, ascii_art(avatar, invert=theme == "light"), rows))


if __name__ == "__main__":
    main()
