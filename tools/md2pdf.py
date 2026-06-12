"""Minimal markdown -> PDF renderer for team docs (Unicode-safe via Windows TTF).

Usage: python tools/md2pdf.py <input.md> <output.pdf> [title]
Handles: H1/H2/H3, paragraphs, bullet lists, fenced code blocks, tables (as
monospace), horizontal rules. Inline **bold** markers are stripped.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from fpdf import FPDF

FONTS = Path(r"C:\Windows\Fonts")


def build_pdf(md_path: Path, pdf_path: Path, title: str) -> None:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("Body", "", str(FONTS / "arial.ttf"))
    pdf.add_font("Body", "B", str(FONTS / "arialbd.ttf"))
    pdf.add_font("Mono", "", str(FONTS / "consola.ttf"))
    pdf.add_page()

    epw = pdf.w - pdf.l_margin - pdf.r_margin

    def para(text: str, size=10.5, style="", indent=0.0, mono=False, lh=5.2):
        pdf.set_font("Mono" if mono else "Body", style, size)
        if indent:
            pdf.set_x(pdf.l_margin + indent)
        pdf.multi_cell(epw - indent, lh, text)

    in_code = False
    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if line.strip().startswith("```"):
            in_code = not in_code
            pdf.ln(1.5)
            continue
        if in_code:
            para(line if line.strip() else " ", size=7.6, mono=True, lh=3.8)
            continue
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        if not clean.strip():
            pdf.ln(2.5)
        elif clean.startswith("# "):
            pdf.ln(2); para(clean[2:], size=17, style="B", lh=8); pdf.ln(2)
        elif clean.startswith("## "):
            pdf.ln(3); para(clean[3:], size=13, style="B", lh=6.5); pdf.ln(1)
        elif clean.startswith("### "):
            pdf.ln(2); para(clean[4:], size=11.5, style="B", lh=6)
        elif clean.strip() == "---":
            pdf.ln(1)
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.l_margin + epw, y)
            pdf.ln(3)
        elif clean.lstrip().startswith("|"):
            para(clean, size=7.6, mono=True, lh=3.9)
        elif clean.lstrip().startswith(("- ", "* ")) or re.match(r"^\s*\d+\.\s", clean):
            para(clean.strip(), indent=4, lh=5.0)
        elif clean.startswith("> "):
            para(clean[2:], size=10, style="B", indent=4)
        else:
            para(clean)
    pdf.output(str(pdf_path))
    print(f"PDF written: {pdf_path}")


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    build_pdf(src, dst, sys.argv[3] if len(sys.argv) > 3 else src.stem)
