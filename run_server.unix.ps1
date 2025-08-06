cd dashboard

poetry run gunicorn root:server --bind 0.0.0.0:8000
