"""Enables the Home Assistant test plugin when it is installed."""

try:
    import pytest_homeassistant_custom_component  # noqa: F401

    pytest_plugins = ["pytest_homeassistant_custom_component"]
except ImportError:  # core tests run without Home Assistant
    pass
