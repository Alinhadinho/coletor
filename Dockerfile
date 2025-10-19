# 🧱 Base image: lightweight and up-to-date
FROM python:3.11-slim

# 👇 Install minimal dependencies for Flet Web
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libx11-6 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libcups2 \
    libxkbcommon0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# 🏠 Set working directory
WORKDIR /src

# 📦 Copy dependency file first (for caching)
COPY requirements.txt .

# 🐍 Install Python packages (no root warnings)
RUN pip install --no-cache-dir -r requirements.txt

# 📁 Copy your full app
COPY . .

# 🌐 Expose port 8000 (Render will map $PORT automatically)
EXPOSE 8000

# 🚀 Run the app in web mode, using the correct port
CMD ["python", "-m", "flet", "run", "--web", "--port", "8000", "main.py"]

