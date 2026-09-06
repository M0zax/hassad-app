"""
The printable plan as a PDF (A4) -- the same content as app_logic.calendar_html
(title, one-line subtitle, the day-by-day table) set in the app's own paper,
ink and IBM Plex Sans Arabic, which carries both scripts.

Arabic is shaped and laid out right-to-left by fpdf2's text-shaping engine
(HarfBuzz); the table's columns run right-to-left too. Fonts live in fonts/.
"""

import os

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

from app_logic import tpl

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
PAPER, DEEP = (247, 241, 227), (239, 229, 207)
INK, MUTED, RULE, HAIR = (34, 25, 15), (107, 90, 68), (140, 118, 86), (217, 204, 176)

# column widths (mm) for the 182 mm text width: day, field, size, largest block, why
WIDTHS = (22, 16, 22, 32, 90)


def build(rows, lang="en"):
    """Return the PDF as bytes. `rows` are the schedule rows the app shows (display names)."""
    t = tpl(lang)
    rtl = lang == "ar"
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(14, 16, 14)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_font("plex", "", os.path.join(FONT_DIR, "IBMPlexSansArabic-Regular.ttf"))
    pdf.add_font("plex", "B", os.path.join(FONT_DIR, "IBMPlexSansArabic-SemiBold.ttf"))
    pdf.set_text_shaping(use_shaping_engine=True, direction="rtl" if rtl else "ltr",
                         script="arab" if rtl else "latn", language=lang)
    pdf.add_page()
    pdf.set_fill_color(*PAPER)
    pdf.rect(0, 0, 210, 297, style="F")
    align = "R" if rtl else "L"

    pdf.set_text_color(*INK)
    pdf.set_font("plex", "B", 20)
    pdf.cell(0, 12, t["cal_title"], align=align, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("plex", "", 10.5)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 6, t["cal_sub"], align=align, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    head = list(t["cal_head"])
    widths = list(WIDTHS)
    def why(text):
        # fpdf2's bidi reverses "35 + 34" inside Arabic: drop the left-to-right mark (the
        # browser needs it, fpdf2 trips on it) and join the sum with no-break spaces
        return text.replace("‎", "").replace(" + ", " + ") if rtl else text

    body = [[str(r["Day"]), str(r["Field"]), f"{r['Hectares']} {t['ha']}",
             f"{r['Largest block after (ha)']} {t['ha']}", why(str(r["Why this field now"]))] for r in rows]
    aligns = ["L", "L", "R", "R", "L"]
    if rtl:                                   # the first column sits at the right
        head, widths, aligns = head[::-1], widths[::-1], ["R" if a == "L" else "L" for a in aligns[::-1]]
        body = [row[::-1] for row in body]

    pdf.set_text_color(*INK)
    pdf.set_draw_color(*HAIR)
    pdf.set_line_width(0.2)
    heading = FontFace(family="plex", emphasis="BOLD", size_pt=9, color=MUTED, fill_color=PAPER)
    with pdf.table(col_widths=widths, text_align=aligns, headings_style=heading, line_height=5.2,
                   borders_layout="HORIZONTAL_LINES", padding=(1.6, 1.2), width=182,
                   first_row_as_headings=True) as table:
        hrow = table.row()
        for h in head:
            hrow.cell(h)
        for i, row in enumerate(body):
            style = FontFace(family="plex", emphasis="BOLD" if i == 0 else None, size_pt=10,
                             color=INK, fill_color=DEEP if i == 0 else None)
            r = table.row(style=style)
            for cell in row:
                r.cell(cell)
    return bytes(pdf.output())
