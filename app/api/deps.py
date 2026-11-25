from fastapi import Request

from services.query_engine import QueryEngine


def get_query_engine(request: Request) -> QueryEngine:
    return request.app.state.query_engine
