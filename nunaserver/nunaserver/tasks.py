"""
Run Nunavut jobs as Celery background tasks
to allow for long-running jobs.
"""
# see issue https://github.com/celery/kombu/issues/1804
import functools
from threading import RLock
import kombu.utils

if not getattr(kombu.utils.cached_property, 'lock', None):
    setattr(kombu.utils.cached_property, 'lock', functools.cached_property(lambda _: RLock()))
    # Must call __set_name__ here since this cached property is not defined in the context of a class
    # Refer to https://docs.python.org/3/reference/datamodel.html#object.__set_name__
    kombu.utils.cached_property.lock.__set_name__(kombu.utils.cached_property, 'lock')

from celery import Celery, Task
from nunaserver import settings


def make_celery(name):
    """
    Create a Celery wrapper for use in running
    background tasks.
    """
    celery_inst = Celery(name, backend=settings.CELERY_RESULT_BACKEND, broker=settings.CELERY_BROKER_URL)

    return celery_inst


celery = make_celery("nunaserver")


def init_celery(celery_inst, app):
    """
    Initialize Celery instance with flask data.
    """
    celery_inst.conf.update(app.config)

    # pylint: disable=abstract-method
    class ContextTask(Task):
        """
        Task running with flask context.
        """

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_inst.Task = ContextTask
    return celery_inst
