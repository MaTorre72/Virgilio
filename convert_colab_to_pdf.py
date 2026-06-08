#!/usr/bin/env python3
"""Convert a Jupyter/Google Colab notebook into an orderly printable PDF.

The converter is designed for notebooks used as structured project documents.
It deliberately removes the Colab/Jupyter interactive interface and prints only
cell contents.

Layout rules:
- every notebook cell starts on a new A4 page;
- tables are kept together whenever they fit on one page;
- table cells wrap text instead of being clipped;
- code blocks wrap long lines;
- embedded graphics are scaled proportionally to fit the printable area;
- page numbers are added automatically.

Usage:
    python convert_colab_to_pdf.py input.ipynb output.pdf
    python convert_colab_to_pdf.py input.ipynb output.pdf --keep-html
"""
from __future__ import annotations

import argparse
import base64
import html
from pathlib import Path
import re
import sys

import cairosvg
import mistune
import nbformat
from weasyprint import HTML

CSS = r"""
@page {
  size: A4 portrait;
  margin: 14mm 13mm 18mm 13mm;
  @bottom-center {
    content: "Progetto Virgilio - pagina " counter(page) " / " counter(pages);
    color: #68756c;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 7.5pt;
  }
}

* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: #fff;
  color: #222;
  font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
  font-size: 9.5pt;
  line-height: 1.34;
}

.cell {
  break-before: page;
  page-break-before: always;
}
.cell:first-child {
  break-before: auto;
  page-break-before: auto;
}

h1, h2, h3, h4 {
  color: #1d3b2a;
  break-after: avoid-page;
  page-break-after: avoid;
}
h1 { font-size: 18pt; line-height: 1.12; margin: 0 0 7pt; }
h2 { font-size: 13.4pt; line-height: 1.18; margin: 13pt 0 5pt; }
h3 { font-size: 11.3pt; line-height: 1.20; margin: 10pt 0 4pt; }
h4 { font-size: 10.2pt; line-height: 1.20; margin: 8pt 0 3pt; }

p { margin: 0 0 6pt; orphans: 3; widows: 3; }
ul, ol { margin: 3pt 0 6pt; padding-left: 19pt; }
li { margin-bottom: 2pt; }
blockquote {
  margin: 6pt 0 8pt 8pt;
  padding: 3pt 8pt;
  border-left: 3px solid #86a58e;
  color: #333;
}
hr { border: 0; border-top: 1px solid #b9c8bd; margin: 8pt 0; }

a { color: inherit; text-decoration: underline; }
strong { font-weight: 700; }

/* Do not split tables across two pages unless a table is physically taller
   than the printable area. */
table {
  width: 100%;
  max-width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  border-spacing: 0;
  margin: 6pt 0 9pt;
  font-size: 7.75pt;
  line-height: 1.17;
  break-inside: avoid;
  page-break-inside: avoid;
}
thead, tbody, tr, th, td {
  break-inside: avoid;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid #aeb8b1;
  padding: 3px 4px;
  vertical-align: top;
  overflow-wrap: anywhere;
  hyphens: auto;
}
th {
  background: #e9f0eb;
  color: #1f3226;
  font-weight: 700;
}

code, pre {
  font-family: "DejaVu Sans Mono", Consolas, monospace;
}
code { font-size: 0.92em; }
pre {
  margin: 6pt 0 9pt;
  padding: 6pt;
  border: 1px solid #d5ddd7;
  background: #f5f7f5;
  font-size: 7.65pt;
  line-height: 1.22;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  break-inside: avoid;
  page-break-inside: avoid;
}

img, svg {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 250mm;
  margin: 4mm auto 0;
  object-fit: contain;
  break-inside: avoid;
  page-break-inside: avoid;
}

.graphic-cell { text-align: center; }
.graphic-cell p { margin: 0; }
.graphic-cell img,
.graphic-cell svg { max-height: 246mm; }

/* Graphic cells with a title need a little more vertical clearance. */
.graphic-cell.has-title img,
.graphic-cell.has-title svg { max-height: 236mm; }
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_notebook", type=Path)
    parser.add_argument("output_pdf", type=Path)
    parser.add_argument("--keep-html", action="store_true", help="Keep the intermediate clean HTML beside the PDF")
    return parser.parse_args()


def markdown_renderer():
    return mistune.create_markdown(
        escape=False,
        plugins=["table", "strikethrough", "task_lists"],
    )



def normalize_embedded_images(source: str) -> str:
    """Convert embedded SVG data URIs to high-resolution PNG data URIs.

    Mistune deliberately blocks SVG data URIs as potentially unsafe. For this
    local print workflow we rasterize them first, preserving the visual result
    while avoiding executable SVG content in the generated HTML.
    """
    pattern = re.compile(r"data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)")

    def replace(match: re.Match[str]) -> str:
        svg_bytes = base64.b64decode(match.group(1))
        # CairoSVG may not find a font containing a few UI symbols.
        # Replace them with robust ASCII equivalents before rasterization.
        svg_text = svg_bytes.decode("utf-8")
        svg_text = svg_text.replace("✓", "OK").replace("▸", "> ").replace("→", "->")
        png_bytes = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), output_width=1360)
        encoded = base64.b64encode(png_bytes).decode("ascii")
        return "data:image/png;base64," + encoded

    return pattern.sub(replace, source)


def make_html(notebook_path: Path) -> str:
    with notebook_path.open("r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    md = markdown_renderer()
    sections: list[str] = []
    for index, cell in enumerate(nb.cells):
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)

        source = normalize_embedded_images(source)

        classes = ["cell", f"cell-{index}"]
        if "data:image/" in source:
            classes.append("graphic-cell")
            # The first two graphic pages include a short title before the image.
            visible_prefix = source.split("![", 1)[0].strip()
            if visible_prefix:
                classes.append("has-title")

        if cell.cell_type == "markdown":
            content = md(source)
        elif cell.cell_type == "code":
            content = "<pre><code>" + html.escape(source) + "</code></pre>"
            outputs = cell.get("outputs", [])
            for output in outputs:
                if output.get("output_type") == "stream":
                    content += "<pre><code>" + html.escape("".join(output.get("text", ""))) + "</code></pre>"
        else:
            content = "<pre>" + html.escape(source) + "</pre>"

        sections.append(f'<section class="{" ".join(classes)}">{content}</section>')

    return """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>Progetto Virgilio</title>
<style>
%s
</style>
</head>
<body>
%s
</body>
</html>
""" % (CSS, "\n".join(sections))


def main() -> int:
    args = parse_args()
    notebook_path = args.input_notebook.resolve()
    output_pdf = args.output_pdf.resolve()
    if not notebook_path.exists():
        raise SystemExit(f"Notebook not found: {notebook_path}")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    html_path = output_pdf.with_suffix(".html")
    clean_html = make_html(notebook_path)
    html_path.write_text(clean_html, encoding="utf-8")

    HTML(string=clean_html, base_url=str(output_pdf.parent)).write_pdf(str(output_pdf))

    if not args.keep_html:
        html_path.unlink(missing_ok=True)

    print(output_pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
