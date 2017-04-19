FROM python:3.5.3-slim

RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid 10001 --shell /usr/sbin/nologin --home /app --create-home app

WORKDIR /app/

RUN apt-get update && \
    apt-get install -y gcc apt-transport-https

# Install pip and requirements
COPY ./requirements.txt /app/requirements.txt

RUN pip install -U 'pip>=8' && \
    pip install --no-cache-dir -r requirements.txt

# Install the app
COPY . /app/

# Set Python-related environment variables to reduce annoying-ness
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PORT 8000

USER app
EXPOSE $PORT

# FIXME(willkg): Set ENTRYPOINT and CMD.
# https://github.com/mozilla-services/Dockerflow#dockerfile-requirements
