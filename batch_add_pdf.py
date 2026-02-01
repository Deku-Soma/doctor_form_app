# batch_add_pdf.py
# Script to add PDF generation to remaining forms

import re

FORMS_TO_UPDATE = [
    ("pages/forms/form_psychology.py", "psychology_questionnaire", 193),
    ("pages/forms/form_musculoskeletal.py", "musculoskeletal_questionnaire", 182),
    ("pages/forms/form_hot_cold_exposure.py", "hot_cold_exposure", 225),
    ("pages/forms/form_heights_questionnaire.py", "heights_questionnaire", 175),
    ("pages/forms/form_confined_spaces.py", "confined_spaces_questionnaire", 233),
    ("pages/forms/form_certificate_fitness.py", "certificate_of_fitness", 244),
]

PDF_CODE_TEMPLATE = '''
            # Generate PDF
            try:
                from pages.template_generator import generate_pdf_for_form
                pdf_path = f"outputs/{form_type}_{{sub_id}}.pdf"
                generate_pdf_for_form("{form_type}", data, pdf_path)
                QMessageBox.information(self, "Success", f"Form saved successfully!\\nPDF: {{pdf_path}}")
            except Exception as pdf_error:
                print(f"PDF generation failed: {{pdf_error}}")
                import traceback
                traceback.print_exc()
                QMessageBox.information(self, "Success", "Form saved!\\n(PDF generation failed)")
'''

for file_path, form_type, line_num in FORMS_TO_UPDATE:
    print(f"\\nProcessing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the QMessageBox.information line
    target_line = line_num - 1  # Convert to 0-indexed
    
    if target_line < len(lines) and 'QMessageBox.information' in lines[target_line]:
        # Replace the success message with PDF generation code
        indent = len(lines[target_line]) - len(lines[target_line].lstrip())
        pdf_code = PDF_CODE_TEMPLATE.format(form_type=form_type)
        
        # Remove the old QMessageBox line
        lines[target_line] = pdf_code + '\\n'
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✓ Updated {file_path}")
    else:
        print(f"✗ Could not find target line in {file_path}")

print("\\n✅ Batch update complete!")
