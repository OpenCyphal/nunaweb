"""
Run Flask dev server.
Allows us to run with `python3 -m nunaserver`.
"""
from nunaserver.server import app

if __name__ == "__main__":
    app.run(port=5000)
