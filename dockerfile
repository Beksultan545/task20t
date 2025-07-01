FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# wait-for-it.sh қосу
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# netcat ашық порт тексеруге керек
RUN apt-get update && apt-get install -y netcat-openbsd

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

