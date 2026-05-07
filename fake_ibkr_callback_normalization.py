from __future__ import annotations


OPEN_ORDER_STATUSES = {
    "apisent",
    "pendingcancel",
    "pendingsubmit",
    "presubmitted",
    "submitted",
}

TERMINAL_ORDER_STATUS_MAP = {
    "filled": "filled",
    "cancelled": "canceled",
    "canceled": "canceled",
    "inactive": "rejected",
    "rejected": "rejected",
}

NON_TERMINAL_ORDER_STATUS_MAP = {
    "apisent": "submitted",
    "pendingcancel": "submitted",
    "pendingsubmit": "submitted",
    "presubmitted": "submitted",
    "submitted": "submitted",
}


def normalize_order_status(broker_status: str) -> str:
    normalized = broker_status.lower()
    if normalized in TERMINAL_ORDER_STATUS_MAP:
        return TERMINAL_ORDER_STATUS_MAP[normalized]
    if normalized in NON_TERMINAL_ORDER_STATUS_MAP:
        return NON_TERMINAL_ORDER_STATUS_MAP[normalized]
    return normalized


def is_terminal_order_status(order_status: str) -> bool:
    return order_status in {"filled", "canceled", "rejected"}


def is_open_order_status(status: object) -> bool:
    return str(status).lower() in OPEN_ORDER_STATUSES


def optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def parse_int_qty(value: object) -> int:
    return int(float(str(value)))


def parse_buying_power(value: object) -> float:
    return float(value)
