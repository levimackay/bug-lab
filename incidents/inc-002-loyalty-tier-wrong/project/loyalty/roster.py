import csv
from pathlib import Path

from loyalty.models import Member


def load_members(path: str | Path) -> list[Member]:
    """Read a member roster export. Rows: member_id,name,points."""
    members: list[Member] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("member_id"):
                continue
            members.append(Member(row["member_id"], row["name"], int(row["points"])))
    return members
