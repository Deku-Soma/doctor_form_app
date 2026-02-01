# add_pdf_generation.py
# Helper script to add PDF generation to all forms

import os
import re

FORMS_DIR = "pages/forms"

# Forms to update with their form types
FORMS_TO_UPDATE = [
    ("form_drug_testing.py", "workplace_drug_testing"),
    ("form_certificate_fitness.py", "certificate_of_fitness"),
    ("form_heights_questionnaire.py", "heights_questionnaire"),
    ("form_hot_cold_exposure.py", "hot_cold_exposure"),
    ("form_confined_spaces.py", "confined_spaces_questionnaire"),
    ("form_musculoskeletal.py", "musculoskeletal_questionnaire"),
    ("form_psychology.py", "psychology_questionnaire"),
    ("form_cwb_referral.py", "cwb_medical_referral"),
    ("form_annexure3.py", "annexure3_cwb"),
]

PDF_GENERATION_CODE = '''
            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                pdf_path = f"outputs/{form_type}_{sub_id}.pdf"
                generate_pdf_for_form("{form_type}", data, pdf_path)
                QMessageBox.information(self, "Success", f"Form saved successfully!\\nPDF generated at: {pdf_path}")
            except Exception as pdf_error:
                print(f"PDF generation failed: {pdf_error}")
                QMessageBox.information(self, "Success", "Form saved successfully!\\n(PDF generation failed - check logs)")
'''

def add_pdf_generation(file_path, form_type):
    """Add PDF generation code to a form file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the QMessageBox.information success message
    pattern = r'(QMessageBox\.information\(self, "Success", "[^"]+saved successfully!"\))'
    
    if re.search(pattern, content):
        # Replace with PDF generation code
        pdf_code = PDF_GENERATION_CODE.format(form_type=form_type)
        new_content = re.sub(pattern, pdf_code.strip(), content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Updated {file_path}")
        return True
    else:
        print(f"✗ Pattern not found in {file_path}")
        return False

if __name__ == "__main__":
    for filename, form_type in FORMS_TO_UPDATE:
        file_path = os.path.join(FORMS_DIR, filename)
        if os.path.exists(file_path):
            add_pdf_generation(file_path, form_type)
        else:
            print(f"✗ File not found: {file_path}")
