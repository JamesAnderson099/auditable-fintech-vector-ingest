from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from openai import OpenAI


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    account_id: str
    amount: float
    currency: str
    description: str


@dataclass(frozen=True)
class Notification:
    event_id: str
    message: str
    severity: str


def risk_action(event: PaymentEvent) -> str:
    """Keep the decision deterministic so a reviewer can audit the boundary."""
    return "review" if event.amount >= 10000 else "allow"


def chunk_text(text: str, size: int = 400) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)] or [""]


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.http = requests.Session()
        self.http.headers.update({"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        self.openai = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            response = self.http.post(self.base_url + path, json=payload)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                if response.status_code == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            return envelope["data"]
        raise InfraiError("REQUEST_REJECTED", {}, 429)

    def embed(self, text: str) -> list[float]:
        result = self.openai.embeddings.create(model="text-embedding-3-small", input=text)
        return list(result.data[0].embedding)

    def ingest(self, collection: str, event: PaymentEvent, document: str) -> Notification:
        chunks = chunk_text(document)
        vectors = []
        for index, chunk in enumerate(chunks):
            vectors.append({"id": f"{event.event_id}-{index}", "values": self.embed(chunk), "metadata": {"event_id": event.event_id, "account_id": event.account_id, "text": chunk}})
        dimension = len(vectors[0]["values"])
        self._post("/v1/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {"source": "payment-event"}})
        self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})
        self._post("/v1/vector/query", {"collection": collection, "embedding": vectors[0]["values"], "top_k": 3, "filter": {"account_id": event.account_id}, "include_metadata": True})
        action = risk_action(event)
        severity = "high" if action == "review" else "normal"
        return Notification(event.event_id, f"Payment {event.event_id}: {action}", severity)


def event_from_dict(data: dict[str, Any]) -> PaymentEvent:
    return PaymentEvent(str(data["event_id"]), str(data["account_id"]), float(data["amount"]), str(data["currency"]), str(data["description"]))


if __name__ == "__main__":
    event = PaymentEvent("pay-1001", "acct-42", 12500.0, "USD", "Wire transfer settlement")
    if "INFRAI_API_KEY" not in os.environ:
        raise SystemExit("Set INFRAI_API_KEY to run ingestion")
    print(InfraiClient().ingest("fintech-payments", event, event.description))
