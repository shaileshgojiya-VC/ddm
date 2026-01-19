"""
HTML to PDF conversion utilities.
"""

from weasyprint import HTML
from io import BytesIO


def html_to_pdf(html_content: str) -> BytesIO:
    """Convert HTML content to PDF."""
    pdf_file = BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file
