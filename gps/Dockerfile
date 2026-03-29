FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1

RUN uv pip install "fastmcp>=2.0"

COPY server.py ./

EXPOSE 8101

CMD ["python", "server.py"]
