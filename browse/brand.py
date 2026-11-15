"""Coauthored's site chrome: the shared <head> links, header and footer.

This replaces arXiv's ``arxiv_brand`` templates (from arXiv's design system), which
carry arXiv's name and logo; those are arXiv trademarks and are not ours to use. The
template variables keep the names arxiv_brand used, so the page templates that set
them (``hide_nav``, ``header_page_actions`` ...) work unchanged.

    browse.brand.init_app(app)                 # after the config is loaded
    {% include "coauthored_brand/header.html" %}

Values resolve from the defaults below, then the app config, then the render context.
"""
from typing import Any

from markupsafe import Markup

__all__ = ["init_app", "context", "DEFAULTS"]

# name -> (type, default). "html" values are marked safe; they must be trusted.
DEFAULTS: dict[str, tuple[str, Any]] = {
    "static_base": ("url", ""),
    "header_variant": ("attr", ""),
    "base_url": ("url", ""),
    "auth_url": ("url", ""),
    "submit_url": ("url", ""),
    "account_path": ("url", "/account"),
    "help_url": ("url", ""),
    "source_url": ("url", "https://github.com/coauthoredai/coauthored-browse"),
    "upstream_url": ("url", "https://github.com/arXiv/arxiv-browse"),
    "hide_nav": ("bool", False),
    "hide_announcement": ("bool", False),
    "signed_in": ("bool", False),
    "header_page_actions": ("html", ""),
}


def _value(kind: str, value: Any) -> Any:
    if kind == "bool":
        return bool(value)
    return Markup(value) if kind == "html" else value


def context(**values: Any) -> dict[str, Any]:
    """Per-request values as a template context. Unknown names raise TypeError."""
    unknown = sorted(set(values) - set(DEFAULTS))
    if unknown:
        raise TypeError(f"browse.brand.context(): unknown variable(s) {unknown}")
    return {k: _value(DEFAULTS[k][0], v) for k, v in values.items() if v is not None}


def config_values(config: Any, static_url_path: str) -> dict[str, Any]:
    """Site-wide values from the app config: BASE_SERVER, AUTH_SERVER, SUBMIT_SERVER and
    HELP_SERVER joined with EXTERNAL_URL_SCHEME (default https); the static base is the
    app's own static route, so nothing is loaded from another site."""
    get = config.get
    scheme = get("EXTERNAL_URL_SCHEME") or "https"
    hosts = {"base_url": get("BASE_SERVER"), "auth_url": get("AUTH_SERVER") or get("BASE_SERVER"),
             "submit_url": get("SUBMIT_SERVER") or get("BASE_SERVER"),
             "help_url": get("HELP_SERVER") or get("BASE_SERVER")}
    out: dict[str, Any] = {k: f"{scheme}://{h}" for k, h in hosts.items() if h}
    out["static_base"] = static_url_path.rstrip("/") + "/"
    if get("COAUTHORED_SOURCE_URL"):
        out["source_url"] = get("COAUTHORED_SOURCE_URL")
    return out


def init_app(app: Any, **values: Any) -> Any:
    """Set the defaults, then the config values, then ``values`` as Jinja globals."""
    env = app.jinja_env
    for name, (kind, default) in DEFAULTS.items():
        env.globals.setdefault(name, _value(kind, default))
    env.globals.update(context(**{**config_values(app.config, app.static_url_path or "/static"), **values}))
    return app
