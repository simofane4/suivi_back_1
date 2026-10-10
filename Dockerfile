# Use Python 3.12 slim
FROM python:3.12-slim

# Install system deps for Pillow, psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --settings=suivi_back.settings.prod

# Expose port. Render injects a PORT at runtime and routes to it, so the app has
# to bind that value rather than a fixed one.
EXPOSE 8000

# Migrate before serving. Render does not run migrations for `env: docker`
# services, so without this the Postgres instance stays empty and every endpoint
# fails on an unmigrated schema. `exec` keeps gunicorn as PID 1 so signals and
# zero-downtime deploys still work.
CMD ["sh", "-c", "python manage.py migrate --noinput --settings=suivi_back.settings.prod && exec gunicorn suivi_back.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-4} --timeout 120"]