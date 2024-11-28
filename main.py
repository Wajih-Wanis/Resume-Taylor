import streamlit as st
import os
import tempfile
from typing import Any, Dict

# Backend imports (Assuming these are your custom modules)
from backend.model import OssModel, Openai
from backend.resume_reader import ResumeReader
from backend.job_parser import JobParser
from backend.resume_generation import ResumeGenerator
from backend.types import Resume, JobDescription
import logging
from datetime import datetime


# Create the 'logs' directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create a unique filename with date and time
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_resume_creation_{current_time}.log")

# Configure logging to write to the new log file with timestamps
logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
# Sidebar configuration
def sidebar_config() -> None:
    st.sidebar.title("Model Configuration")

    # Model selection
    model_type = st.sidebar.selectbox(
        "Select AI Model", ["Open Source", "OpenAI", "Anthropic"]
    )

    # Initialize model in session state if not already initialized
    if 'model' not in st.session_state:
        st.session_state['model'] = None

    if 'model_type' not in st.session_state:
        st.session_state['model_type'] = None

    if 'credentials' not in st.session_state:
        st.session_state['credentials'] = {}

    # Credentials based on model type
    if model_type == "Open Source":
        st.sidebar.info("Using Open Source Model")
        if st.session_state['model_type'] != "Open Source":
            st.session_state['model'] = OssModel()
            st.session_state['model_type'] = "Open Source"

    elif model_type == "OpenAI":
        api_key = st.sidebar.text_input(
            "OpenAI API Key", type="password"
        )
        if st.sidebar.button("Validate OpenAI Key"):
            try:
                st.session_state['model'] = Openai(api_key)
                st.session_state['credentials']['api_key'] = api_key
                st.session_state['model_type'] = "OpenAI"
                st.sidebar.success("OpenAI Key Validated!")
            except Exception as e:
                st.sidebar.error(f"Validation Failed: {e}")

    # You can add Anthropic model initialization similarly

# Resume parsing section
def resume_parsing_section() -> None:
    st.header("Resume Parsing")

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)", type=['pdf'],
        help="Upload a PDF resume for parsing"
    )

    if uploaded_file is not None:
        # Check if the resume has already been parsed
        if 'resume_file_name' in st.session_state and st.session_state['resume_file_name'] == uploaded_file.name:
            st.write("Resume already uploaded and parsed.")
        else:
            # New file uploaded, parse it
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

            try:
                resume_parser = ResumeReader(tmp_file_path, st.session_state['model'])
                parsed_resume = resume_parser.parse_resume()

                # Store parsed resume
                st.session_state['parsed_resume'] = parsed_resume
                st.session_state['resume_file_name'] = uploaded_file.name

                os.unlink(tmp_file_path)
            except Exception as e:
                st.error(f"Error parsing resume: {e}")
                os.unlink(tmp_file_path)
            return

        # Display parsed resume for editing
        st.subheader("Resume Details")

        # Create editable fields for resume
        edited_resume = {}
        parsed_resume = st.session_state['parsed_resume']

        for field, value in parsed_resume.model_dump().items():
            if value is not None:
                if isinstance(value, list):
                    edited_resume[field] = st.multiselect(
                        f"Edit {field.replace('_', ' ').title()}",
                        options=value,
                        default=value
                    )
                elif isinstance(value, dict):
                    st.write(f"Edit {field.replace('_', ' ').title()}:")
                    edited_dict = {}
                    for k, v in value.items():
                        edited_dict[k] = st.text_input(f"{k}", v)
                    edited_resume[field] = edited_dict
                else:
                    edited_resume[field] = st.text_input(
                        f"Edit {field.replace('_', ' ').title()}",
                        value
                    )

        # Update the parsed resume with edited values
        st.session_state['parsed_resume'] = Resume(**edited_resume)
    else:
        st.session_state['parsed_resume'] = None

# Job description parsing section
def job_description_parsing_section() -> None:
    st.header("Job Description Parsing")

    parse_method = st.radio(
        "Job Description Parsing Method",
        ["Link Scraping", "Manual Entry"],
        key="parse_method"
    )

    if parse_method == "Link Scraping":
        job_link = st.text_input("Enter Job Posting URL")
        if st.button("Scrape Job Description"):
            try:
                parser = JobParser(job_link, st.session_state['model'])
                job_description = parser.job_parser()
                if job_description:
                    st.success("Job Description Scraped Successfully!")
                    st.session_state['job_description'] = job_description
                else:
                    st.warning("Failed to scrape job description.")
            except Exception as e:
                st.error(f"Scraping Error: {e}")
    else:
        st.subheader("Manually Enter Job Description")
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
            st.session_state['job_description'] = job_description

    # Allow editing of scraped/entered job description
    if 'job_description' in st.session_state and st.session_state['job_description']:
        job_description = st.session_state['job_description']
        st.subheader("Edit Job Description")

        edited_job_desc = {}
        for field, value in job_description.model_dump().items():
            if value is not None:
                if isinstance(value, list):
                    edited_job_desc[field] = st.multiselect(
                        f"Edit {field.replace('_', ' ').title()}",
                        options=value,
                        default=value
                    )
                else:
                    edited_job_desc[field] = st.text_input(
                        f"Edit {field.replace('_', ' ').title()}",
                        value
                    )

        # Update job description
        st.session_state['job_description'] = JobDescription(**edited_job_desc)
    else:
        st.session_state['job_description'] = None

# Resume generation and saving section
def resume_generation_section() -> None:
    st.header("Resume Generation")

    parsed_resume = st.session_state.get('parsed_resume', None)
    job_description = st.session_state.get('job_description', None)

    if parsed_resume and job_description:
        resume_generator = ResumeGenerator(st.session_state['model'])

        # Check if the resume has already been generated
        #if 'generated_resume' not in st.session_state:
            # Generate resume
        resume_generation_prompt = resume_generator._resume_generation_prompt(
                parsed_resume, job_description
            )
        logging.info(f"Resume generation prompt from main app {resume_generation_prompt}")
        generated_resume = resume_generator.resume_creation(resume_generation_prompt)
        st.session_state['generated_resume'] = generated_resume
        #else:
          #  logging.info("Found generated resume in session state")
            #   generated_resume = st.session_state['generated_resume']
        logging.info(generated_resume)
        # Display generated resume for final editing
        st.subheader("Generated Resume Preview")
        print(generated_resume)
        final_resume_edit = {}
        for field, value in generated_resume.model_dump().items():
            if value is not None:
                if isinstance(value, list):
                    final_resume_edit[field] = st.multiselect(
                        f"Edit {field.replace('_', ' ').title()}",
                        options=value,
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

        # Update final resume
        final_resume = Resume(**final_resume_edit)
        st.session_state['generated_resume'] = final_resume

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
    else:
        st.info("Please ensure both the resume and job description are provided.")

# Main Streamlit app
def main():
    st.title("AI Resume Generator")

    # Initialize session state variables
    if 'model' not in st.session_state:
        st.session_state['model'] = None

    if 'parsed_resume' not in st.session_state:
        st.session_state['parsed_resume'] = None

    if 'job_description' not in st.session_state:
        st.session_state['job_description'] = None

    if 'generated_resume' not in st.session_state:
        st.session_state['generated_resume'] = None

    # Sidebar configuration
    sidebar_config()

    # Resume parsing
    resume_parsing_section()

    # Job description parsing
    job_description_parsing_section()

    # Resume generation
    if st.session_state['parsed_resume'] and st.session_state['job_description']:
        resume_generation_section()

if __name__ == "__main__":
    main()      