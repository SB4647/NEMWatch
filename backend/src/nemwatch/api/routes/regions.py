from fastapi import APIRouter

from nemwatch.api.schemas import RegionResponse

router = APIRouter(prefix="/api/v1/regions", tags=["regions"])


@router.get("", response_model=list[RegionResponse])
async def list_regions() -> list[RegionResponse]:
    return RegionResponse.all()
