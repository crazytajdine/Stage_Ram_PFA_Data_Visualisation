FROM python:3.10-slim

WORKDIR /app


COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    \
    rm -rf ~/.cache/pip

COPY dashboard/ .



CMD [ "gunicorn", "root:server", "--bind", "0.0.0.0:8000"]