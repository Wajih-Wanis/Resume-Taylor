from pydantic import BaseModel


class Resume(BaseModel):
    full_name : str
    phone_number : int
    location : str
    socials : dict[str]
    profile : str 
    skill : list[str]
    eductation : dict[str]
    experience : dict[str] 
    project : dict[str]
    hobbies : list[str]
    languages : list[str]



class JobDescription(BaseModel):
    job_poster : str 
    required_skills : list[str] 
    tasks : list[str] 

