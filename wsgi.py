"""WSGI entrypoint for Gunicorn / DigitalOcean App Platform."""

from app import app as application  # noqa: F401
