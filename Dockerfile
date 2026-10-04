FROM node:22-bookworm-slim AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY assets ./assets
COPY templates ./templates
COPY apps ./apps
RUN npm run build:css

FROM python:3.14.8-slim AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN useradd --create-home --uid 1000 ministry
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=ministry:ministry . .
RUN mkdir -p media staticfiles && chown -R ministry:ministry /app
USER ministry
ENTRYPOINT ["sh", "docker/entrypoint.sh"]

FROM python-base AS development
USER root
RUN pip install --no-cache-dir ruff==0.16.10
USER ministry
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM python-base AS production
COPY --from=assets --chown=ministry:ministry /app/static/css/app.css /app/static/css/app.css
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
