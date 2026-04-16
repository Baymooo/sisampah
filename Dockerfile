FROM python:3.11-slim

WORKDIR /app

# Install build dependencies untuk package 'cryptography'
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Perhatikan jumlah worker: untuk t2.micro (gratisan EC2), 
# 1 worker dengan 2-4 threads sudah cukup stabil.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120", "app:app"]