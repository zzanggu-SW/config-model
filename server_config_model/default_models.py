from pydantic import BaseModel


class DefaultResult(BaseModel):
    client: int = 0
    count_flag: int = 0
    grade: int = 0
    color: float = 0.0
    size: float = 0.0
