"""
Run Nunavut jobs as Celery background tasks
to allow for long-running jobs.
"""
from nunaserver import settings
import celery
from celery import Celery, Task

def make_celery(name):
    """
    Create a Celery wrapper for use in running
    background tasks.
    """
    celery = Celery(
        name,
        backend=settings.CELERY_RESULT_BACKEND,
        broker=settings.CELERY_BROKER_URL
    )

    return celery
celery = make_celery("nunaserver")

def init_celery(celery, app):
    celery.conf.update(app.config)

    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
