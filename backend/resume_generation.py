from backend.model import Model
from backend.types import Resume,JobDescription
import pypdf
import docx 
import os 
import logging
from datetime import datetime


# Create the 'logs' directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create a unique filename with date and time
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_job_parser_{current_time}.log")

# Configure logging to write to the new log file with timestamps
logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)



class ResumeGenerator:

    def __init__(self,model:Model):
        self.model = model 

    def _resume_generation_prompt(self, base_resume: Resume, job_description: JobDescription) -> str:
        """
        Generate a prompt to customize the resume for a specific job description.
        
        :param base_resume: Original resume to be tailored
        :param job_description: Job description to align the resume with
        :return: A detailed prompt for resume customization
        """
        # Construct a detailed prompt that focuses on aligning the resume with job requirements
        prompt = f"""
        Given the following base resume and job description, generate a tailored resume:

        Base Resume:
        - Name: {base_resume.full_name}
        - Current Profile: {base_resume.profile or 'Not specified'}
        - Skills: {', '.join(base_resume.skills or [])}
        - Education: {base_resume.eductation}
        - Experience: {base_resume.experience}
        - Projects: {base_resume.project}

        Job Description:
        - Job Title: {job_description.job_title}
        - Required Skills: {', '.join(job_description.required_skills or [])}
        - Job Profile: {job_description.profile}
        - Key Tasks: {', '.join(job_description.tasks or [])}

        Instructions:
        1. Prioritize matching skills from the original resume to the job requirements
        2. Highlight experiences and projects most relevant to the job
        3. Adjust the profile summary to align with the job description
        4. Do NOT add any skills not present in the original resume
        5. Preserve the original resume's structure and personal details
        6. Focus on demonstrating how existing skills and experiences match the job needs

        Provide a JSON-formatted resume that closely matches the original Resume model.
        """
        return prompt

    def resume_creation(self,input:str) -> Resume:
        try:
            # Use the model to parse the input into a Resume object
            resume = self.model.parse_json_to_model(input, Resume)
            return resume
        except Exception as e:
            raise ValueError(f"Failed to create resume: {str(e)}")
        

    def save_pdf_resume(self,resume:Resume)->str:
        filename = f"{resume.full_name.replace(' ', '_')}_resume.pdf"
        filepath = os.path.join('resumes', filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create a PDF document (using a library like reportlab or pypdf)
        pdf_writer = pypdf.PdfWriter()
        pdf_page = pypdf.PdfPage()
        
        # Add resume details to the PDF
        pdf_content = self._format_resume_content(resume)
        pdf_page.add_text(pdf_content)
        pdf_writer.add_page(pdf_page)
        
        # Save the PDF
        with open(filepath, 'wb') as f:
            pdf_writer.write(f)
        
        return filepath
    


    def save_docx_resume(self,resume:Resume)-> str :
        # Generate a filename based on the resume's name
        filename = f"{resume.full_name.replace(' ', '_')}_resume.docx"
        filepath = os.path.join('resumes', filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create a new Word document
        doc = docx.Document()
        
        # Add resume details to the document
        doc.add_heading(f"Resume - {resume.full_name}", 0)
        
        # Add sections to the document
        sections = [
            ("Profile", resume.profile),
            ("Contact", f"Phone: {resume.phone_number}, Location: {resume.location}"),
            ("Skills", ", ".join(resume.skills or [])),
            ("Education", str(resume.eductation)),
            ("Experience", str(resume.experience)),
            ("Projects", str(resume.project))
        ]
        
        for title, content in sections:
            doc.add_heading(title, level=1)
            doc.add_paragraph(str(content) if content else "N/A")
        
        # Save the document
        doc.save(filepath)
        
        return filepath
    
    def _format_resume_content(self, resume: Resume) -> str:
        return f"""
        {resume.full_name}
        {resume.phone_number} | {resume.location}

        PROFILE
        {resume.profile}

        SKILLS
        {', '.join(resume.skills or [])}

        EDUCATION
        {resume.eductation}

        EXPERIENCE
        {resume.experience}

        PROJECTS
        {resume.project}
        """