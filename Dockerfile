FROM python:3.10-slim

ENV \
    # poetry
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_ANSI=1

WORKDIR /app

RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.8.3

COPY ./pyproject.toml ./poetry.lock ./

RUN poetry install --only main --no-root

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
