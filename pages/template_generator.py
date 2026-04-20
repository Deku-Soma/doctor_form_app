# template_generator.py
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
import base64
import tempfile

# Template mapping for all form types
TEMPLATE_MAP = {
    "workplace_drug_testing": "drug_testing.html",
    "vitamin_b_consent": "vitamin_b.html",
    "certificate_of_fitness": "certificate_fitness.html",
    "heights_questionnaire": "heights_questionnaire.html",
    "hot_cold_exposure": "hot_cold_exposure.html",
    "confined_spaces_questionnaire": "confined_spaces.html",
    "musculoskeletal_questionnaire": "musculoskeletal.html",
    "psychology_questionnaire": "psychology.html",
    "cwb_medical_referral": "cwb_referral.html",
    "complete_wellbeing": "complete_wellbeing.html",
    "annexure3_cwb": "annexure3.html"
}


def save_signature_temp(base64_data):
    """Convert base64 signature to temporary image file"""
    if not base64_data or base64_data == "":
        return None
    try:
        img_data = base64.b64decode(base64_data)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', mode='wb')
        temp_file.write(img_data)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        print(f"Error saving signature: {e}")
        return None


from Utility.file_manager import file_manager
from Utility.local_db import local_db
from Utility.app_context import get_resource_path
from datetime import datetime

def generate_pdf_for_form(form_type, data, output_path=None, employee_data=None, status="approved"):
    """
    Generate PDF for a specific form type
    
    Args:
        form_type: Form type identifier (e.g., 'workplace_drug_testing')
        data: Dictionary containing form data
        output_path: Optional override for path (legacy support)
        employee_data: Dictionary containing selected employee data
    """
    try:
        # Get template name
        template_name = TEMPLATE_MAP.get(form_type)
        if not template_name:
            raise ValueError(f"Unknown form type: {form_type}")
        
        # Setup Jinja2 environment
        cwd = os.getcwd()
        # Use resource path for templates
        templates_path = get_resource_path(os.path.join('templates', 'jinja2'))
        
        # Determine output path using FileManager if employee data provided
        final_path = output_path
        relative_path = ""
        filename = ""
        
        if employee_data and not final_path:
            company_folder = employee_data.get('company_folder')
            employee_folder = employee_data.get('folder_name')
            
            # Fallback if folder names missing (e.g. manual entry)
            if not company_folder:
                company_folder = "Unassigned_Company"
            if not employee_folder:
                employee_folder = f"{employee_data.get('full_name', 'Unknown')}_{employee_data.get('id_number', '000')}"
            
            final_path, relative_path, filename = file_manager.get_full_pdf_path(
                company_folder, 
                employee_folder, 
                form_type
            )
        elif not final_path:
            # Fallback for no employee data - save to root outputs
            filename = f"{form_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            final_path = os.path.join(cwd, "outputs", filename)
            relative_path = f"outputs/{filename}"
        
        # Create templates directory if it doesn't exist
        if not os.path.exists(templates_path):
            os.makedirs(templates_path)
        
        env = Environment(loader=FileSystemLoader(templates_path))
        template = env.get_template(template_name)
        
        # Handle signatures - convert base64 to temporary files
        temp_files = []
        signature_paths = {}
        
        # Check for various signature fields
        signature_fields = [
            'employee_signature_data',
            'examiner_signature_data',
            'ohnp_signature_data',
            'practitioner_signature_data',
            'signature_data',
            'employee_signature',
            'ohnp_signature',
            'practitioner_signature',
            'employee_signature_img',
            'ohn_signature_img'
        ]
        
        # Also check nested structures - Jinja2 can access nested dicts directly
        # No need to create dotted paths, just ensure the data is passed through
        
        # Check top-level signature fields and create data URIs
        for field in signature_fields:
            if field in data and isinstance(data[field], str) and data[field]:
                # Create data URI
                signature_paths[f"{field}_base64"] = f"data:image/png;base64,{data[field]}"
                # Also keep original
                signature_paths[field] = data[field]
        
        # Load logo and convert to data URI
        logo_path = get_resource_path(os.path.join('themes', 'Logo.png'))
        logo_data_uri = ""
        if os.path.exists(logo_path):
            try:
                with open(logo_path, 'rb') as logo_file:
                    logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
                    logo_data_uri = f"data:image/png;base64,{logo_base64}"
            except Exception as e:
                print(f"Warning: Could not load logo: {e}")
        
        # Load stamps and convert to data URIs
        stamp1_path = get_resource_path(os.path.join('themes', 'Dr.R.Malebye stamp.png'))
        stamp1_data_uri = ""
        if os.path.exists(stamp1_path):
            try:
                with open(stamp1_path, 'rb') as stamp_file:
                    stamp_base64 = base64.b64encode(stamp_file.read()).decode('utf-8')
                    stamp1_data_uri = f"data:image/png;base64,{stamp_base64}"
            except Exception as e:
                print(f"Warning: Could not load stamp 1: {e}")
        
        stamp2_path = get_resource_path(os.path.join('themes', 'helthcorp stamp.png'))
        stamp2_data_uri = ""
        if os.path.exists(stamp2_path):
            try:
                with open(stamp2_path, 'rb') as stamp_file:
                    stamp_base64 = base64.b64encode(stamp_file.read()).decode('utf-8')
                    stamp2_data_uri = f"data:image/png;base64,{stamp_base64}"
            except Exception as e:
                print(f"Warning: Could not load stamp 2: {e}")
        
        # Merge signature paths, logo, and stamps into data
        # Also add employee data if present
        render_data = {
            **data, 
            **signature_paths, 
            'logo_data_uri': logo_data_uri,
            'stamp1_data_uri': stamp1_data_uri,
            'stamp2_data_uri': stamp2_data_uri
        }
        
        if employee_data:
            render_data['company_name'] = employee_data.get('company_name', '')
            render_data['employee_name'] = employee_data.get('full_name', '')
            render_data['employee_id'] = employee_data.get('id_number', '')
            render_data['job_title'] = employee_data.get('job_title', '')
            render_data['department'] = employee_data.get('department', '')
        
        # Debug: Print signature-related data
        print(f"\n=== PDF Generation Debug for {form_type} ===")
        print(f"Signature paths created: {list(signature_paths.keys())}")
        if 'sign' in data:
            print(f"Sign object keys: {list(data['sign'].keys())}")
            for key, value in data['sign'].items():
                if 'signature' in key:
                    print(f"  {key}: {'<base64 data>' if value else 'EMPTY'}")
        print("===\n")
        
        # Render template
        html_out = template.render(**render_data)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(final_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate PDF
        HTML(string=html_out).write_pdf(final_path)
        print(f"PDF generated successfully at {final_path}")
        
        # Record in database if employee data present
        if employee_data and 'id' in employee_data:
            # Clean up path for database - ensure it's relative
            try:
                # Use os.path.relpath to get relative path from app root
                db_path = os.path.relpath(final_path, cwd)
            except ValueError:
                db_path = final_path
                
            doc_id = local_db.record_document(
                employee_id=employee_data['id'],
                form_type=form_type,
                file_path=db_path,
                file_name=filename,
                generated_by=data.get('generated_by', 'System')
            )
            
            # Create status record for approval workflow
            local_db.create_document_status(doc_id, status)
        
        # Save debug HTML for troubleshooting
        debug_path = final_path.replace('.pdf', '_debug.html')
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        
        return output_path
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise
    finally:
        # Clean up temporary signature files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_file}: {e}")


# Legacy function for backward compatibility
def generate_html_pdf(data: dict, signature_path: str, temp_id: str, output_path="form_output.pdf"):
    """Legacy function - kept for backward compatibility"""
    cwd = os.getcwd()
    templates_path = os.path.join(cwd, 'templates')

    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template(f'template_{temp_id}.html')

    # Make signature path relative (WeasyPrint needs file:// path)
    sig_url = f"file:///{os.path.abspath(signature_path).replace(os.sep, '/')}" if signature_path else None

    # Render template with data
    print(sig_url)
    html_out = template.render(data=data, signature_path=sig_url)

    # Generate PDF
    HTML(string=html_out).write_pdf(output_path)
    print(f"PDF generated at {output_path}")

    with open("debug_output.html", "w", encoding="utf-8") as f:
        f.write(html_out)
