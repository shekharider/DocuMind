from pydantic import BaseModel


class DocumentResponse(BaseModel):

    id: int

    filename: str

    filepath: str

    session_id: int

    class Config:
        from_attributes = True