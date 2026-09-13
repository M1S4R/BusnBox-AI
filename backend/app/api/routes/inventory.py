from fastapi import APIRouter, HTTPException, status

from app.schemas.inventory import InventorySearchRequest
from app.schemas.inventory_api import (
    InventorySearchBody,
    InventorySearchResponse,
)
from app.services.inventory_service import (
    InventoryServiceConfigurationError,
    InventoryServiceUnavailableError,
    inventory_service,
)

router = APIRouter(
    prefix="/api/inventory",
    tags=["Inventory"],
)


@router.post(
    "/search",
    response_model=InventorySearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_inventory(
    body: InventorySearchBody,
) -> InventorySearchResponse:
    try:
        result = await inventory_service.search_trips(
            InventorySearchRequest(
                source=body.source.strip(),
                destination=body.destination.strip(),
                travel_date=body.travel_date,
                minimum_seats=body.minimum_seats,
                bus_type=body.bus_type,
                operator=body.operator,
                maximum_price=body.maximum_price,
                sort_by=body.sort_by,
                page=body.page,
                page_size=body.page_size,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except InventoryServiceConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inventory integration is incorrectly configured.",
        ) from exc

    except InventoryServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inventory service is currently unavailable.",
        ) from exc

    return InventorySearchResponse(
        success=True,
        source=result.source,
        destination=result.destination,
        travel_date=result.travel_date,
        provider=result.provider,
        trip_count=len(result.trips),
        trips=result.trips,
    )
