from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    title: str


class ChatSessionResponse(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    session_id: int
    role: str
    content: str