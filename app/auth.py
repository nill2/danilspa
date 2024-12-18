"""Process the authentication requests."""

from typing import Any, Callable, TypeVar, Union
from flask import Response, render_template, Blueprint

auth = Blueprint("auth", __name__)

ResponseReturnValue = Union[Response, str]

F = TypeVar("F", bound=Callable[..., ResponseReturnValue])


def route_decorator(path: str, **kwargs: Any) -> Callable[[F], F]:
    """Use a typed decorator for Flask routes."""

    def decorator(func: F) -> F:
        # Correctly return the decorated function
        return auth.route(path, **kwargs)(func)  # type: ignore

    return decorator


@route_decorator("/login", methods=["GET", "POST"])
def login() -> ResponseReturnValue:
    """Render the login page."""
    return render_template("login.html")


@route_decorator("/logout", methods=["GET", "POST"])
def logout() -> str:
    """Log the user out."""
    return "This is a stub for a logout"  # Replace with redirect(url_for('auth.login')) if needed.
