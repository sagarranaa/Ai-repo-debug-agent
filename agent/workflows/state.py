from typing import TypedDict


class RepairState(TypedDict, total=False):
    proposal: dict
    approved: bool
    status: str
    backup_file: str
    test_result: dict