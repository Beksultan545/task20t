FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y netcat-openbsd
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY . .
COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

CMD ["./wait-for-it.sh", "postgres:5432", "--", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
