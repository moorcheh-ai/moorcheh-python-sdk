from typing import TypedDict


class ChatHistoryItem(TypedDict):
    role: str
    content: str


class AnswerResponse(TypedDict):
    answer: str
    model: str
    contextCount: int
    query: str
    usedContext: bool | None
    structuredData: dict | None
