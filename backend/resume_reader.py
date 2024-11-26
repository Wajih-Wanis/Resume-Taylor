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
            "eductation": {{"degree/certification": "details"}},
            "experience": {{"company": "role and details"}},
            "project": {{"project name": "description"}},
            "hobbies": ["list of hobbies"],
            "languages": ["list of languages"]
        }}

        Resume content:
        {content}

        Provide only the JSON output, no additional text. Ensure all fields are present, using empty values if information is not found.
        """
    
    def parse_resume(self) -> Union[Resume,None]:
        try:
            # Read PDF content
            content = self.read_resume_pdf()
            
            # Create and send prompt to LLM
            prompt = self._create_prompt(content)
            llm_response = self.model._run(prompt)
            print(f"llm_response for resume parsing : {llm_response}")
            # Extract JSON from response (in case LLM adds additional text)
            try:
                # Find the first occurrence of '{' and the last occurrence of '}'
                start_idx = llm_response.find('{')
                end_idx = llm_response.rindex('}') + 1
                json_str = llm_response[start_idx:end_idx]
                
                # Parse JSON response
                resume_dict = json.loads(json_str)
                logging.info(f"Resume dict {resume_dict}")
                # Convert phone number to int if it's not already
                if isinstance(resume_dict.get('phone_number'), str):
                    resume_dict['phone_number'] = int(''.join(filter(str.isdigit, resume_dict['phone_number'])))
                
                # Create Resume object
                return Resume(**resume_dict)
            
            except json.JSONDecodeError as e:
                logging.info(f"Error parsing LLM response as JSON: {e}")
                logging.info("LLM response:", llm_response)
                return None
            
            except ValueError as e:
                print(f"Error creating Resume object: {e}")
                return None
            
        except Exception as e:
            print(f"Error processing resume: {e}")
            return None