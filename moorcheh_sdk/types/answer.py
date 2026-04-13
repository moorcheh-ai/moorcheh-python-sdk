from typing import TypedDict


class ChatHistoryItem(TypedDict):
    role: str
    content: str


class AnswerResponse(TypedDict):
    answer: str
    model: str
    context_count: int
    query: str
    used_context: bool | None
    structured_data: dict | None
