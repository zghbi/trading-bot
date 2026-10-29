"""Synthetic component demonstration. No production imports or order transport."""

from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class DemoSignal:
    identifier: str
    label: str
    side: Side
    reference_price: Decimal


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    event: str
    signal_id: str
    detail: str


class PaperAccount:
    """In-memory teaching example; it has no real account or broker connection."""

    def __init__(self) -> None:
        self.position: DemoSignal | None = None
        self.audit: list[AuditEvent] = []

    def offer(self, signal: DemoSignal, sequence: int) -> None:
        if not signal.identifier or not signal.reference_price.is_finite() or signal.reference_price <= 0:
            raise ValueError("Invalid synthetic signal")
        if self.position is not None:
            self.audit.append(AuditEvent(sequence, "PAPER_BLOCKED", signal.identifier, "Synthetic account already occupied"))
            return
        self.position = signal
        self.audit.append(AuditEvent(sequence, "PAPER_ACCEPTED", signal.identifier, "Virtual position only; no order sent"))

    def close(self, identifier: str, sequence: int) -> None:
        if self.position is None or self.position.identifier != identifier:
            raise ValueError("Synthetic position mismatch")
        self.position = None
        self.audit.append(AuditEvent(sequence, "PAPER_CLOSED", identifier, "Explicit virtual event; no PnL calculated"))


def main() -> None:
    path = Path(__file__).parent / "examples" / "synthetic-scenario.json"
    scenario = json.loads(path.read_text(encoding="utf-8"))
    if scenario.get("data_origin") != "SYNTHETIC_ONLY":
        raise ValueError("This demonstration accepts its fixed synthetic fixture only")
    account = PaperAccount()
    last_sequence = 0
    for event in scenario["events"]:
        sequence = event["sequence"]
        if type(sequence) is not int or sequence <= last_sequence:
            raise ValueError("Synthetic events must be ordered")
        last_sequence = sequence
        if event["kind"] == "signal":
            signal = DemoSignal(event["id"], event["label"], Side(event["side"]), Decimal(event["reference_price"]))
            account.offer(signal, sequence)
        elif event["kind"] == "close":
            account.close(event["position_id"], sequence)
        else:
            raise ValueError("Unknown synthetic event")
    result = {
        "mode": "SYNTHETIC_DEMONSTRATION",
        "real_orders_sent": 0,
        "audit": [asdict(event) for event in account.audit],
        "virtual_position": account.position.identifier if account.position else None,
        "performance_claim": None,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
