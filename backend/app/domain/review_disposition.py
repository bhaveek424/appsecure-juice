from enum import StrEnum


class ReviewDisposition(StrEnum):
    UNREVIEWED = "Unreviewed"
    TRUE_POSITIVE = "True Positive"
    FALSE_POSITIVE = "False Positive"
    DUPLICATE = "Duplicate"
    NEEDS_INVESTIGATION = "Needs Investigation"

    @classmethod
    def values(cls) -> frozenset[str]:
        return frozenset(member.value for member in cls)
