from flask import Flask, render_template, request, redirect, url_for
import boto3
import pymysql
import os
import uuid

app = Flask(__name__)

# =========================
# S3 (LAZY INIT - FIX MEMORY ISSUE)
# =========================
def get_s3():
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
        region_name='ap-southeast-2'
    )

BUCKET_NAME = os.environ.get('S3_BUCKET')

# =========================
# DATABASE
# =========================
def get_db():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        connect_timeout=5
    )

# =========================
# INIT DB
# =========================
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS laporan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama TEXT,
            lokasi TEXT,
            deskripsi TEXT,
            foto_url TEXT,
            status VARCHAR(50) DEFAULT 'baru',
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# =========================
# ROUTE HOME
# =========================
@app.route('/')
def index():
    return render_template('index.html')

# =========================
# LAPORAN
# =========================
@app.route('/laporan', methods=['GET', 'POST'])
def laporan():
    if request.method == 'POST':
        try:
            nama = request.form.get('nama')
            lokasi = request.form.get('lokasi')
            deskripsi = request.form.get('deskripsi')
            foto = request.files.get('foto')

            if not all([nama, lokasi, deskripsi, foto]):
                return "Data tidak lengkap", 400

            filename = f"{uuid.uuid4()}_{foto.filename}"

            # upload S3
            s3 = get_s3()
            s3.upload_fileobj(foto, BUCKET_NAME, filename)

            foto_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"

            # save DB
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO laporan (nama, lokasi, deskripsi, foto_url) VALUES (%s,%s,%s,%s)",
                (nama, lokasi, deskripsi, foto_url)
            )
            conn.commit()
            cur.close()
            conn.close()

            return redirect(url_for('index'))

        except Exception as e:
            print("ERROR:", e)
            return str(e), 500

    return render_template('laporan.html')

# =========================
# ADMIN
# =========================
@app.route('/admin')
def admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM laporan ORDER BY tanggal DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin.html', laporan=data)

# =========================
# UPDATE STATUS
# =========================
@app.route('/update/<int:id>', methods=['POST'])
def update_status(id):
    status = request.form.get('status')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE laporan SET status=%s WHERE id=%s", (status, id))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin'))

# =========================
# MAIN
# =========================
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
