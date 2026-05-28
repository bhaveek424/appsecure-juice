from enum import StrEnum


class ReviewRunStatus(StrEnum):
    QUEUED = "Queued"
    ZAPPING = "Zapping"
    TRIAGING = "Triaging"
    READY_FOR_SKILLS = "Ready For Skills"
    PROBING = "Probing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

    @classmethod
    def active_statuses(cls) -> frozenset["ReviewRunStatus"]:
        return frozenset(
            {
                cls.QUEUED,
                cls.ZAPPING,
                cls.TRIAGING,
                cls.READY_FOR_SKILLS,
                cls.PROBING,
            }
        )

    @property
    def is_active(self) -> bool:
        return self in self.active_statuses()
