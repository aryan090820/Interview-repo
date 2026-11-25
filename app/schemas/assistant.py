from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool: str
    result: Any


class QuestionIn(BaseModel):
    question: str = Field(..., min_length=3)


class QueryAnswer(BaseModel):
    question: str
    sql: str
    attempts: int
    rows: list[dict[str, Any]]
