# html_pdf_generator.py
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

def generate_html_pdf(data: dict, signature_path: str, temp_id:str,output_path="form_output.pdf"):
    # Load template
    cwd = os.getcwd()
    templates_path = os.path.join(cwd, 'templates')

    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template(f'template_{temp_id}.html')

    # Make signature path relative (WeasyPrint needs file:// path)
    sig_url = sig_url = f"file:///{os.path.abspath(signature_path).replace(os.sep, '/')}" if signature_path else None

    # Render template with data
    print(sig_url)
    html_out = template.render(data=data, signature_path=sig_url)

    # Generate PDF
    HTML(string=html_out).write_pdf(output_path)
    print(f"PDF generated at {output_path}")

    with open("debug_output.html", "w", encoding="utf-8") as f:
     f.write(html_out)

