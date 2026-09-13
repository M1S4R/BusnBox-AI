import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.integrations.inventory.base import (
    InventoryAuthenticationError,
    InventoryProvider,
    InventoryResponseError,
    InventoryUnavailableError,
)
from app.schemas.inventory import (
    InventorySearchRequest,
    InventorySearchResult,
)

logger = logging.getLogger(__name__)


class CompanyInventoryProvider(InventoryProvider):
    """
    HTTP client for the company's inventory API.

    The current request and response formats are placeholders based on the
    BusNBox normalized contract. Update only the mapping methods when the
    company provides its official API documentation.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        search_path: str | None = None,
        api_key: str | None = None,
        api_key_header: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.search_path = (
            search_path or settings.inventory_api_search_path
        )

        self._owns_client = client is None

        if client is not None:
            self.client = client
            return

        headers = {
            "Accept": "application/json",
            "User-Agent": "BusNBox-AI/1.0",
        }

        resolved_api_key = api_key or settings.inventory_api_key
        resolved_key_header = (
            api_key_header or settings.inventory_api_key_header
        )

        if resolved_api_key:
            headers[resolved_key_header] = resolved_api_key

        timeout = httpx.Timeout(
            timeout=settings.inventory_api_timeout_seconds,
            connect=settings.inventory_api_connect_timeout_seconds,
        )

        self.client = httpx.AsyncClient(
            base_url=base_url or settings.inventory_api_base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=False,
        )

    async def search_trips(
        self,
        search: InventorySearchRequest,
    ) -> InventorySearchResult:
        request_params = self._build_search_params(search)

        try:
            response = await self.client.get(
                self.search_path,
                params=request_params,
            )

            self._raise_for_status(response)

            try:
                payload = response.json()
            except ValueError as exc:
                raise InventoryResponseError(
                    "Inventory API returned invalid JSON."
                ) from exc

            return self._map_search_response(
                payload=payload,
                search=search,
            )

        except InventoryAuthenticationError:
            raise

        except InventoryResponseError:
            raise

        except httpx.TimeoutException as exc:
            logger.warning(
                "Inventory API request timed out: %s",
                exc.request.url,
            )

            raise InventoryUnavailableError(
                "The inventory provider timed out."
            ) from exc

        except httpx.RequestError as exc:
            logger.warning(
                "Inventory API request failed: %s",
                exc.request.url,
            )

            raise InventoryUnavailableError(
                "The inventory provider could not be reached."
            ) from exc

    @staticmethod
    def _build_search_params(
        search: InventorySearchRequest,
    ) -> dict[str, str | int]:
        """
        Convert BusNBox search fields to company API query parameters.

        Update these parameter names when the official company API
        documentation is available.
        """

        params: dict[str, str | int] = {
            "source": search.source,
            "destination": search.destination,
            "travel_date": search.travel_date.isoformat(),
            "minimum_seats": search.minimum_seats,
        }

        if search.bus_type:
            params["bus_type"] = search.bus_type

        if search.operator:
            params["operator"] = search.operator

        if search.maximum_price is not None:
            params["maximum_price"] = str(search.maximum_price)

        return params

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise InventoryAuthenticationError(
                "The inventory API rejected the configured credentials."
            )

        if response.status_code == 429:
            raise InventoryUnavailableError(
                "The inventory API rate limit was reached."
            )

        if 400 <= response.status_code < 500:
            raise InventoryResponseError(
                f"Inventory API rejected the request "
                f"with status {response.status_code}."
            )

        if response.status_code >= 500:
            raise InventoryUnavailableError(
                f"Inventory API failed with status "
                f"{response.status_code}."
            )

    @staticmethod
    def _map_search_response(
        *,
        payload: Any,
        search: InventorySearchRequest,
    ) -> InventorySearchResult:
        """
        Convert the company response into BusNBox's normalized format.

        For now, this expects the provider response to already follow the
        normalized InventorySearchResult schema. Replace this function's
        mapping logic after receiving the actual company response sample.
        """

        if not isinstance(payload, dict):
            raise InventoryResponseError(
                "Inventory API response must be a JSON object."
            )

        raw_trips = payload.get("trips", [])
        mapped_trips: list[dict[str, Any]] = []
        for trip in raw_trips:
            if not isinstance(trip, dict):
                continue
            if "operator" in trip and isinstance(trip["operator"], dict) and "bus" in trip and isinstance(trip["bus"], dict):
                mapped_trips.append(trip)
                continue

            operator_raw = trip.get("operator")
            if isinstance(operator_raw, dict):
                operator_dict = operator_raw
            else:
                operator_dict = {
                    "id": str(trip.get("operator_id", 1)),
                    "name": str(operator_raw or "Operator"),
                }

            bus_raw = trip.get("bus")
            if isinstance(bus_raw, dict):
                bus_dict = bus_raw
            else:
                bus_type = str(trip.get("bus_type", "Standard"))
                bus_dict = {
                    "id": str(trip.get("bus_id", 1)),
                    "name": bus_type,
                    "bus_type": bus_type,
                    "registration_number": trip.get("bus_number"),
                    "amenities": trip.get("amenities", []),
                    "total_seats": trip.get("total_seats"),
                }

            mapped_trips.append({
                "id": str(trip.get("trip_id") or trip.get("id")),
                "source": trip.get("source", search.source),
                "destination": trip.get("destination", search.destination),
                "departure_time": trip.get("departure_time"),
                "arrival_time": trip.get("arrival_time"),
                "operator": operator_dict,
                "bus": bus_dict,
                "price": trip.get("fare") if trip.get("fare") is not None else trip.get("price", 0),
                "available_seats": trip.get("available_seats", 0),
                "boarding_point": trip.get("boarding_point"),
                "dropping_point": trip.get("dropping_point"),
                "booking_url": trip.get("booking_url"),
            })

        total_results = payload.get("count", payload.get("total_results", len(mapped_trips)))
        normalized_payload = {
            **payload,
            "source": payload.get("source", search.source),
            "destination": payload.get(
                "destination",
                search.destination,
            ),
            "travel_date": payload.get(
                "travel_date",
                search.travel_date.isoformat(),
            ),
            "provider": "company",
            "total_results": total_results,
            "page": payload.get("page", search.page),
            "page_size": payload.get("page_size", search.page_size),
            "total_pages": payload.get("total_pages", 1 if total_results > 0 else 0),
            "trips": mapped_trips,
        }

        try:
            return InventorySearchResult.model_validate(
                normalized_payload
            )
        except ValidationError as exc:
            logger.warning(
                "Inventory response validation failed: %s",
                exc,
            )

            raise InventoryResponseError(
                "Inventory API returned an unexpected response format."
            ) from exc

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
