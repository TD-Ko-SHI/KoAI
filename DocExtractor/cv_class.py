#this is to use the pydantic to extract the contents from document such as pdf and return the extracted information in a structured format.
from langchain_core.pydantic_v1 import BaseModel
from typing import Optional

class Experiences(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class Education(Experiences):
    degree: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    grade: Optional[str] = None

class WorkExperience(Experiences):
    company: Optional[str] = None
    position: Optional[str] = None
    responsibilities: Optional[str] = None

class Skill(BaseModel):
    name: str
    level: Optional[str] = None

class Individual(BaseModel):
    first_name: str
    last_name: str
    address: Optional[str] = None
    city: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[list[Education]] = None
    work_experience: Optional[list[WorkExperience]] = None
    skills: Optional[list[Skill]] = None
