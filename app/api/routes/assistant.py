from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agent.tools import TOOL_REGISTRY, invoke_tool
from api.deps import get_query_engine
from db.session import get_db
from schemas.assistant import QueryAnswer, QuestionIn, ToolCall, ToolResult
from services.query_engine import QueryEngine

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/tools")
def list_tools() -> dict:
    return {"tools": sorted(TOOL_REGISTRY)}


@router.post("/tools/{tool_name}", response_model=ToolResult)
def call_tool(tool_name: str, payload: ToolCall, db: Session = Depends(get_db)):
    try:
        result = invoke_tool(db, tool_name, payload.arguments)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown tool {tool_name}")
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ToolResult(tool=tool_name, result=result)


@router.post("/query", response_model=QueryAnswer)
def ask_database(payload: QuestionIn, query_engine: QueryEngine = Depends(get_query_engine)):
    return query_engine.ask(payload.question)
