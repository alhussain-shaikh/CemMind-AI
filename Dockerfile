FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Install the project in editable mode
RUN pip install -e .

EXPOSE 8080

ENV STREAMLIT_SERVER_HEADLESS=true

CMD ["streamlit", "run", "app.py"] 