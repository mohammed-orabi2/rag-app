from typing import Literal, Annotated, List, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class State(TypedDict):
    query: str
    messages: List[str]
    query_type: str | None
    content: List[str] | None
    response: str | None
    rewritten_query: str | None
    program_type: List | None
    excluded_ids: List[str]
    question_category: str | None
    dynamic_k: int | None
    retriever_intent: str | None
    price_campus_info: dict | None
    suggestion: str | None
    entry_level: List[str] | None
    rules_prompt: str | None
    response_type: (
        str | None
    )  # response type field (used as a flag) for tracking response type


class QueryClassifier(BaseModel):
    is_program_selection: Literal[True, False] = Field(
        ..., description="binary classifier for programs"
    )


class FiveWayQueryClassifier(BaseModel):
    question_category: Literal["program_selection", "rules", "follow_up", "general"] = (
        Field(
            ...,
            description="Classify query into program selection, rules explanation, follow-up for missing info, general question",
        )
    )

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"

    def __reduce__(self):
        return (self.__class__, (self.question_category,))

    def dict(self, **kwargs):
        return {"question_category": self.question_category}


class ProgramExtractionOutput(BaseModel):
    program_type: List[
        Literal[
            "MSc",
            "PGE",
            "BTS",
            "BBA",
            "MIM",
            "MBA",
            "Other",
            "Master",
            "Mastère",
            "Bachelor",
            "Cycle prépa",
            "Cycle d'Ingénieur",
            "Cycle Préparatoire",
            "Mastère Spécialisé®",
            "Programme d'Ingénieur",
        ]
    ] = Field(
        default=[
            "MSc",
            "PGE",
            "BTS",
            "BBA",
            "MIM",
            "MBA",
            "Other",
            "Master",
            "Mastère",
            "Bachelor",
            "Cycle prépa",
            "Cycle d'Ingénieur",
            "Cycle Préparatoire",
            "Mastère Spécialisé®",
            "Programme d'Ingénieur",
        ],
        description="List of program types",
    )

class ProgramExtractionOutputV2(BaseModel):
    program_type: List[
        Literal[
            "PGE",
            "BTS",
            "BBA",
            "MIM",
            "MBA",
            "Other",
            "Bachelor",
            "Cycle prépa",
            "Cycle d'Ingénieur",
            "Cycle Préparatoire",
            "Programme d'Ingénieur",
            "Master"
        ]
    ] = Field(
        default=[
            "PGE",
            "BTS",
            "BBA",
            "MIM",
            "MBA",
            "Other",
            "Bachelor",
            "Cycle prépa",
            "Cycle d'Ingénieur",
            "Cycle Préparatoire",
            "Programme d'Ingénieur",
            "Master"
        ],
        description="List of program types",
    )

class RetrieverIntentOutput(BaseModel):
    retriever_intent: Literal["REPEAT", "NEW"] = Field(
        ..., description="Intent for the retriever: REPEAT or NEW"
    )


class DocumentMatchResponse(BaseModel):
    matched_ids: list[int] = Field(
        ..., description="List of document IDs that match the query"
    )


class PriceCampusExtraction(BaseModel):
    price: Optional[int] = Field(
        default=None, description="price in euros, null if not mentioned"
    )
    price_condition: Optional[str] = Field(
        default=None, description="one of 'gt', 'lte', or null"
    )
    languages: List[str] | None = Field(    
        default=None, description="language of instruction, null if not mentioned"
    )
    primos_arrivant: bool | None = Field(
        default=None,
        description="True if primos_arrivant is mentioned, False otherwise",
    )
    school_rank: Optional[int] = Field(
        default=None, description="maximum school rank, null if not mentioned"
    )


class TopProgramIDs(BaseModel):
    """Top ranked program IDs after re-ranking"""

    top_ids: List[str] = Field(
        ..., description="List of program IDs ranked by relevance (most relevant first)"
    )

class EntryLevelPromptOutput(BaseModel):
    """Entry level prompt output"""

    entry_level: List[str] = Field(
        ..., description="Entry level information extracted from the query"
    )