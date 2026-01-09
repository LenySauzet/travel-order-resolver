FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.9.15 /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN uv sync --locked

EXPOSE 8000 8501
