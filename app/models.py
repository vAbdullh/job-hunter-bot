from pydantic import BaseModel


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str | None = None
    url: str
