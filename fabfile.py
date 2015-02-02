from fabric.api import run, task
from fabtools.vagrant import vagrant

vagrant = vagrant  # Silence flake8


@task
def ping():
    """
    This is just a test function.
    """
    run("echo pong")
