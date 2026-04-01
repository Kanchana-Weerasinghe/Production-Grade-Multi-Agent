from pydantic import BaseModel

class Budget(BaseModel):
    max_tokens: int
    max_tool_calls: int
    max_wall_time_sec: int
    max_retries: int

    used_tokens: int = 0
    used_tool_calls: int = 0
