from backend.types import JobDescription
from backend.model import Model
from bs4 import BeautifulSoup
import requests
import re 
from seleniumbase import Driver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
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

class JobParser:

    def __init__(self,job_link:str,model:Model):
        self.job_link = job_link 
        self.model = model 
        self.driver = Driver(uc=True,headless=True)


    def scrape_job(self) -> list[str]:
        try:
            # Navigate to page
            self.driver.get(self.job_link)
            
            # Wait for page to load (adjust timeout as needed)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Optional: Add random delay to mimic human behavior
            time.sleep(2 + (time.time() % 3))
            
            # Get page source
            page_source = self.driver.page_source
            
            # Parse HTML 
            soup = BeautifulSoup(page_source, 'html.parser')
            logging.info(f"Raw soup {soup}")
            # Remove script, style, and navigation elements
            for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            
            # Extract clean text
            text = soup.get_text(separator=' ', strip=True)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            logging.info(f"Clean page text {text}")
            # Split into chunks with 25% overlap
            return self._split_text_into_chunks(text)
        except Exception as e:
            logging.info(f"Error scraping job page: {e}")
            return []
        finally:
            # Close driver
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _split_text_into_chunks(self, text: str, max_chars: int = 8092, overlap_percent: float = 0.1) -> list[str]:
        # Calculate overlap size
        overlap_chars = int(max_chars * overlap_percent)
        
        # Split text into words
        words = text.split()
        
        chunks = []
        start = 0
        
        while start < len(words):
            # Calculate end index
            end = start
            current_chunk = []
            current_length = 0
            
            # Build chunk without cutting words
            while end < len(words) and current_length < max_chars:
                word = words[end]
                if current_length + len(word) + 1 > max_chars:
                    break
                current_chunk.append(word)
                current_length += len(word) + 1
                end += 1
            
            # Add chunk
            chunks.append(' '.join(current_chunk))
            
            # Move start index with overlap
            start = end - int(overlap_chars / 5)  # Approximate word-level overlap
        logging.info(f"Split chunks {chunks}")
        return chunks

    def _job_parsing_prompt(self, chunk: str) -> str:
        prompt = f"""
        You are an expert job description parser. Extract details from this job description chunk:

        Chunk:
        {chunk}

        IMPORTANT: If you find relevant information, update the JSON. 
        If not in this chunk, leave fields as they are.

        Provide the output as JSON with these keys:
        {{
            "job_poster": "string (company name)",
            "job_title": "string",
            "required_skills": ["skill1", "skill2", ...],
            "tasks": ["task1", "task2", ...]
            "profile" : "string profile required for the job"
        }}

        If no new information is found, return the existing JSON or empty values.
        """
        return prompt

    def job_parser(self) -> JobDescription:
        try:
            # Scrape job page
            job_chunks = self.scrape_job()
            
            if not job_chunks:
                raise ValueError("No job description content found")
            
            # Initialize result dictionary
            result = {
                "job_poster": "",
                "job_title": "",
                "required_skills": [],
                "tasks": []
            }
            
            # Process each chunk
            for chunk in job_chunks:
                # Create parsing prompt for this chunk
                prompt = self._job_parsing_prompt(chunk)
                
                # Use model to parse job description chunk
                llm_response = self.model._run(prompt)
                
                # Extract JSON from response
                try:
                    # Find the first occurrence of '{' and the last occurrence of '}'
                    start_idx = llm_response.find('{')
                    end_idx = llm_response.rindex('}') + 1
                    json_str = llm_response[start_idx:end_idx]
                    
                    # Parse JSON response
                    chunk_result = json.loads(json_str)
                    
                    # Update result, avoiding duplicates
                    # Update job_poster and job_title if not already set
                    if not result["job_poster"] and chunk_result.get("job_poster"):
                        result["job_poster"] = chunk_result["job_poster"]
                    
                    if not result["job_title"] and chunk_result.get("job_title"):
                        result["job_title"] = chunk_result["job_title"]
                    
                    # Merge skills and tasks, avoiding duplicates
                    result["required_skills"].extend(
                        [skill for skill in chunk_result.get("required_skills", []) 
                         if skill not in result["required_skills"]]
                    )
                    
                    result["tasks"].extend(
                        [task for task in chunk_result.get("tasks", []) 
                         if task not in result["tasks"]]
                    )
                
                except json.JSONDecodeError as e:
                    logging.info(f"Error parsing chunk response as JSON: {e}")
                    logging.info("Chunk response:", llm_response)
                    continue
            
            # Create JobDescription object
            return JobDescription(**result)
        
        except Exception as e:
            logging.info(f"Error parsing job description: {e}")
            return None