"""Database configuration supports both a URL and individual environment fields."""
import importlib
import os
from unittest import TestCase
from unittest.mock import patch
from service import config


class TestConfiguration(TestCase):
    """Check database configuration in CI and in the development environment."""

    def tearDown(self):
        importlib.reload(config)

    def test_explicit_database_url(self):
        """A complete database URL takes precedence over component defaults."""
        uri = "postgresql://example:example@db:5432/accounts"
        with patch.dict(os.environ, {"DATABASE_URI": uri}, clear=True):
            importlib.reload(config)
            self.assertEqual(config.SQLALCHEMY_DATABASE_URI, uri)

    def test_database_components(self):
        """Build the URL from individually supplied connection settings."""
        with patch.dict(os.environ, {
            "DATABASE_USER": "example", "DATABASE_PASSWORD": "test-only",
            "DATABASE_HOST": "database", "DATABASE_NAME": "accounts"
        }, clear=True):
            importlib.reload(config)
            self.assertEqual(
                config.SQLALCHEMY_DATABASE_URI,
                "postgresql://example:test-only@database:5432/accounts"
            )
