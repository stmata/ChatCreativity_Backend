from pydantic import BaseModel
from typing import List, Optional

class ConfigModel(BaseModel):
    tone: str
    genderTone: str
    messageValue: int
    durationValue: str
    linkValue: Optional[str] = None

class DownloadRequest(BaseModel):
    ids: List[str]  
    format: Optional[str] = None

class AnalyzePayload(BaseModel):
    session_id: str
    prolific_id: str

class ChatRequest(BaseModel):
    message: str

class FinalIdeaRequest(BaseModel):
    idea: str
    prolific_id: str

