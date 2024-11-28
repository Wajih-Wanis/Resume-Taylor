from pydantic import BaseModel
from typing import Optional, List, Dict


class Resume(BaseModel):
    full_name: Optional[str]
    phone_number: Optional[int]
    location: Optional[str]
    socials: Optional[Dict[str, str]]  
    profile: Optional[str]
    skills: Optional[List[str]]  
    education: Optional[List[Dict[str, str]]] 
    experience: Optional[List[Dict[str, str]]]  
    projects: Optional[Dict[str, str]]  
    hobbies: Optional[List[str]]  
    languages: Optional[List[str]]



class JobDescription(BaseModel):
    job_poster : str | None
    job_title : str | None
    required_skills : list[str] | None
    tasks : list[str] | None
    profile : str | None
