# Inventory Adapter & Integration Guide

BusNBox AI searches travel availability through an **abstract inventory provider interface**.

It does **NOT** require direct access to your company's SQL database.

---

## 1. Architecture

```text
BusNBox AI
    │
    ▼ (Internal Service Call)
InventoryService
    │
    ▼ (create_inventory_provider())
┌─────────────────────────────────┐
│     InventoryProvider (Base)    │
└────────────────┬────────────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
MockProvider         CompanyInventoryProvider
(In-Memory / Dev)    (HTTP REST Client)
                            │
                            ▼
                     Company Inventory API
```

---

## 2. Configuration

Set the provider in `.env` or container environment:

### Local Development / Mock Testing
```env
INVENTORY_PROVIDER=mock
```
*Runs completely in-memory. Zero external database or mock container required.*

### Company Production API
```env
INVENTORY_PROVIDER=company
INVENTORY_API_BASE_URL=https://inventory.yourcompany.com
INVENTORY_API_SEARCH_PATH=/api/trips/search
INVENTORY_API_KEY=your_private_api_key
INVENTORY_API_KEY_HEADER=X-API-Key
INVENTORY_API_TIMEOUT_SECONDS=15
```

---

## 3. Inventory Contract

### Search Request (Sent by BusNBox)
```json
{
  "source": "Chennai",
  "destination": "Bangalore",
  "travel_date": "2026-09-15",
  "operator": "Kaveri Travels",
  "bus_type": "AC",
  "maximum_price": 800.0,
  "minimum_seats": 1,
  "departure_time": "18:00",
  "page": 1,
  "page_size": 50
}
```

### Search Response (Expected from Company API)
```json
{
  "trips": [
    {
      "id": "TRIP-1029",
      "source": "Chennai",
      "destination": "Bangalore",
      "departure_time": "2026-09-15T21:30:00",
      "arrival_time": "2026-09-16T04:00:00",
      "operator": {
        "id": "OP-1",
        "name": "Kaveri Travels"
      },
      "bus": {
        "id": "BUS-1",
        "name": "Kaveri Premium",
        "bus_type": "AC Sleeper",
        "registration_number": "KA-05-KV-4004",
        "amenities": ["Charging Point", "WiFi", "Blanket"],
        "total_seats": 36
      },
      "price": "750.00",
      "available_seats": 12,
      "boarding_point": "Koyambedu",
      "dropping_point": "Madiwala",
      "booking_url": null
    }
  ]
}
```

---

## 4. Customizing the Adapter

If your company's existing inventory endpoint uses different field names (e.g. `origin` instead of `source`, or `fare` instead of `price`), customize only the serialization/deserialization methods in:

[`backend/app/integrations/inventory/company.py`](../backend/app/integrations/inventory/company.py)

BusNBox's NLP, Gemini, and conversational state layers remain completely unaffected.
