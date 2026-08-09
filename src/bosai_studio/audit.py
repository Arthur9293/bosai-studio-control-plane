from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    sequence: int
    event_type: str
    payload: dict[str, Any]
    previous_event_hash: str
    payload_digest: str
    event_hash: str


class AuditTrail:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    @staticmethod
    def _canonical(payload: dict[str, Any]) -> bytes:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")

    def append(self, event_type: str, payload: dict[str, Any]) -> AuditEvent:
        sequence = len(self._events) + 1
        previous = self._events[-1].event_hash if self._events else "GENESIS"
        payload_digest = sha256(self._canonical(payload)).hexdigest()
        material = {
            "sequence": sequence,
            "event_type": event_type,
            "payload_digest": payload_digest,
            "previous_event_hash": previous,
        }
        event_hash = sha256(self._canonical(material)).hexdigest()
        event = AuditEvent(
            event_id=f"audit-{sequence:04d}",
            sequence=sequence,
            event_type=event_type,
            payload=dict(payload),
            previous_event_hash=previous,
            payload_digest=payload_digest,
            event_hash=event_hash,
        )
        self._events.append(event)
        return event

    def verify(self) -> bool:
        previous = "GENESIS"
        for index, event in enumerate(self._events, start=1):
            if event.sequence != index or event.previous_event_hash != previous:
                return False
            if sha256(self._canonical(event.payload)).hexdigest() != event.payload_digest:
                return False
            material = {
                "sequence": event.sequence,
                "event_type": event.event_type,
                "payload_digest": event.payload_digest,
                "previous_event_hash": event.previous_event_hash,
            }
            if sha256(self._canonical(material)).hexdigest() != event.event_hash:
                return False
            previous = event.event_hash
        return True
