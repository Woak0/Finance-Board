import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field

@dataclass
class NetWorthSnapshot:
    net_position: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date_recorded: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "net_position": self.net_position,
            "date_recorded": self.date_recorded.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            net_position=data["net_position"],
            id=data["id"],
            date_recorded=datetime.fromisoformat(data["date_recorded"])
        )

class NetWorthManager:
    def __init__(self):
        self.snapshots: list[NetWorthSnapshot] = []

    def add_snapshot(self, net_position: float):
        snapshot = NetWorthSnapshot(net_position=net_position)
        self.snapshots.append(snapshot)
        print(f"Net worth snapshot of ${net_position:,.2f} recorded.")
        return snapshot

    def get_all_snapshots(self) -> list[NetWorthSnapshot]:
        return sorted(self.snapshots, key=lambda s: s.date_recorded, reverse=True)