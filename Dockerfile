# The production image: what Railway builds and runs (see docs/DEPLOY.md).
#
# Two stages. The first has uv and builds the virtualenv; the second copies
# only the finished app across, so uv itself (about 40 MB) never ships.
# Dependencies install before the code is copied in, so a change to the code
# alone reuses the cached dependency layer and the build takes seconds.

FROM python:3.14-slim AS build

# uv, pinned to the version the lockfile was written with.
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

WORKDIR /app

# Compile to bytecode at build time, so the first request doesn't pay for it.
# Copy packages into the virtualenv rather than hard-linking them from uv's
# cache, and keep no cache, since the cache is never needed again.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .
RUN uv sync --locked --no-dev


FROM python:3.14-slim

# Run as an unprivileged user, so a bug in the app can't rewrite the image.
RUN useradd --system --no-create-home app

WORKDIR /app
COPY --from=build /app /app
USER app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# `fastapi run` serves on 0.0.0.0 and reads the port from $PORT, which Railway
# sets. Proxy headers are on by default; trusting them from any address is
# safe here because only Railway's proxy can reach the container, and it's
# what gives the app the buyer's real IP instead of the proxy's.
CMD ["fastapi", "run", "app/main.py", "--forwarded-allow-ips", "*"]
