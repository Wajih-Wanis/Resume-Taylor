from pydantic import BaseModel



class Resume(BaseModel):
    full_name : str
    