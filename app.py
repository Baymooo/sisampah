from flask import Flask, render_template, request, redirect, url_for
import boto3
import psycopg2
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Koneksi ke S3
s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
    region_name='ap-southeast-1'
)
BUCKET_NAME = os.environ.get('S3_BUCKET')

# Koneksi ke RDS (database)
def get_db():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS')
    )

# Buat tabel kalau belum ada
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS laporan (
            id SERIAL PRIMARY KEY,
            nama TEXT,
            lokasi TEXT,
            deskripsi TEXT,
            foto_url TEXT,
            status TEXT DEFAULT 'baru',
            tanggal TIMESTAMP DEFAULT NOW()
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# FITUR 1: Halaman utama
@app.route('/')
def index():
    return render_template('index.html')

# FITUR 2: Form laporan + upload foto ke S3
@app.route('/laporan', methods=['GET', 'POST'])
def laporan():
    if request.method == 'POST':
        nama = request.form['nama']
        lokasi = request.form['lokasi']
        deskripsi = request.form['deskripsi']
        foto = request.files['foto']

        # Upload foto ke S3
        filename = f"{uuid.uuid4()}_{foto.filename}"
        s3.upload_fileobj(foto, BUCKET_NAME, filename)
        foto_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"

        # Simpan ke database RDS
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO laporan (nama, lokasi, deskripsi, foto_url) VALUES (%s, %s, %s, %s)",
            (nama, lokasi, deskripsi, foto_url)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('index'))

    return render_template('laporan.html')

# FITUR 3: Dashboard admin
@app.route('/admin')
def admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM laporan ORDER BY tanggal DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', laporan=data)

# Update status laporan
@app.route('/update/<int:id>', methods=['POST'])
def update_status(id):
    status = request.form['status']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE laporan SET status=%s WHERE id=%s", (status, id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)