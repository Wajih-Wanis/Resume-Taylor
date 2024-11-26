from pydantic import BaseModel


class Resume(BaseModel):
    full_name : str | None
    phone_number : int | None
    location : str | None
    socials : dict[str,str] | None
    profile : str | None
    skills : list[str] | None
    eductation : dict[str,str] | None
    experience : dict[str,str] | None
    project : dict[str,str] | None
    hobbies : list[str] | None
    languages : list[str] | None



class JobDescription(BaseModel):
    job_poster : str | None
    job_title : str | None
    required_skills : list[str] | None
    tasks : list[str] | None
    profile : str | None
