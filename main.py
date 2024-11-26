import streamlit as st
import os
import tempfile
import base64
from typing import Any, Dict

# Backend imports
from backend.model import OssModel, Openai
from backend.resume_reader import ResumeReader
from backend.job_parser import JobParser
from backend.resume_generation import ResumeGenerator
from backend.types import Resume, JobDescription

# Sidebar configuration
def sidebar_config() -> Dict[str, Any]:
    st.sidebar.title("Model Configuration")
    
    # Model selection
    model_type = st.sidebar.selectbox(
        "Select AI Model", 
        ["Open Source", "OpenAI", "Anthropic"]
    )
    
    # Credentials based on model type
    credentials = {}
    
    if model_type == "Open Source":
        st.sidebar.info("Using Open Source Model")
        model = OssModel()
    
    elif model_type == "OpenAI":
        credentials['api_key'] = st.sidebar.text_input(
            "OpenAI API Key", 
            type="password"
        )
        if st.sidebar.button("Validate OpenAI Key"):
            try:
                model = Openai(credentials['api_key'])
                st.sidebar.success("OpenAI Key Validated!")
            except Exception as e:
                st.sidebar.error(f"Validation Failed: {e}")
   # elif model_type == "Anthropic":
    #    credentials['api_key'] = st.sidebar.text_input(
    #        "Anthropic API Key", 
 #           type="password"
    #    )
   #     if st.sidebar.button("Validate Anthropic Key"):
    #        try:
  #              model = AnthropicModel(credentials['api_key'])
  #              st.sidebar.success("Anthropic Key Validated!")
 #           except Exception as e:
  #              st.sidebar.error(f"Validation Failed: {e}")
    return {
        'model_type': model_type, 
        'model': model, 
        'credentials': credentials
    }

# Resume parsing section
def resume_parsing_section(model):
    st.header("Resume Parsing")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)", 
        type=['pdf'],
        help="Upload a PDF resume for parsing"
    )
    
    if uploaded_file is not None:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            # Parse resume
            resume_parser = ResumeReader(tmp_file_path, model)
            parsed_resume = resume_parser.parse_resume()
            
            # Display parsed resume for editing
            st.subheader("Resume Details")
            
            # Create editable fields for resume
            edited_resume = {}
            
            # Dynamically create input fields based on resume attributes
            for field, value in parsed_resume.model_dump().items():
                if value is not None:
                    if isinstance(value, list):
                        # Handle list fields (skills, hobbies, etc.)
                        edited_resume[field] = st.multiselect(
                            f"Edit {field.replace('_', ' ').title()}", 
                            value, 
                            default=value
                        )
                    elif isinstance(value, dict):
                        # Handle dictionary fields (education, experience, etc.)
                        st.write(f"Edit {field.replace('_', ' ').title()}:")
                        edited_dict = {}
                        for k, v in value.items():
                            edited_dict[k] = st.text_input(f"{k}", v)
                        edited_resume[field] = edited_dict
                    else:
                        # Handle string and other fields
                        edited_resume[field] = st.text_input(
                            f"Edit {field.replace('_', ' ').title()}", 
                            value
                        )
            
            # Create modified resume
            modified_resume = Resume(**edited_resume)
            
            # Return the parsed and potentially modified resume
            os.unlink(tmp_file_path)  # Clean up temporary file
            return modified_resume
        
        except Exception as e:
            st.error(f"Error parsing resume: {e}")
            os.unlink(tmp_file_path)  # Clean up temporary file
            return None

# Job description parsing section
def job_description_parsing_section(model):
    st.header("Job Description Parsing")
    
    # Parse method selection
    parse_method = st.radio(
        "Job Description Parsing Method", 
        ["Link Scraping", "Manual Entry"]
    )
    
    job_description = None
    
    if parse_method == "Link Scraping":
        # Link input for scraping
        job_link = st.text_input("Enter Job Posting URL")
        
        if st.button("Scrape Job Description"):
            try:
                parser = JobParser(job_link, model)
                job_description = parser.job_parser()
                
                if job_description:
                    st.success("Job Description Scraped Successfully!")
                else:
                    st.warning("Failed to scrape job description.")
            except Exception as e:
                st.error(f"Scraping Error: {e}")
    
    else:  # Manual Entry
        st.subheader("Manually Enter Job Description")
        
        # Create input fields for job description
        job_poster = st.text_input("Job Poster (Company)")
        job_title = st.text_input("Job Title")
        required_skills = st.text_area("Required Skills (comma-separated)")
        tasks = st.text_area("Key Tasks (comma-separated)")
        profile = st.text_area("Job Profile")
        
        if st.button("Create Job Description"):
            job_description = JobDescription(
                job_poster=job_poster,
                job_title=job_title,
                required_skills=required_skills.split(',') if required_skills else [],
                tasks=tasks.split(',') if tasks else [],
                profile=profile
            )
    
    # Allow editing of scraped/entered job description
    if job_description:
        st.subheader("Edit Job Description")
        
        # Dynamically create input fields for editing
        edited_job_desc = {}
        for field, value in job_description.model_dump().items():
            if value is not None:
                if isinstance(value, list):
                    edited_job_desc[field] = st.multiselect(
                        f"Edit {field.replace('_', ' ').title()}", 
                        value, 
                        default=value
                    )
                else:
                    edited_job_desc[field] = st.text_input(
                        f"Edit {field.replace('_', ' ').title()}", 
                        value
                    )
        
        # Update job description
        job_description = JobDescription(**edited_job_desc)
        
        return job_description
    
    return None

# Resume generation and saving section
def resume_generation_section(model, parsed_resume, job_description):
    st.header("Resume Generation")
    
    if parsed_resume and job_description:
        # Initialize resume generator
        resume_generator = ResumeGenerator(model)
        
        # Generate resume
        resume_generation_prompt = resume_generator._resume_generation_prompt(
            parsed_resume, 
            job_description
        )
        
        generated_resume = resume_generator.resume_creation(resume_generation_prompt)
        
        # Display generated resume for final editing
        st.subheader("Generated Resume Preview")
        
        # Create editable fields for generated resume
        final_resume_edit = {}
        for field, value in generated_resume.model_dump().items():
            if value is not None:
                if isinstance(value, list):
                    final_resume_edit[field] = st.multiselect(
                        f"Edit {field.replace('_', ' ').title()}", 
                        value, 
                        default=value
                    )
                elif isinstance(value, dict):
                    st.write(f"Edit {field.replace('_', ' ').title()}:")
                    edited_dict = {}
                    for k, v in value.items():
                        edited_dict[k] = st.text_input(f"{k}", v)
                    final_resume_edit[field] = edited_dict
                else:
                    final_resume_edit[field] = st.text_input(
                        f"Edit {field.replace('_', ' ').title()}", 
                        value
                    )
        
        # Final resume creation
        final_resume = Resume(**final_resume_edit)
        
        # Save options
        save_col1, save_col2 = st.columns(2)
        
        with save_col1:
            if st.button("Save as PDF"):
                pdf_path = resume_generator.save_pdf_resume(final_resume)
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{final_resume.full_name}_resume.pdf",
                    mime="application/pdf"
                )
        
        with save_col2:
            if st.button("Save as DOCX"):
                docx_path = resume_generator.save_docx_resume(final_resume)
                with open(docx_path, "rb") as docx_file:
                    docx_bytes = docx_file.read()
                
                st.download_button(
                    label="Download DOCX",
                    data=docx_bytes,
                    file_name=f"{final_resume.full_name}_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# Main Streamlit app
def main():
    st.title("AI Resume Generator")
    
    # Sidebar configuration
    config = sidebar_config()
    model = config['model']
    
    # Resume parsing
    parsed_resume = resume_parsing_section(model)
    
    # Job description parsing
    job_description = job_description_parsing_section(model)
    
    # Resume generation
    if parsed_resume and job_description:
        resume_generation_section(model, parsed_resume, job_description)

if __name__ == "__main__":
    main()