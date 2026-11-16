from core_domain.ddd import DomainError


class SignInFailed(DomainError):
    """Sign-in did not finish. The message is plain enough to show the operator as is."""


class SignInRequired(DomainError):
    """The call needs a signed-in operator and there is none, or their session has ended. The
    frontend matches this class's name to ask the operator to sign in, so keep it one class."""
