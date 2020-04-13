FROM python:3-slim

WORKDIR /nm-stats

# RUN apt-get update && apt-get install -y --force-yes libpq-dev gcc
# RUN pip --no-cache-dir install toml prometheus_client psycopg2psycopg2-binary
RUN pip --no-cache-dir install toml prometheus_client psycopg2-binary
# RUN mkdir -p /etc/nm-stats
# RUN ln -s /etc/nm-stats/config.toml config.toml

EXPOSE 8000

COPY . .
