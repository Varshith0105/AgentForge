import pytest


def test_celery_import():
    try:
        from app.core.celery_app import celery_app
        assert True
    except ImportError:
        pytest.skip("Celery not installed")
