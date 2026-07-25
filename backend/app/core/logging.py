"""Logging configuration."""

from logging.config import dictConfig


def configure_logging(level: str = "INFO") -> None:
    """Configure application and Uvicorn logs with one consistent format."""

    normalized_level = level.upper()
    # One shared dictConfig keeps application, access, and error logs aligned
    # without relying on framework defaults.
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": ("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": normalized_level,
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": normalized_level,
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["console"],
                    "level": normalized_level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": normalized_level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": normalized_level,
                    "propagate": False,
                },
            },
        }
    )
