class DomainError(Exception):
    message = "The request could not be completed."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class EventNotFoundError(DomainError):
    message = "Event not found."


class RegistrationNotFoundError(DomainError):
    message = "This email is not registered for the event."


class EventInPastError(DomainError):
    message = "This event has already started and can no longer be changed."


class EventFullError(DomainError):
    message = "This event is full."


class AlreadyRegisteredError(DomainError):
    message = "This email is already registered for the event."


class CapacityBelowRegistrationsError(DomainError):
    def __init__(self, registered_count: int) -> None:
        # Always plural: this only fires when 1 <= max_capacity < registered_count.
        super().__init__(
            f"Max capacity cannot be lower than the current {registered_count} registrations."
        )


class StartTimeInPastError(DomainError):
    message = "The event start time must be in the future."
