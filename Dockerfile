# Use a lightweight Python base image
FROM python:3.11-slim

# Install minimal system packages needed for flet-web (no GUI)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libgdk-pixbuf2.0-0 libx11-6 \
    libatk1.0-0 libatk-bridge2.0-0 libxcomposite1 libxdamage1 \
    libxrandr2 libasound2 libpangocairo-1.0-0 libcups2 \
    libxkbcommon0 libgbm1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 🚨 The important part — run in web mode!
CMD ["python", "-m", "flet", "run", "--web", "--port", "8000", "main.py"]
