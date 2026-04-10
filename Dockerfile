# Pakai Python versi 3.11
FROM python:3.11-slim

# Buat folder kerja di dalam container
WORKDIR /app

# Copy file requirements dulu (biar lebih cepat build ulang)
COPY requirements.txt .

# Install semua library yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file aplikasi
COPY . .

# Buka port 5000
EXPOSE 5000

# Jalankan aplikasi pakai gunicorn (lebih stabil dari flask langsung)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]