class PunchError(Exception):
    """Raised by punch validation when a business rule is violated.

    The ``status_code`` maps directly to an HTTP response code:
    - 404: no open entry found
    - 409: employee already clocked in
    - 422: invalid timestamp (future or clock-out before clock-in)
    """

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)
