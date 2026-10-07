"""The one-page brief as a real PDF file, rendered on the server from the session already there.

It reads the same session view as the result page and the printable brief page
(`Hub.view`), so the three cannot disagree, and it sends no Qloo or LLM request. The
layout follows `static/print.css` (art direction A, one A4 page): text stays selectable,
supplier links stay clickable, and the type steps down (never below about 6.6 pt) until
everything fits one page, as `static/print.js` does in the browser.

Needs the optional `fpdf2` package (pure Python; `requirements.txt`). Fonts are static
instances of Archivo and Newsreader (SIL Open Font License) in `motif/web/fonts/`.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

FONTS = Path(__file__).resolve().parent / "fonts"
INK, MUTE, HAIR, ACCENT = (18, 18, 18), (94, 91, 86), (207, 205, 198), (255, 74, 28)
PAGE_W, PAGE_H, ML, MR, MT, MB = 210.0, 297.0, 13.0, 13.0, 11.0, 10.0
LEFT_COL, GAP = 30.0, 5.0
PT = 25.4 / 72  # mm per point
FACES = {"black": "Archivo-Condensed-Black.ttf", "bold": "Archivo-Narrow-ExtraBold.ttf", "semi": "Archivo-SemiBold.ttf",
         "logo": "Archivo-Expanded-Black.ttf", "light": "Newsreader-Light.ttf", "text": "Newsreader-Regular.ttf",
         "strong": "Newsreader-SemiBold.ttf"}
# step-down levels: the scale applied to every type size, like print.css .fit1 … .fit3
LEVELS = (1.0, 0.94, 0.88, 0.82, 0.76, 0.7)


class PdfUnavailable(RuntimeError):
    """fpdf2 is not installed; the web app answers 503 instead of a broken file."""


def available() -> bool:
    try:
        import fpdf  # noqa: F401
    except ImportError:
        return False
    return True


def filename(brand: str) -> str:
    """MOTIF-<Brand>-Brief.pdf with the brand folded to ASCII letters, digits, and hyphens."""
    folded = "".join(c for c in unicodedata.normalize("NFKD", brand or "") if not unicodedata.combining(c))
    slug = re.sub(r"[^A-Za-z0-9]+", "-", folded).strip("-") or "Brand"
    return f"MOTIF-{slug[:60]}-Brief.pdf"


Segment = Tuple[str, str, float, Tuple[int, int, int], Optional[str]]  # text, face, size pt, colour, link


class _Brief:
    def __init__(self, scale: float):
        from fpdf import FPDF
        self.k = scale
        pdf = FPDF(unit="mm", format="A4")
        for face, file in FACES.items():
            pdf.add_font(face, "", str(FONTS / file))
        pdf.set_margins(ML, MT, MR)
        pdf.set_auto_page_break(True, margin=MB)
        pdf.set_creator("MOTIF")
        pdf.add_page()
        self.pdf = pdf
        self.right_x = ML + LEFT_COL + GAP

    # -- text -----------------------------------------------------------------------------------------

    def s(self, pt: float) -> float:
        return pt * self.k

    def seg(self, text: str, face: str = "text", size: float = 9.4, color=INK, link: Optional[str] = None) -> Segment:
        return (text, face, self.s(size), color, link)

    def flow(self, segments: Sequence[Segment], x: float, w: float, lh: float = 1.38, spacing: float = 0.0) -> None:
        """Lay out mixed-font segments as one paragraph between x and x + w.

        Wraps at spaces only (a word is never cut unless it is wider than the column), aligns
        every font on one baseline, and makes linked words clickable with an accent underline.
        """
        pdf = self.pdf
        # tokens grouped into unbreakable words: pieces of different segments with no space between
        # them ("(" + a linked trade name + ")") stay on one line
        groups: List[List[Tuple[str, Segment]]] = []
        joinable = False
        for seg in segments:
            for piece in re.findall(r"\n|[^\S\n]+|[^\s]+", seg[0]):
                if piece == "\n" or piece.isspace():
                    groups.append([(piece, seg)])
                    joinable = False
                elif joinable:
                    groups[-1].append((piece, seg))
                else:
                    groups.append([(piece, seg)])
                    joinable = True
        height = max((seg[2] for seg in segments if seg[0]), default=self.s(9.4)) * PT * lh

        def width(piece: str, seg: Segment) -> float:
            pdf.set_font(seg[1], size=seg[2])
            pdf.set_char_spacing(spacing)
            return pdf.get_string_width(piece)

        lines: List[List[Tuple[str, Segment, float]]] = [[]]
        used = 0.0
        for group in groups:
            piece, seg = group[0]
            if piece == "\n":
                lines.append([])
                used = 0.0
                continue
            if piece.isspace():
                if lines[-1]:
                    pw = width(" ", seg)
                    lines[-1].append((" ", seg, pw))
                    used += pw
                continue
            parts = [(p_, s_, width(p_, s_)) for p_, s_ in group]
            gw = sum(pw for _, _, pw in parts)
            if used + gw > w + 0.01 and lines[-1]:
                while lines[-1] and lines[-1][-1][0] == " ":
                    used -= lines[-1].pop()[2]
                lines.append([])
                used = 0.0
            for piece, seg, pw in parts:
                while pw > w - used and len(piece) > 1 and used == 0.0:  # one word wider than the column: cut it
                    cut = len(piece)
                    while cut > 1 and width(piece[:cut], seg) > w:
                        cut -= 1
                    lines[-1].append((piece[:cut], seg, width(piece[:cut], seg)))
                    lines.append([])
                    piece = piece[cut:]
                    pw = width(piece, seg)
                lines[-1].append((piece, seg, pw))
                used += pw

        y = pdf.get_y()
        for line in lines:
            if y + height > PAGE_H - MB:  # overflow is caught by the page count, as auto page break would
                pdf.add_page()
                y = MT
            baseline = y + height * 0.78
            cx = x
            for piece, (_, face, size, color, link), pw in line:
                pdf.set_font(face, size=size)
                pdf.set_char_spacing(spacing)
                pdf.set_text_color(*color)
                pdf.text(cx, baseline, piece)
                if link and piece.strip():
                    pdf.link(cx, y, pw, height, link)
                    pdf.set_draw_color(*ACCENT)
                    pdf.set_line_width(0.5 * PT)
                    pdf.line(cx, baseline + 0.5, cx + pw, baseline + 0.5)
                cx += pw
            y += height
        pdf.set_char_spacing(0)
        pdf.set_y(y)

    def gap(self, mm: float) -> None:
        self.pdf.set_y(self.pdf.get_y() + mm * self.k)

    # -- blocks ---------------------------------------------------------------------------------------

    def header(self, brand: str, label: str, title: str, lines: List[str], top_note: str) -> None:
        pdf = self.pdf
        y = MT
        pdf.set_font("logo", size=12)
        pdf.set_char_spacing(2.2)
        pdf.set_text_color(*INK)
        pdf.set_xy(ML, y)
        pdf.cell(60, 5, "MOTIF")
        pdf.set_char_spacing(0.8)
        pdf.set_font("semi", size=6.6)
        pdf.set_text_color(*MUTE)
        for i, text in enumerate(("PERFUMER BRIEF · SCENT DIRECTION", top_note.upper())):
            pdf.set_xy(ML, y + i * 3.1)
            pdf.cell(PAGE_W - ML - MR, 3.1, text, align="R")
        pdf.set_char_spacing(0)
        y += 7.4
        pdf.set_draw_color(*INK)
        pdf.set_line_width(1.5 * PT)
        pdf.line(ML, y, PAGE_W - MR, y)
        pdf.set_y(y + 4 * self.k)
        self.flow([self.seg(brand.upper(), "black", 28)], ML, PAGE_W - ML - MR, lh=0.95)
        self.gap(1.2)
        self.flow([self.seg(label.upper(), "bold", 6.6)], ML, 120, lh=1.3, spacing=0.9)
        self.gap(1.4)
        pdf.set_fill_color(*ACCENT)
        pdf.rect(ML, pdf.get_y(), 14, 1.4, style="F")
        self.gap(3.4)
        self.flow([self.seg(title, "light", 14)], ML, 170, lh=1.18)
        for line in lines:
            self.gap(0.9)
            self.flow([self.seg(line, size=8.6)], ML, 170)

    def section(self, num: str, title: str) -> float:
        """Rule, number, and title in the left column; returns the y where the right column starts."""
        pdf = self.pdf
        self.gap(3)
        y = pdf.get_y()
        pdf.set_draw_color(*INK)
        pdf.set_line_width(1 * PT)
        pdf.line(ML, y, PAGE_W - MR, y)
        y += 2 * self.k
        pdf.set_y(y)
        self.flow([self.seg(num, "black", 14)], ML, LEFT_COL, lh=1.0)
        self.gap(0.8)
        self.flow([self.seg(title.upper(), "bold", 7.2)], ML, LEFT_COL, lh=1.3, spacing=0.75)
        left_bottom = pdf.get_y()
        pdf.set_y(y)
        self._left_bottom = left_bottom
        return y

    def end_section(self) -> None:
        self.pdf.set_y(max(self.pdf.get_y(), self._left_bottom))

    @property
    def rw(self) -> float:
        return PAGE_W - MR - self.right_x

    def strip(self, x: float, y: float, w: float, h: float, props: List[Dict[str, Any]]) -> None:
        """MOTIF's scent strip (static/strips.js): one texture per pole, faint where not requested."""
        pdf = self.pdf
        px = 25.4 / 96  # the textures are drawn in CSS pixels
        body = h * 0.9
        with pdf.rect_clip(x, y, w, body):
            for p in props:
                tex = _TEXTURES.get(p.get("pole"))
                if not tex:
                    continue
                tw, th, draw = tex
                opacity = 0.95 if p.get("requested") else 0.3
                with pdf.local_context(stroke_opacity=opacity, fill_opacity=opacity):
                    pdf.set_draw_color(*INK)
                    pdf.set_fill_color(*INK)
                    ty = 0.0
                    while ty * px < body:
                        tx = 0.0
                        while tx * px < w:
                            draw(pdf, x + tx * px, y + ty * px, px)
                            tx += tw
                        ty += th
        pdf.set_draw_color(*INK)
        pdf.set_line_width(0.8 * PT)
        pdf.polygon([(x, y), (x + w, y), (x + w, y + body), (x + w / 2, y + h), (x, y + body)], style="D")


def _line(pdf, ox, oy, px, x1, y1, x2, y2, width):
    pdf.set_line_width(width * px)
    pdf.line(ox + x1 * px, oy + y1 * px, ox + x2 * px, oy + y2 * px)


def _circle(pdf, ox, oy, px, cx, cy, r, width=None):
    if width is None:
        pdf.ellipse(ox + (cx - r) * px, oy + (cy - r) * px, 2 * r * px, 2 * r * px, style="F")
    else:
        pdf.set_line_width(width * px)
        pdf.ellipse(ox + (cx - r) * px, oy + (cy - r) * px, 2 * r * px, 2 * r * px, style="D")


_TEXTURES = {  # tile width, tile height (CSS px), painter; mirrors static/strips.js
    "light": (16, 16, lambda p, x, y, s: _circle(p, x, y, s, 8, 8, 1.4)),
    "dense": (6, 6, lambda p, x, y, s: _circle(p, x, y, s, 3, 3, 1.3)),
    "polished": (10, 7, lambda p, x, y, s: _line(p, x, y, s, 0, 3.5, 10, 3.5, 0.9)),
    "raw": (14, 14, lambda p, x, y, s: [_line(p, x, y, s, *seg, 1.1) for seg in ((1, 4, 5, 2), (8, 9, 12, 6), (3, 12, 6, 10))]),
    "natural": (26, 16, lambda p, x, y, s: (p.set_line_width(s), p.bezier([(x, y + 8 * s), (x + 6.5 * s, y + 2 * s), (x + 13 * s, y + 8 * s)]),
                                            p.bezier([(x + 13 * s, y + 8 * s), (x + 19.5 * s, y + 14 * s), (x + 26 * s, y + 8 * s)]))),
    "synthetic": (12, 12, lambda p, x, y, s: [_line(p, x, y, s, 0, 0, 12, 0, 0.8), _line(p, x, y, s, 0, 0, 0, 12, 0.8)]),
    "warm": (9, 9, lambda p, x, y, s: _line(p, x, y, s, 0, 9, 9, 0, 0.9)),
    "cool": (9, 9, lambda p, x, y, s: _line(p, x, y, s, 4.5, 0, 4.5, 9, 0.8)),
    "intimate": (14, 14, lambda p, x, y, s: _circle(p, x, y, s, 7, 7, 2, 0.9)),
    "projecting": (44, 44, lambda p, x, y, s: [_circle(p, x, y, s, 22, 22, 9, 0.8), _circle(p, x, y, s, 22, 22, 18, 0.6)]),
    "sweet": (20, 20, lambda p, x, y, s: _circle(p, x, y, s, 10, 10, 3.4, 0.9)),
    "dry": (12, 12, lambda p, x, y, s: [_line(p, x, y, s, 0, 12, 12, 0, 0.5), _line(p, x, y, s, 0, 0, 12, 12, 0.5)]),
}


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _build(view: Dict[str, Any], scale: float):
    r = view["result"]
    brand = (view.get("resolution") or {}).get("name") or view.get("reference") or "Brand"
    date = (view.get("fetched") or [""])[0][:10]
    b = _Brief(scale)
    pdf = b.pdf
    pdf.set_title(f"MOTIF brief · {brand}")
    head = r["headline"]
    top = ("Recorded preview · " if view.get("data_label") == "recorded" else "") + "Cultural evidence sourced from Qloo" + (f" · {date}" if date else "")
    b.header(brand, head["label"], head["title"], head.get("lines") or [], top)
    x, w = b.right_x, b.rw
    n = 0

    def num() -> str:
        nonlocal n
        n += 1
        return f"{n:02d}"

    # 01 cultural profile
    b.section(num(), "Cultural profile")
    if not r["profile"]:
        text = ("Weaker signals, none strong enough to lead: " + "; ".join(
            p["label"].lower() + " (" + ", ".join(p["source_short"]) + ")" for p in r["minor"][:4]) + "."
                if r["minor"] else "MOTIF reads no motif in the Qloo descriptors.")
        b.flow([b.seg(text)], x, w)
    for p in r["profile"][:4]:
        segs = [b.seg(p["label"].upper() + " · ", "bold", 8.6),
                b.seg(p["strength_label"].lower() + ", " + ("references only: " if p["basis"]["kind"] == "related_only" else "")
                      + ", ".join(p["source_short"]) + "." + (" " + p["translation"] if p.get("translation") else "") + " Examples: ")]
        for i, e in enumerate(p["examples"][:3]):
            segs += [b.seg((", " if i else "")), b.seg(e["tag"].upper(), size=7.7), b.seg(f" ({e['entity']})")]
        segs.append(b.seg("."))
        b.flow(segs, x, w)
        b.gap(1.2)
    b.end_section()

    # 02 olfactory direction
    b.section(num(), "Olfactory direction")
    resolved = [d for d in r["dimensions"] if d["state"] == "resolved"]
    opened = [d for d in r["dimensions"] if d["state"] != "resolved"]
    segs: List[Segment] = []
    if resolved:
        for i, d in enumerate(resolved):
            segs += [b.seg(" · " if i else "", size=8.6), b.seg(d["word"].upper(), "strong", 8.6),
                     b.seg(f" ({d['name'].lower()}, {d['confidence_word']})", size=8.6)]
    else:
        segs.append(b.seg("No dimension resolved yet", size=8.6))
    segs.append(b.seg((". Open to the perfumer: " + ", ".join(
        d["name"].lower() + (" (motifs pull both ways)" if d["state"] == "balanced_open" else "") for d in opened) + ".")
                      if opened else ".", size=8.6))
    b.flow(segs, x, w)
    b.end_section()

    # 03 scent architecture
    a = r["architecture"]
    b.section(num(), "Scent architecture")
    if a["status"] != "proposed":
        b.flow([b.seg("No scent architecture is proposed: the structure is open to the perfumer.")], x, w)
    else:
        col = (w - 2 * 3) / 3
        top_y = pdf.get_y()
        bottoms = []
        strip_w, strip_h = 9.0, 34.0 * (0.82 if scale < 0.8 else 1.0)
        for i, role in enumerate(a["roles"]):
            cx = x + i * (col + 3)
            pdf.set_y(top_y)
            if role.get("open"):
                pdf.set_draw_color(*MUTE)
                with pdf.local_context(dash_pattern={"dash": 0.8, "gap": 0.6}):
                    pdf.set_line_width(0.5 * PT)
                    pdf.line(cx, top_y, cx + col, top_y)
                pdf.set_y(top_y + 1)
                b.flow([b.seg(role["name"].upper(), "black", 10)], cx, col, lh=1.0)
                b.flow([b.seg("Open to the perfumer", "bold", 9.6, MUTE)], cx, col, lh=1.15)
                bottoms.append(pdf.get_y())
                continue
            b.strip(cx, top_y, strip_w, strip_h, role.get("props") or [])
            tx, tw = cx + strip_w + 2.5, col - strip_w - 2.5
            pdf.set_y(top_y)
            b.flow([b.seg(role["name"].upper() + (" · TENTATIVE" if role.get("tentative") else ""), "black", 10)], tx, tw, lh=1.0)
            b.gap(0.6)
            b.flow([b.seg(role["label"], "bold", 9.6)], tx, tw, lh=1.15)
            b.gap(0.6)
            b.flow([b.seg(", ".join(role["descriptors"]), size=7.6)], tx, tw)
            refs = role.get("materials", [])[:2]
            if refs:
                b.gap(0.8)
                segs = [b.seg("e.g. ", size=7.6)]
                for j, m in enumerate(refs):
                    segs.append(b.seg(("; " if j else "") + m["generic"], size=7.6))
                    if m.get("example"):
                        segs += [b.seg(" (", size=7.6), b.seg(m["example"], size=7.6, link=m.get("url")), b.seg(")", size=7.6)]
                b.flow(segs, tx, tw)
            bottoms.append(max(pdf.get_y(), top_y + strip_h))
        pdf.set_y(max(bottoms) if bottoms else top_y)
    b.end_section()

    # 04 emphasize and avoid (only when supported)
    if a["emphasize"] or a["avoid"]:
        b.section(num(), "Emphasize and avoid")
        segs = []
        if a["emphasize"]:
            segs += [b.seg("Emphasize ", "strong"), b.seg("; ".join(e["label"].lower() for e in a["emphasize"]) + ". ")]
        if a["avoid"]:
            segs += [b.seg("Avoid ", "strong"), b.seg("; ".join(e["label"].lower() for e in a["avoid"]) + ".")]
        b.flow(segs, x, w)
        b.end_section()

    # 05 why, with sources
    b.section(num(), "Why")
    for wy in [w_ for w_ in r["why"] if w_["state"] == "resolved"][:3]:
        segs = [b.seg(f"{wy['name'].upper()} → {wy['word'].upper()} · ", "bold", 8.6)]
        for i, c in enumerate(wy["chain"][:2]):
            segs.append(b.seg(("; " if i else "") + c["label"] + (" (tentative)" if c.get("tentative") else "") + " from "))
            for j, e in enumerate(c["examples"][:2]):
                segs += [b.seg(", " if j else ""), b.seg(e["tag"].upper(), size=7.7)]
        segs.append(b.seg("."))
        b.flow(segs, x, w)
        b.gap(1.2)
    q = r["sources"]["qloo"]
    kinds = list(dict.fromkeys(_lower_first(rq["what"]) for rq in q["requests"]))
    b.flow([b.seg("Cultural evidence sourced from ", "strong", 7.4), b.seg("Qloo", "strong", 7.4, link="https://www.qloo.com/"),
            b.seg(" · fetched " + ", ".join(q["dates"]) + " · " + ", ".join(kinds)
                  + ". Every phrase traces to its Qloo entity, field, and request in MOTIF's session record.", size=7.4)], x, w)
    if r["sources"]["suppliers"]:
        b.gap(0.6)
        segs = [b.seg("Supplier pages (identity of the trade-name examples) · ", "strong", 7.4)]
        for i, sup in enumerate(r["sources"]["suppliers"]):
            segs += [b.seg(" · " if i else "", size=7.4), b.seg(sup["material"], size=7.4, link=sup["url"])]
        b.flow(segs, x, w)
    b.end_section()

    # 06 the brief
    brief = view.get("brief")
    if brief:
        b.section(num(), "The brief")
        if view.get("intent"):
            b.flow([b.seg("Application context: “" + view["intent"] + "”", size=7.6, color=MUTE)], x, w)
            b.gap(1)
        b.flow([b.seg(re.sub(r"\n\s*\n+", "\n", brief["text"]).strip(), size=7.9)], x, w, lh=1.36)
        if brief.get("author") == "llm":
            b.gap(1)
            b.flow([b.seg("Prose drafted by Claude from this result and checked against it.", size=7.6, color=MUTE)], x, w)
        b.end_section()

    # footer
    b.gap(4)
    y = pdf.get_y()
    pdf.set_draw_color(*HAIR)
    pdf.set_line_width(0.5 * PT)
    pdf.line(ML, y, PAGE_W - MR, y)
    pdf.set_y(y + 1.8)
    pdf.set_font("text", size=b.s(6.9))
    pdf.set_text_color(*MUTE)
    pdf.set_xy(PAGE_W - MR - 12, y + 1.8)
    pdf.cell(12, b.s(6.9) * PT * 1.38, f"{pdf.page} / {pdf.page}", align="R")
    pdf.set_y(y + 1.8)
    b.flow([b.seg("A creative direction, not a formula: not smelled or balanced, no proportions, no prediction of who will like it.",
                  size=6.9, color=MUTE)], ML, PAGE_W - ML - MR - 12)
    return pdf


def render(view: Dict[str, Any]) -> bytes:
    """One A4 page for a session view that has a result; the largest type that fits one page."""
    if not available():
        raise PdfUnavailable("PDF export needs the fpdf2 package")
    if not view.get("result"):
        raise ValueError("no result to print")
    pdf = None
    for scale in LEVELS:
        pdf = _build(view, scale)
        if pdf.pages_count == 1:
            break
    return bytes(pdf.output())
