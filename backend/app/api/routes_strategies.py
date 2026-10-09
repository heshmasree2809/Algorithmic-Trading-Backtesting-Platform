from fastapi import APIRouter

from app.schemas.schemas import StrategyOut
from app.strategies.implementations import list_strategies

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyOut])
def get_strategies():
    return list_strategies()
