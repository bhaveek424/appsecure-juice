from datetime import UTC, datetime

_MONTHS = (
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
)

_Z85_CHARSET = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~"
)


def _to_mmmyy(when: datetime) -> str:
    return _MONTHS[when.month - 1] + str(when.year)[-2:]


def z85_encode(raw: bytes) -> str:
    if len(raw) % 4:
        raw += b"\0" * (4 - len(raw) % 4)
    encoded: list[str] = []
    for offset in range(0, len(raw), 4):
        value = int.from_bytes(raw[offset : offset + 4], "big")
        block = [0] * 5
        for index in range(4, -1, -1):
            block[index] = value % 85
            value //= 85
        encoded.extend(_Z85_CHARSET[char] for char in block)
    return "".join(encoded)


def juice_shop_monthly_coupon(
    discount: int = 10,
    *,
    when: datetime | None = None,
) -> str:
    """Build a current-month Juice Shop coupon without brute forcing codes."""
    moment = when or datetime.now(UTC)
    payload = f"{_to_mmmyy(moment)}-{discount}"
    return z85_encode(payload.encode("ascii"))
