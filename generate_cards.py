#!/usr/bin/env python3
"""
generate_cards.py
-----------------
Generates library age-category sign cards on A4 portrait pages.
Each card shows: שם סדרה | שם סופר/ת  in the Assistant Hebrew font.

Usage
-----
  # From a CSV file:
  python generate_cards.py data.csv output.pdf

  # Built-in demo (no CSV needed):
  python generate_cards.py --demo output.pdf

  # Choose how many columns (default 2) and rows (default 4) per page:
  python generate_cards.py data.csv output.pdf --cols 2 --rows 3

CSV format (UTF-8, with header row)
------------------------------------
  series,author,category
  "הארי פוטר","ג'יי קיי רולינג","ילדים"
  "קצה הזמן","דן לב","נוער"
  ...

Category values (case-insensitive, also accepts English):
  אחר / other
  מיוחדים / special
  גיל רך / 0-6
  ילדים / 7-12
  נוער / 13-18
  מבוגרות/ים / adults / 18+
"""

import argparse
import csv
import os
import sys
import urllib.request
from weasyprint import HTML, CSS

# ---------------------------------------------------------------------------
# Color palette per age category
# ---------------------------------------------------------------------------
CATEGORY_COLORS = {
    "אחר":         {"bg": "#2956AA", "text": "#FFFFFF"},
    "other":       {"bg": "#2956AA", "text": "#FFFFFF"},
    "מיוחדים":     {"bg": "#FFC980", "text": "#603700"},
    "special":     {"bg": "#FFC980", "text": "#603700"},
    "גיל רך":      {"bg": "#FFE9BD", "text": "#6E4A00"},
    "0-6":         {"bg": "#FFE9BD", "text": "#6E4A00"},
    "ילדים":       {"bg": "#FFE9BD", "text": "#6E4A00"},
    "7-12":        {"bg": "#FFE9BD", "text": "#6E4A00"},
    "נוער":        {"bg": "#77DFD5", "text": "#13534D"},
    "13-18":       {"bg": "#77DFD5", "text": "#13534D"},
    "מבוגרות/ים":  {"bg": "#F7F7F9", "text": "#262A33"},
    "מבוגרים":     {"bg": "#F7F7F9", "text": "#262A33"},
    "adults":      {"bg": "#F7F7F9", "text": "#262A33"},
    "18+":         {"bg": "#F7F7F9", "text": "#262A33"},
}

CATEGORY_LABELS = {
    "אחר":        "אחר",
    "other":      "אחר",
    "מיוחדים":    "מיוחדים",
    "special":    "מיוחדים",
    "גיל רך":     "גיל רך (0–6)",
    "0-6":        "גיל רך (0–6)",
    "ילדים":      "ילדים (7–12)",
    "7-12":       "ילדים (7–12)",
    "נוער":       "נוער (13–18)",
    "13-18":      "נוער (13–18)",
    "מבוגרות/ים": "מבוגרות/ים (18+)",
    "מבוגרים":    "מבוגרות/ים (18+)",
    "adults":     "מבוגרות/ים (18+)",
    "18+":        "מבוגרות/ים (18+)",
}

DEFAULT_COLORS = {"bg": "#EEEEEE", "text": "#333333"}

# ---------------------------------------------------------------------------
# Font handling
# ---------------------------------------------------------------------------
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_VF = os.path.join(FONT_DIR, "Assistant-VF.ttf")
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/assistant/Assistant%5Bwght%5D.ttf"


def ensure_font():
    """Download Assistant variable font if not already present."""
    if os.path.isfile(FONT_VF):
        return True
    os.makedirs(FONT_DIR, exist_ok=True)
    try:
        print("Downloading Assistant font...", end=" ", flush=True)
        urllib.request.urlretrieve(FONT_URL, FONT_VF)
        print("done.")
        return True
    except Exception as e:
        print(f"\nWarning: could not download font ({e}). Falling back to system font.")
        return False


def font_face_css():
    """Return @font-face CSS block using local file if available, else Google Fonts import."""
    if os.path.isfile(FONT_VF):
        font_path = FONT_VF.replace("\\", "/")
        return f"""@font-face {{
    font-family: 'Assistant';
    src: url('{font_path}') format('truetype');
    font-weight: 100 900;
}}"""
    # Fallback: try Google Fonts (requires internet)
    return "@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700&display=swap');"


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"/>
<style>
  {font_face}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Assistant', Arial, sans-serif;
    direction: rtl;
    unicode-bidi: embed;
    background: white;
  }}

  /* ---- A4 page shell ---- */
  .page {{
    width: 210mm;
    min-height: 297mm;
    padding: 10mm;
    page-break-after: always;
    display: grid;
    grid-template-columns: repeat({cols}, 1fr);
    grid-template-rows: repeat({rows}, 1fr);
    gap: 5mm;
    align-content: start;
  }}

  /* ---- Individual card ---- */
  .card {{
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6mm 8mm;
    min-height: {card_height}mm;
    text-align: center;
    overflow: hidden;
  }}

  .card-main {{
    font-size: {font_size}pt;
    line-height: 1.3;
    direction: rtl;
    word-break: break-word;
  }}

  .series-name {{
    font-weight: 700;
  }}

  .separator {{
    font-weight: 400;
    margin: 0 0.15em;
  }}

  .author-name {{
    font-weight: 400;
  }}

  .category-label {{
    font-size: {label_size}pt;
    font-weight: 600;
    margin-top: 3mm;
    opacity: 0.75;
  }}

  @media print {{
    @page {{
      size: A4 portrait;
      margin: 0;
    }}
    body {{
      margin: 0;
    }}
    .page {{
      page-break-after: always;
    }}
  }}
</style>
</head>
<body>
{pages}
</body>
</html>
"""

CARD_TEMPLATE = """\
<div class="card" style="background:{bg};color:{text};">
  <div class="card-main">
    <span class="series-name">{series}</span><span class="separator"> | </span><span class="author-name">{author}</span>
  </div>
  <div class="category-label">{cat_label}</div>
</div>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def escape_html(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def lookup_category(raw: str):
    key = raw.strip()
    colors = CATEGORY_COLORS.get(key) or CATEGORY_COLORS.get(key.lower(), DEFAULT_COLORS)
    label = CATEGORY_LABELS.get(key) or CATEGORY_LABELS.get(key.lower(), key)
    return colors, label


def build_card(series: str, author: str, category: str) -> str:
    colors, label = lookup_category(category)
    return CARD_TEMPLATE.format(
        bg=colors["bg"],
        text=colors["text"],
        series=escape_html(series),
        author=escape_html(author),
        cat_label=escape_html(label),
    )


def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def generate_pdf(cards_data, output_path, cols=2, rows=4):
    cards_per_page = cols * rows
    # A4 usable height = 297 - 20 (top+bottom padding) - gaps
    # gaps = (rows-1) * 5mm  →  total_gap = 15mm for 4 rows
    usable_h = 297 - 20 - (rows - 1) * 5
    card_height = usable_h / rows

    # Font size scales with card height (approx)
    font_size = max(11, min(22, int(card_height * 0.28)))
    label_size = max(7, font_size - 4)

    all_pages = []
    for page_cards in chunk(cards_data, cards_per_page):
        card_html = "\n".join(
            build_card(s, a, c) for s, a, c in page_cards
        )
        all_pages.append(
            f'<div class="page">\n{card_html}\n</div>'
        )

    html_content = HTML_TEMPLATE.format(
        font_face=font_face_css(),
        cols=cols,
        rows=rows,
        card_height=round(card_height, 1),
        font_size=font_size,
        label_size=label_size,
        pages="\n\n".join(all_pages),
    )

    HTML(string=html_content, base_url=".").write_pdf(output_path)
    print(f"✓ Saved {len(cards_data)} cards → {output_path}")


def read_csv(path):
    cards = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            series = row.get("series") or row.get("שם סדרה") or ""
            author = row.get("author") or row.get("שם סופר/ת") or row.get("מחבר") or ""
            category = row.get("category") or row.get("קטגוריה") or row.get("גיל") or "אחר"
            if series.strip():
                cards.append((series.strip(), author.strip(), category.strip()))
    return cards


DEMO_DATA = [
    ("הארי פוטר", "ג'יי.קיי. רולינג", "ילדים"),
    ("שר הטבעות", "ג'ון ר.ר. טולקין", "נוער"),
    ("מארס", "אנדי וויר", "מבוגרות/ים"),
    ("אמא של יוני", "שולמית לפיד", "גיל רך"),
    ("עליסה בארץ הפלאות", "לואיס קרול", "ילדים"),
    ("בין עצים", "ריצ'ארד פאוורס", "מבוגרות/ים"),
    ("כוכב קטן", "אנטואן דה סנט-אכזיפרי", "גיל רך"),
    ("הרצח של רוג'ר אקרויד", "אגאתה כריסטי", "אחר"),
    ("בואי נדבר על אהבה", "אנגס מקלאוד", "מיוחדים"),
    ("סנוני ואמזונות", "ארתור רנסום", "ילדים"),
    ("1984", "ג'ורג' אורוול", "מבוגרות/ים"),
    ("הצוללן", "ז'ול ורן", "נוער"),
]


def main():
    parser = argparse.ArgumentParser(
        description="Generate age-category library sign cards as a PDF on A4 pages."
    )
    parser.add_argument("input", nargs="?", help="CSV file (series,author,category)")
    parser.add_argument("--output", "-o", default="cards.pdf", help="Output PDF path (default: cards.pdf)")
    parser.add_argument("--demo", action="store_true", help="Generate a demo PDF with built-in sample data")
    parser.add_argument("--cols", type=int, default=2, help="Card columns per page (default: 2)")
    parser.add_argument("--rows", type=int, default=4, help="Card rows per page (default: 4)")
    args = parser.parse_args()

    if args.demo:
        cards = DEMO_DATA
        output = args.output
    elif args.input:
        cards = read_csv(args.input)
        output = args.output
    else:
        parser.print_help()
        sys.exit(1)

    if not cards:
        print("Error: no card data found.", file=sys.stderr)
        sys.exit(1)

    ensure_font()
    generate_pdf(cards, output, cols=args.cols, rows=args.rows)


if __name__ == "__main__":
    main()
