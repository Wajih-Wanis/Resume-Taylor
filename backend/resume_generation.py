from backend.model import Model
from backend.types import Resume,JobDescription
from fpdf import FPDF   
import docx 
from typing import Union
import json
import os 
import logging
from datetime import datetime


if not os.path.exists('logs'):
    os.makedirs('logs')

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_{current_time}.log")

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
        logging.info("Resume generation class instantiated")

    def _resume_generation_prompt(self, base_resume: Resume, job_description: JobDescription) -> str:
        # Construct a detailed prompt that focuses on aligning the resume with job requirements
        prompt = f"""
        Given the following base resume and job description, generate a tailored resume:

        Base Resume:
        - full_name: {base_resume.full_name or 'Not specified'}
        - profile: {base_resume.profile or 'Not specified'}
        - social: {base_resume.socials or {}}
        - skills: {', '.join(base_resume.skills or [])}
        - education: {base_resume.education}
        - experience: {base_resume.experience}
        - projects: {base_resume.projects or 'Not specified'}
        - hobbies: {base_resume.hobbies or []}
        - languages: {base_resume.languages or []}
        - location: {base_resume.location or 'Not specified'}

        Job Description:
        - Job Title: {job_description.job_title or 'Not specified'}
        - Required Skills: {', '.join(job_description.required_skills or [])}
        - Job Profile: {job_description.profile or 'Not specified'}
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


    def resume_creation(self, input: str) -> Union[Resume, None]:
        try:
            # Use the model to parse the input into a Resume object
            llm_generated_resume = self.model._run(input)
            logging.info(f"Resume generated llm blueprint {llm_generated_resume}")
            # Extract JSON from response (in case LLM adds additional text)
            try:
                # Find the first occurrence of '{' and the last occurrence of '}'
                start_idx = llm_generated_resume.find('{')
                end_idx = llm_generated_resume.rindex('}') + 1
                json_str = llm_generated_resume[start_idx:end_idx]
                
                # Parse JSON response
                resume_dict = json.loads(json_str)
                logging.info(f"Resume dict: {resume_dict}")
                
                # Preprocess fields to ensure they are compatible with the Resume model
                # Normalize phone_number
                if isinstance(resume_dict.get("phone_number"), str):
                    resume_dict["phone_number"] = int(
                        "".join(filter(str.isdigit, resume_dict["phone_number"]))
                    )
                
                # Ensure optional fields are present
                for field in Resume.__annotations__.keys():
                    if field not in resume_dict:
                        logging.info(f"Field not found {field}")
                        resume_dict[field] = None  # Default to None for missing fields

                # Preprocess education entries
                if isinstance(resume_dict.get("education"), list):
                    resume_dict["education"] = [
                        {
                            key: (value if isinstance(value, str) and value else "")
                            for key, value in entry.items()
                        }
                        for entry in resume_dict["education"]
                    ]

                # Handle optional list fields
                resume_dict["hobbies"] = resume_dict.get("hobbies") or []
                resume_dict["languages"] = resume_dict.get("languages") or []

                # Create Resume object
                logging.info(f"Processed Resume dict for validation: {resume_dict}")
                return Resume(**resume_dict)

            except json.JSONDecodeError as e:
                logging.error(f"Error parsing LLM response as JSON: {e}")
                logging.error(f"LLM response: {llm_generated_resume}")
                return None
            
            except ValueError as e:
                logging.error(f"Error creating Resume object: {e}")
                return None

        except Exception as e:
            logging.error(f"Error processing resume: {e}")
            return None

        

