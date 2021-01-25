"""
Run Nunavut jobs as Celery background tasks
to allow for long-running jobs.
"""
from celery import Celery, Task
from nunaserver import settings


def make_celery(name):
    """
    Create a Celery wrapper for use in running
    background tasks.
    """
    celery_inst = Celery(
        name, backend=settings.CELERY_RESULT_BACKEND, broker=settings.CELERY_BROKER_URL
    )

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
