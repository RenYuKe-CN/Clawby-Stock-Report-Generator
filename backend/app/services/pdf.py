"""PDF report generation — converts markdown report to professional PDF via WeasyPrint."""

from __future__ import annotations

import re
from io import BytesIO
from datetime import datetime
from typing import Any

from weasyprint import HTML

PDF_CSS = """
@page {
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
    @top-center {
        content: element(header);
        font-size: 8pt;
        color: #666;
    }
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #888;
    }
}
body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1a1a1a;
}
.cover-page {
    text-align: center;
    padding-top: 120px;
    page-break-after: always;
}
.cover-page h1 {
    font-size: 26pt;
    font-weight: 700;
    margin-bottom: 8px;
    color: #1a1a1a;
}
.cover-page .subtitle {
    font-size: 14pt;
    color: #555;
    margin-bottom: 40px;
}
.cover-page .meta {
    font-size: 10pt;
    color: #777;
    line-height: 2;
}
.cover-page .disclaimer {
    margin-top: 60px;
    font-size: 8pt;
    color: #aaa;
    font-style: italic;
}
h1 { font-size: 18pt; font-weight: 700; margin: 24pt 0 8pt; color: #1a1a1a; border-bottom: 2px solid #2563eb; padding-bottom: 4pt; }
h2 { font-size: 14pt; font-weight: 600; margin: 18pt 0 6pt; color: #333; }
h3 { font-size: 11pt; font-weight: 600; margin: 14pt 0 4pt; color: #444; }
p { margin: 6pt 0; text-align: justify; }
strong { font-weight: 700; color: #111; }
code { font-family: "SF Mono", "Menlo", monospace; font-size: 9pt; background: #f3f4f6; padding: 1pt 4pt; border-radius: 3pt; }
pre { background: #f3f4f6; padding: 8pt; border-radius: 4pt; font-size: 8pt; overflow-x: auto; border: 1px solid #e5e7eb; margin: 8pt 0; }
ul, ol { margin: 4pt 0; padding-left: 20pt; }
li { margin: 2pt 0; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 16pt 0; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0; font-size: 9pt; }
th { background: #2563eb; color: white; padding: 6pt 8pt; text-align: left; font-weight: 600; }
td { padding: 4pt 8pt; border-bottom: 1px solid #e5e7eb; }
tr:nth-child(even) td { background: #f9fafb; }
.footer-note { margin-top: 20pt; padding-top: 8pt; border-top: 1px solid #e5e7eb; font-size: 8pt; color: #888; }
"""


def md_to_html(md: str) -> str:
    """Convert a subset of Markdown to sanitized HTML."""
    html = md

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold, italic, inline code
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Horizontal rule
    html = re.sub(r'^---$', '<hr>', html, flags=re.MULTILINE)

    # Remove chart placeholders
    html = re.sub(r'!\[chart:.+?\]', '', html)

    # Lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^1\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Wrap consecutive <li> in <ul>
    html = re.sub(r'(<li>.*?</li>(\s*<li>.*?</li>)*)', r'<ul>\1</ul>', html, flags=re.DOTALL)

    # Wrap remaining bare lines in <p>
    lines = html.split('\n')
    wrapped = []
    for line in lines:
        t = line.strip()
        if not t:
            continue
        if t.startswith('<h') or t.startswith('<p') or t.startswith('<ul') or t.startswith('<li') or t.startswith('</') or t.startswith('<hr') or t.startswith('<pre') or t.startswith('<code'):
            wrapped.append(line)
        else:
            wrapped.append(f'<p>{t}</p>')
    html = '\n'.join(wrapped)

    return html


def build_html(
    ticker: str,
    template_name: str,
    provider_name: str,
    model: str,
    generated_at: str,
    markdown_body: str,
) -> str:
    """Build a complete A4 HTML document for PDF generation."""
    body_html = md_to_html(markdown_body)
    gen_date = generated_at[:10] if generated_at else "N/A"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{PDF_CSS}</style>
</head>
<body>

<!-- Cover Page -->
<div class="cover-page">
    <h1>{ticker}</h1>
    <div class="subtitle">{template_name}</div>
    <div class="meta">
        <div>Generated: {gen_date}</div>
        <div>Model: {provider_name} / {model}</div>
        <div>Data Source: Clawby</div>
    </div>
    <div class="disclaimer">
        Not investment advice. This report is for informational purposes only.
    </div>
</div>

<!-- Report Content -->
{body_html}

<div class="footer-note">
    <p>Report generated on {gen_date} using {provider_name} / {model}. Data sourced from Clawby.</p>
    <p><strong>Not investment advice.</strong></p>
</div>

</body>
</html>"""


def generate_pdf(
    ticker: str,
    template_name: str,
    provider_name: str,
    model: str,
    generated_at: str,
    markdown_body: str,
) -> bytes:
    """Generate PDF bytes from report data."""
    html_str = build_html(ticker, template_name, provider_name, model, generated_at, markdown_body)
    buf = BytesIO()
    HTML(string=html_str).write_pdf(buf)
    return buf.getvalue()
