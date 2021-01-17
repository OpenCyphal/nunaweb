# Nunaserver

Nunaserver is the backend for the Nunaweb application.
It is responsible for handling uploads from the frontend,
generating the output code, then returning a zipped output
to the user.

It uses Flask (Python 3.7+) and Celery (Redis backend) to
handle jobs asynchronously. A static file server of some kind
is needed to handle serving outputted zip archives.

## Setting up the Server

Setting up nunaserver is slightly complicated due to the several
processes it needs to run. A docker+docker-compose development and
production setup is in the works to simplify this process.

Required tools for the recommended setup process:
- Python 3.7+ (and pip)
- Docker

1. Install requirements with `pip3 install -r requirements.txt`
2. Run the flask dev server with `python3 -m nunaserver`
3. Run the Celery worker with `celery -A nunaserver.generator worker --loglevel=info`
4. Run a basic static file server with `cd static && python3 -m http.server`

This is a dev setup, not meant to be used for production.

## Deploying

Deploying the server consists of 3 steps:

1. Changing settings
2. Deploying Flask
3. Deploying Celery
4. Deploying a static file server

TODO: Plans are in the works for automating deployment
with Docker.
TODO: The project currently needs to be evaluated for scalability.

Change the settings in `nunaserver/settings.py` to match your planned
production environment.
TODO: Env support is planned.

Flask can be deployed with any regular WSGI server. For example, Gunicorn:
`gunicorn --bind 0.0.0.0:5000 nunaserver.wsgi:app`

will run a production WSGI server on port 5000. You can also configure
nginx or most other popular web servers to run nunaserver as a WSGI app.

Celery is more or less the same as the above dev command.

A static file server can be configured using your web server of choice.
