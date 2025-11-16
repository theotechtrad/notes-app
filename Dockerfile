FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# FIX: fallback to 5000 if $PORT is not set (Docker Desktop)
CMD ["sh","-c","gunicorn -w 4 -b :${PORT:-5000} app:app"]
