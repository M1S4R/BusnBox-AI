import re
from dataclasses import dataclass
from typing import Final


@dataclass
class ExtractedRoute:
    source: str | None = None
    destination: str | None = None
    is_correction: bool = False


KNOWN_CITIES: Final[set[str]] = {
    "chennai",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "coimbatore",
    "mysore",
    "mysuru",
    "mumbai",
    "pune",
    "delhi",
    "jaipur",
    "goa",
    "kochi",
    "madurai",
    "tirupati",
    "vijayawada",
    "trichy",
    "salem",
    "pondicherry",
}

CITY_TYPO_MAP: Final[dict[str, str]] = {
    "bangaluru": "Bengaluru",
    "banglore": "Bangalore",
    "bengaluru": "Bengaluru",
    "bangalore": "Bangalore",
    "chennaii": "Chennai",
    "chennai": "Chennai",
    "madras": "Chennai",
    "hydrabad": "Hyderabad",
    "hyderabad": "Hyderabad",
    "coimbator": "Coimbatore",
    "coimbatore": "Coimbatore",
    "mysur": "Mysore",
    "mysuru": "Mysuru",
    "mysore": "Mysore",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "poona": "Pune",
    "pune": "Pune",
    "delhi": "Delhi",
    "jaipur": "Jaipur",
    "goa": "Goa",
    "kochi": "Kochi",
    "madurai": "Madurai",
    "tirupati": "Tirupati",
    "vijayawada": "Vijayawada",
    "trichy": "Trichy",
    "salem": "Salem",
    "pondicherry": "Pondicherry",
}

NON_CITY_STOPWORDS: Final[set[str]] = {
    "bus",
    "buses",
    "ac",
    "non",
    "volvo",
    "today",
    "tomorrow",
    "cheap",
    "cheapest",
    "fastest",
    "earliest",
    "latest",
    "ticket",
    "tickets",
    "book",
    "booking",
    "find",
    "search",
    "show",
    "need",
    "want",
    "travel",
    "travelling",
    "journey",
    "trip",
    "trips",
    "go",
    "going",
    "gone",
    "get",
    "take",
    "like",
    "reach",
    "me",
    "a",
    "an",
    "the",
    "for",
    "on",
    "at",
    "by",
    "in",
    "and",
    "or",
    "is",
    "are",
    "can",
    "you",
    "please",
    "filter",
    "filters",
    "price",
    "seat",
    "seats",
    "sleeper",
    "seater",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "weekend",
    "here",
    "there",
    "where",
    "some",
    "any",
    "good",
    "option",
    "options",
    "available",
    "instead",
    "actually",
    "sorry",
    "destination",
    "source",
}


class RouteService:
    @staticmethod
    def normalize_city(name: str | None) -> str | None:
        if not name:
            return None

        cleaned = name.strip().lower()
        if not cleaned or cleaned in NON_CITY_STOPWORDS:
            return None

        # Check typo and alias dictionary first
        if cleaned in CITY_TYPO_MAP:
            return CITY_TYPO_MAP[cleaned]

        # Return title-cased location
        return cleaned.title()

    def is_known_or_plausible_city(self, name: str | None) -> bool:
        if not name:
            return False
        cleaned = name.strip().lower()
        if cleaned in NON_CITY_STOPWORDS:
            return False
        if cleaned in CITY_TYPO_MAP or cleaned in KNOWN_CITIES:
            return True
        # Plausible city name: alphabetic and 3-25 chars
        return len(cleaned) >= 3 and cleaned.isalpha()

    def extract_route(
        self,
        message: str,
        current_source: str | None = None,
        current_destination: str | None = None,
    ) -> ExtractedRoute:
        if not message:
            return ExtractedRoute()

        text = " ".join(message.strip().split())
        normalized = text.lower()

        # -------------------------------------------------------------
        # 1. Corrections
        # -------------------------------------------------------------
        # "Actually Bangalore to Chennai" or "Actually Chennai to Bangalore"
        match = re.search(
            r"\b(?:actually|wait,?|no,?)\s+(?:from\s+)?([a-zA-Z]+)\s+to\s+([a-zA-Z]+)\b",
            normalized,
        )
        if match:
            src = self.normalize_city(match.group(1))
            dest = self.normalize_city(match.group(2))
            if src and dest:
                return ExtractedRoute(source=src, destination=dest, is_correction=True)

        # "Change Bangalore to Coimbatore" -> if current_source == Bangalore, change source;
        # if current_destination == Bangalore or neither, check matches
        match = re.search(
            r"\bchange\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)\b",
            normalized,
        )
        if match:
            old_city = self.normalize_city(match.group(1))
            new_city = self.normalize_city(match.group(2))
            if old_city and new_city:
                if current_source and current_source.casefold() == old_city.casefold():
                    return ExtractedRoute(source=new_city, destination=current_destination, is_correction=True)
                if current_destination and current_destination.casefold() == old_city.casefold():
                    return ExtractedRoute(source=current_source, destination=new_city, is_correction=True)
                # Default: change destination to new_city
                return ExtractedRoute(destination=new_city, is_correction=True)

        # "Change destination to Hyderabad" / "Sorry, destination is Hyderabad" / "Destination is Hyderabad"
        match = re.search(
            r"\b(?:sorry,?\s+)?(?:change\s+)?destination\s+(?:is\s+|to\s+)?([a-zA-Z]+)\b",
            normalized,
        )
        if match:
            dest = self.normalize_city(match.group(1))
            if dest:
                return ExtractedRoute(source=current_source, destination=dest, is_correction=True)

        # "Change source to Chennai" / "Sorry, source is Chennai" / "Source is Chennai"
        match = re.search(
            r"\b(?:sorry,?\s+)?(?:change\s+)?source\s+(?:is\s+|to\s+)?([a-zA-Z]+)\b",
            normalized,
        )
        if match:
            src = self.normalize_city(match.group(1))
            if src:
                return ExtractedRoute(source=src, destination=current_destination, is_correction=True)

        # -------------------------------------------------------------
        # 2. Standard Route: "from Chennai to Bangalore", "bus from Chennai to Bangalore"
        # -------------------------------------------------------------
        match = re.search(
            r"\bfrom\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)\b",
            normalized,
        )
        if match:
            src = self.normalize_city(match.group(1))
            dest = self.normalize_city(match.group(2))
            if src and dest:
                return ExtractedRoute(source=src, destination=dest)

        # -------------------------------------------------------------
        # 3. Inverted Route: "to Bangalore from Chennai", "buses to Bangalore from Chennai"
        # -------------------------------------------------------------
        match = re.search(
            r"\b(?:buses?\s+)?to\s+([a-zA-Z]+)\s+from\s+([a-zA-Z]+)\b",
            normalized,
        )
        if match:
            dest = self.normalize_city(match.group(1))
            src = self.normalize_city(match.group(2))
            if src and dest:
                return ExtractedRoute(source=src, destination=dest)

        # -------------------------------------------------------------
        # 4. Arrow or Dash notation: "Chennai → Bangalore", "Chennai -> Bangalore", "Chennai - Bangalore"
        # -------------------------------------------------------------
        match = re.search(
            r"\b([a-zA-Z]+)\s*(?:->|→|-)\s*([a-zA-Z]+)\b",
            text,
        )
        if match:
            src = self.normalize_city(match.group(1))
            dest = self.normalize_city(match.group(2))
            if src and dest:
                return ExtractedRoute(source=src, destination=dest)

        # -------------------------------------------------------------
        # 5. Direct "X to Y": "Chennai to Bangalore", "buses Chennai to Bangalore"
        # -------------------------------------------------------------
        match = re.search(
            r"\b([a-zA-Z]+)\s+to\s+([a-zA-Z]+)\b",
            normalized,
        )
        if match:
            c1 = match.group(1)
            c2 = match.group(2)
            if self.is_known_or_plausible_city(c1) and self.is_known_or_plausible_city(c2):
                src = self.normalize_city(c1)
                dest = self.normalize_city(c2)
                if src and dest:
                    return ExtractedRoute(source=src, destination=dest)

        # -------------------------------------------------------------
        # 6. City pair bus notation: "Chennai Bangalore bus", "Chennai Bangalore buses"
        # -------------------------------------------------------------
        match = re.search(
            r"\b([a-zA-Z]+)\s+([a-zA-Z]+)\s+bus(?:es)?\b",
            normalized,
        )
        if match:
            c1 = match.group(1)
            c2 = match.group(2)
            # Require at least one to be a known city/typo to prevent matching "red sleeper bus"
            if (c1 in CITY_TYPO_MAP or c1 in KNOWN_CITIES) and self.is_known_or_plausible_city(c2):
                src = self.normalize_city(c1)
                dest = self.normalize_city(c2)
                if src and dest:
                    return ExtractedRoute(source=src, destination=dest)

        # -------------------------------------------------------------
        # 7. Single endpoint mentions:
        # "From Chennai", "leaving from Chennai", "travel from Chennai"
        # "To Bangalore", "going to Bangalore", "go to Bangalore"
        # -------------------------------------------------------------
        for m in re.finditer(
            r"\b(?:from|leaving\s+from|departing\s+from|travel\s+from|source\s+is)\s+([a-zA-Z]+)\b",
            normalized,
        ):
            src = self.normalize_city(m.group(1))
            if src:
                return ExtractedRoute(source=src)

        for m in re.finditer(
            r"\b(?:to|going\s+to|go\s+to|travel\s+to|destination\s+is)\s+([a-zA-Z]+)\b",
            normalized,
        ):
            dest = self.normalize_city(m.group(1))
            if dest:
                return ExtractedRoute(destination=dest)

        return ExtractedRoute()


route_service = RouteService()
