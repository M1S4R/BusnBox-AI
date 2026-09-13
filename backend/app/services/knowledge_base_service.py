import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class KnowledgeDocument:
    id: str
    title: str
    category: str
    content: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeMatch:
    document_id: str
    title: str
    category: str
    content: str
    score: float
    matched_terms: tuple[str, ...]
    matched_keywords: tuple[str, ...]


class KnowledgeBaseService:
    def __init__(
        self,
        data_path: Path | None = None,
    ) -> None:
        self._data_path = (
            data_path
            or self._default_data_path()
        )

        self._documents = self._load_documents(
            self._data_path
        )

        self._stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "can",
            "do",
            "does",
            "for",
            "from",
            "how",
            "i",
            "in",
            "is",
            "it",
            "me",
            "my",
            "of",
            "on",
            "or",
            "the",
            "to",
            "what",
            "when",
            "where",
            "which",
            "will",
            "with",
        }

    def search(
        self,
        query: str,
        limit: int = 3,
        minimum_score: float = 0.15,
    ) -> list[KnowledgeMatch]:
        if limit <= 0:
            return []

        normalized_query = self._normalize_text(
            query
        )

        query_terms = self._extract_terms(
            normalized_query
        )

        if not query_terms:
            return []

        matches: list[KnowledgeMatch] = []

        for document in self._documents:
            match = self._score_document(
                document=document,
                normalized_query=normalized_query,
                query_terms=query_terms,
            )

            if (
                match is not None
                and match.score >= minimum_score
            ):
                matches.append(match)

        matches.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return matches[:limit]

    def get_document(
        self,
        document_id: str,
    ) -> KnowledgeDocument | None:
        for document in self._documents:
            if document.id == document_id:
                return document

        return None

    def get_all_documents(
        self,
    ) -> tuple[KnowledgeDocument, ...]:
        return self._documents

    def build_context(
        self,
        matches: list[KnowledgeMatch],
    ) -> str:
        if not matches:
            return ""

        sections: list[str] = []

        for index, match in enumerate(
            matches,
            start=1,
        ):
            section = (
                f"[Document {index}]\n"
                f"Title: {match.title}\n"
                f"Category: {match.category}\n"
                f"Content: {match.content}"
            )

            sections.append(section)

        return "\n\n".join(sections)

    def _score_document(
        self,
        document: KnowledgeDocument,
        normalized_query: str,
        query_terms: set[str],
    ) -> KnowledgeMatch | None:
        normalized_title = self._normalize_text(
            document.title
        )

        normalized_content = self._normalize_text(
            document.content
        )

        normalized_category = self._normalize_text(
            document.category
        )

        title_terms = self._extract_terms(
            normalized_title
        )

        content_terms = self._extract_terms(
            normalized_content
        )

        category_terms = self._extract_terms(
            normalized_category
        )

        document_terms = (
            title_terms
            | content_terms
            | category_terms
        )

        matched_terms = (
            query_terms
            & document_terms
        )

        matched_keywords = tuple(
            keyword
            for keyword in document.keywords
            if self._keyword_matches(
                keyword=keyword,
                normalized_query=(
                    normalized_query
                ),
                query_terms=query_terms,
            )
        )

        if not matched_terms and not matched_keywords:
            return None

        term_recall = (
            len(matched_terms)
            / max(len(query_terms), 1)
        )

        title_overlap = (
            len(query_terms & title_terms)
            / max(len(query_terms), 1)
        )

        category_overlap = (
            len(query_terms & category_terms)
            / max(len(query_terms), 1)
        )

        keyword_score = min(
            len(matched_keywords) / 2,
            1.0,
        )

        phrase_bonus = 0.0

        for keyword in matched_keywords:
            normalized_keyword = (
                self._normalize_text(keyword)
            )

            if (
                " " in normalized_keyword
                and normalized_keyword
                in normalized_query
            ):
                phrase_bonus += 0.10

        score = (
            term_recall * 0.45
            + title_overlap * 0.20
            + category_overlap * 0.10
            + keyword_score * 0.25
            + phrase_bonus
        )

        return KnowledgeMatch(
            document_id=document.id,
            title=document.title,
            category=document.category,
            content=document.content,
            score=round(
                min(score, 1.0),
                4,
            ),
            matched_terms=tuple(
                sorted(matched_terms)
            ),
            matched_keywords=matched_keywords,
        )

    def _keyword_matches(
        self,
        keyword: str,
        normalized_query: str,
        query_terms: set[str],
    ) -> bool:
        normalized_keyword = self._normalize_text(
            keyword
        )

        keyword_terms = self._extract_terms(
            normalized_keyword
        )

        if not keyword_terms:
            return False

        if normalized_keyword in normalized_query:
            return True

        return keyword_terms.issubset(
            query_terms
        )

    def _extract_terms(
        self,
        normalized_text: str,
    ) -> set[str]:
        return {
            token
            for token in normalized_text.split()
            if (
                token
                and token not in self._stop_words
                and len(token) > 1
            )
        }

    def _normalize_text(
        self,
        value: str,
    ) -> str:
        lowered = value.casefold().strip()

        cleaned = re.sub(
            r"[^a-z0-9\s]",
            " ",
            lowered,
        )

        return re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

    def _default_data_path(self) -> Path:
        return (
            Path(__file__).resolve().parents[1]
            / "data"
            / "knowledge_base.json"
        )

    def _load_documents(
        self,
        data_path: Path,
    ) -> tuple[KnowledgeDocument, ...]:
        if not data_path.exists():
            raise FileNotFoundError(
                "Knowledge base data file "
                f"not found: {data_path}"
            )

        raw_content = data_path.read_text(
            encoding="utf-8"
        )

        parsed_data: Any = json.loads(
            raw_content
        )

        if not isinstance(parsed_data, list):
            raise ValueError(
                "Knowledge base JSON must "
                "contain a list."
            )

        documents: list[KnowledgeDocument] = []
        document_ids: set[str] = set()

        for item in parsed_data:
            if not isinstance(item, dict):
                raise ValueError(
                    "Each knowledge base entry "
                    "must be an object."
                )

            document_id = str(
                item.get("id", "")
            ).strip()

            title = str(
                item.get("title", "")
            ).strip()

            category = str(
                item.get("category", "")
            ).strip()

            content = str(
                item.get("content", "")
            ).strip()

            raw_keywords = item.get(
                "keywords",
                [],
            )

            if not document_id:
                raise ValueError(
                    "Knowledge document id "
                    "cannot be empty."
                )

            if document_id in document_ids:
                raise ValueError(
                    "Duplicate knowledge document "
                    f"id: {document_id}"
                )

            if not title:
                raise ValueError(
                    f"Document {document_id} "
                    "must have a title."
                )

            if not category:
                raise ValueError(
                    f"Document {document_id} "
                    "must have a category."
                )

            if not content:
                raise ValueError(
                    f"Document {document_id} "
                    "must have content."
                )

            if not isinstance(raw_keywords, list):
                raise ValueError(
                    f"Document {document_id} "
                    "keywords must be a list."
                )

            keywords = tuple(
                str(keyword).strip()
                for keyword in raw_keywords
                if str(keyword).strip()
            )

            documents.append(
                KnowledgeDocument(
                    id=document_id,
                    title=title,
                    category=category,
                    content=content,
                    keywords=keywords,
                )
            )

            document_ids.add(document_id)

        return tuple(documents)


knowledge_base_service = KnowledgeBaseService()
