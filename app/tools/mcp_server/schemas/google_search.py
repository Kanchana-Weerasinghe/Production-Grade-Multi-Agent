from pydantic import BaseModel

class GoogleSearchArgs(BaseModel):
    query: str

class GoogleSearchResult(BaseModel):
    results: list
