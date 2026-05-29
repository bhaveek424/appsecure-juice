class ReviewRunNotFoundError(Exception):
    pass


class ReviewRunNotReadyError(Exception):
    pass


class ReviewRunNotCancellableError(Exception):
    pass


class ReviewRunCancelledError(Exception):
    pass


class UnknownSkillError(Exception):
    pass
