from sqlalchemy.orm import configure_mappers

from app.database.base import Base
from app.models import Bus, City, Operator, Route, Trip


def test_expected_tables_are_registered() -> None:
    expected_tables = {
        "cities",
        "operators",
        "buses",
        "routes",
        "trips",
    }

    assert set(Base.metadata.tables.keys()) == expected_tables


def test_orm_mappers_configure_successfully() -> None:
    configure_mappers()


def test_model_table_names() -> None:
    assert City.__tablename__ == "cities"
    assert Operator.__tablename__ == "operators"
    assert Bus.__tablename__ == "buses"
    assert Route.__tablename__ == "routes"
    assert Trip.__tablename__ == "trips"


def test_route_foreign_keys() -> None:
    source_foreign_keys = {
        str(foreign_key.column)
        for foreign_key in Route.__table__.c.source_city_id.foreign_keys
    }

    destination_foreign_keys = {
        str(foreign_key.column)
        for foreign_key in Route.__table__.c.destination_city_id.foreign_keys
    }

    assert source_foreign_keys == {"cities.id"}
    assert destination_foreign_keys == {"cities.id"}


def test_trip_foreign_keys() -> None:
    route_foreign_keys = {
        str(foreign_key.column)
        for foreign_key in Trip.__table__.c.route_id.foreign_keys
    }

    bus_foreign_keys = {
        str(foreign_key.column)
        for foreign_key in Trip.__table__.c.bus_id.foreign_keys
    }

    assert route_foreign_keys == {"routes.id"}
    assert bus_foreign_keys == {"buses.id"}
