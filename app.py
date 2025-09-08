from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import io

def create_pdf(summary_text, bullet_points):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "YouTube Video Summary")

    # Final Summary
    c.setFont("Helvetica-Bold", 12)
    y = height - 100
    c.drawString(50, y, "Final Summary:")
    y -= 20

    c.setFont("Helvetica", 11)
    lines = simpleSplit(summary_text, "Helvetica", 11, width - 100)
    for line in lines:
        c.drawString(50, y, line)
        y -= 15

    # Bullet Points
    c.setFont("Helvetica-Bold", 12)
    y -= 10
    c.drawString(50, y, "Bullet Points:")
    y -= 20

    c.setFont("Helvetica", 11)
    for i, point in enumerate(bullet_points, 1):
        wrapped_lines = simpleSplit(point, "Helvetica", 11, width - 100)
        c.drawString(50, y, f"{i}. {wrapped_lines[0]}")
        y -= 15
        for line in wrapped_lines[1:]:
            c.drawString(70, y, line)  # indent continuation lines
            y -= 15
        y -= 5  # space between bullets

        # Add new page if needed
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
