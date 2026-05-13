# pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


def generate_pdf(form_data: dict, signature_path: str, output_path: str = "form_output.pdf"):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "Medical Form Submission")
    y -= 1 * cm

    c.setFont("Helvetica", 11)
    for key, value in form_data.items():
        if isinstance(value, str):
            c.drawString(2 * cm, y, f"{key}: {value}")
            y -= 0.7 * cm
            if y < 4 * cm:
                c.showPage()
                y = height - 2 * cm

    # Signature
    if signature_path:
        y -= 1 * cm
        c.drawString(2 * cm, y, "Signature:")
        y -= 4.5 * cm
        try:
            c.drawImage(signature_path, 2 * cm, y, width=8*cm, height=3*cm)
        except Exception as e:
            c.drawString(2 * cm, y, f"Failed to load signature: {e}")

    c.showPage()
    c.save()
