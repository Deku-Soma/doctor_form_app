"""
FileManager - Utility for organizing PDF files into company/employee folder structure.
"""
import os
import re
from datetime import datetime


class FileManager:
    def __init__(self, base_path: str = "outputs"):
        self.base_path = base_path
        # Ensure base directory exists
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
    
    def sanitize_name(self, name: str) -> str:
        """
        Remove special characters and replace spaces with underscores.
        Safe for use as folder/file names.
        """
        # Remove characters that are problematic in file names
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace multiple spaces/whitespace with single underscore
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Remove any leading/trailing underscores
        return sanitized.strip('_')
    
    def get_company_folder(self, company_folder_name: str) -> str:
        """
        Get the path to a company's folder. Creates it if it doesn't exist.
        
        Args:
            company_folder_name: Sanitized company folder name (from database)
            
        Returns:
            Absolute path to company folder
        """
        company_path = os.path.join(self.base_path, company_folder_name)
        if not os.path.exists(company_path):
            os.makedirs(company_path)
        return os.path.abspath(company_path)
    
    def get_employee_folder(self, company_folder_name: str, employee_folder_name: str) -> str:
        """
        Get the path to an employee's folder within their company folder.
        Creates both folders if they don't exist.
        
        Args:
            company_folder_name: Sanitized company folder name
            employee_folder_name: Sanitized employee folder name (Name_IDNumber)
            
        Returns:
            Absolute path to employee folder
        """
        employee_path = os.path.join(self.base_path, company_folder_name, employee_folder_name)
        if not os.path.exists(employee_path):
            os.makedirs(employee_path)
        return os.path.abspath(employee_path)
    
    def generate_pdf_filename(self, form_type: str, date: datetime = None) -> str:
        """
        Generate a PDF filename with the form type and date.
        
        Args:
            form_type: Type of form (e.g., 'drug_testing', 'certificate_fitness')
            date: Date for the filename (defaults to today)
            
        Returns:
            Filename like 'drug_testing_2026-01-31.pdf'
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        # Sanitize form type just in case
        safe_form_type = self.sanitize_name(form_type)
        return f"{safe_form_type}_{date_str}.pdf"
    
    def get_full_pdf_path(self, company_folder_name: str, employee_folder_name: str,
                          form_type: str, date: datetime = None) -> tuple:
        """
        Get the full path for a new PDF file.
        Creates necessary folders and returns the path.
        
        Args:
            company_folder_name: Sanitized company folder name
            employee_folder_name: Sanitized employee folder name
            form_type: Type of form
            date: Date for filename (defaults to today)
            
        Returns:
            Tuple of (absolute_path, relative_path, filename)
        """
        employee_folder = self.get_employee_folder(company_folder_name, employee_folder_name)
        filename = self.generate_pdf_filename(form_type, date)
        
        # Handle duplicate filenames by adding a counter
        full_path = os.path.join(employee_folder, filename)
        counter = 1
        base_filename = filename.replace('.pdf', '')
        
        while os.path.exists(full_path):
            filename = f"{base_filename}_{counter}.pdf"
            full_path = os.path.join(employee_folder, filename)
            counter += 1
        
        # Calculate relative path from base_path
        relative_path = os.path.relpath(full_path, self.base_path)
        
        return full_path, relative_path, filename


# Singleton instance
file_manager = FileManager()
