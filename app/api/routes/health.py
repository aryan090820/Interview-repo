from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    return {"status": "ok", "examples_indexed": len(request.app.state.query_engine.index)}
