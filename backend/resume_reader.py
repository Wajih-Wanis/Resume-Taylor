from pypdf import PdfReader
from backend.types import Resume
from backend.model import Model
from typing import Union
import json
import os 
import logging
from datetime import datetime


# Create the 'logs' directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create a unique filename with date and time
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_resume_reader_{current_time}.log")

# Configure logging to write to the new log file with timestamps
logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)




class ResumeReader:

    def __init__(self,resume_path:str,model:Model):
        self.resume_path = resume_path
        self.model = model
    
    def read_resume_pdf(self) -> str:
        reader = PdfReader(self.resume_path)
        content = ""
        for page in reader.pages:
            logging.info(f"Raw pdf page {page}")
            if "/Annots" in page:
                for annotation in page["/Annots"]:
                    obj = annotation.get_object()
                    if "/A" in obj and "/URI" in obj["/A"]:
                        content+=obj["/A"]["/URI"]
            content+=page.extract_text()

        return content
    
    def _create_prompt(self, content: str) -> str:
        return f"""
        Please analyze the following resume content and extract the relevant information in JSON format.
        The output should strictly follow this structure:
        {{
            "full_name": "string",
            "phone_number": integer (just numbers, no spaces or special characters),
            "location": "string",
            "socials": {{"platform": "url"}},
            "profile": "string (summary/objective)",
            "skills": ["list of skills"],
            "education": [{{"degree/certification": "details"}}],
            "experience": [{{"company": "role and details"}}],
            "projects": {{"project name": "description"}},
            "hobbies": ["list of hobbies"],
            "languages": ["list of languages"]
        }}

        Resume content:
        {content}

        Provide only the JSON output, no additional text. Ensure all fields are present, using empty values (e.g., null, empty lists, or empty dictionaries) if information is not found. Adhere to this structure exactly.
        """

        
    def parse_resume(self) -> Union[Resume, None]:
        try:
            # Read PDF content
            content = self.read_resume_pdf()
            
            # Create and send prompt to LLM
            prompt = self._create_prompt(content)
            llm_response = self.model._run(prompt)
            logging.info(f"LLM response for resume parsing: {llm_response}")
            
            try:
                # Extract JSON from response
                start_idx = llm_response.find('{')
                end_idx = llm_response.rindex('}') + 1
                json_str = llm_response[start_idx:end_idx]
                resume_dict = json.loads(json_str)
                logging.info(f"Resume dict: {resume_dict}")
                
                try:
                    # Normalize phone_number
                    if isinstance(resume_dict.get("phone_number"), str):
                        resume_dict["phone_number"] = int(
                            "".join(filter(str.isdigit, resume_dict["phone_number"]))
                        )

                    # Ensure all optional fields are present
                    for field in Resume.__annotations__.keys():
                        if field not in resume_dict:
                            resume_dict[field] = None  # Default None for missing fields

                    # Preprocess education entries
                    if isinstance(resume_dict.get("education"), list):
                        resume_dict["education"] = [
                            {
                                key: (value if isinstance(value, str) and value else "")
                                for key, value in entry.items()
                            }
                            for entry in resume_dict["education"]
                        ]
                    # Preprocess education entries
                    if isinstance(resume_dict.get("experience"), list):
                        resume_dict["experience"] = [
                            {
                                key: (value if isinstance(value, str) and value else "")
                                for key, value in entry.items()
                            }
                            for entry in resume_dict["experience"]
                        ]
                    # Handle optional list fields
                    resume_dict["hobbies"] = resume_dict.get("hobbies") or []
                    resume_dict["languages"] = resume_dict.get("languages") or []
                    resume_dict["profile"] = resume_dict.get("profile") or ""

                    # Create Resume object
                    logging.info(f"Processed Resume dict for validation: {resume_dict}")
                    return Resume(**resume_dict)

                except ValueError as e:
                    logging.error(f"Error creating Resume object: {e}")
                    logging.error(f"Resume dict at error: {resume_dict}")
                    return None
            
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing LLM response as JSON: {e}")
                logging.error(f"LLM response: {llm_response}")
                return None
            
            except ValueError as e:
                logging.error(f"Error creating Resume object: {e}")
                return None
            
        except Exception as e:
            logging.error(f"Error processing resume: {e}")
            return None
