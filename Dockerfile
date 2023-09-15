FROM python:3.9.18-bullseye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
RUN pip install -U pip && pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv install --dev --system --deploy --ignore-pipfile
COPY . /code/
