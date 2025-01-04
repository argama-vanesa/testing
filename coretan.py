import sqlite3

# Cek koneksi database dan isi tabel Users
conn = sqlite3.connect("pharmily.db")
cursor = conn.cursor()

def insert_initial_values(conn):
    cursor = conn.cursor()

    # Cek apakah pengguna dengan username 'dokter1' sudah ada
    cursor.execute("SELECT COUNT(*) FROM Users WHERE username = 'dokter1'")
    if cursor.fetchone()[0] == 0:
        # Menambahkan pengguna dengan peran "dokter"
        cursor.execute('''
            INSERT INTO Users (username, password, role, hospital_name, hospital_address, hospital_contact, doctor_sip, doctor_name)
            VALUES 
            ('dokter1', 'password123', 'dokter', 'RS Sehat Selalu', 'Jl. Kesehatan No.1', '021-1234567', 'SIP-001', 'Dr. Andi')
        ''')

    # Cek apakah pengguna dengan username 'pasien1' sudah ada
    cursor.execute("SELECT COUNT(*) FROM Users WHERE username = 'pasien1'")
    if cursor.fetchone()[0] == 0:
        # Menambahkan pengguna dengan peran "pasien"
        cursor.execute('''
            INSERT INTO Users (username, password, role, patient_name, patient_age, patient_gender, patient_address)
            VALUES 
            ('pasien1', 'password123', 'pasien', 'Budi Santoso', 30, 'Laki-laki', 'Jl. Harmoni No. 2')
        ''')

    # Cek apakah nomor antrean untuk pasien 'pasien1' sudah ada
    cursor.execute("SELECT COUNT(*) FROM QueueNumber WHERE queue_number = 'A001'")
    if cursor.fetchone()[0] == 0:
        # Menambahkan nomor antrean
        cursor.execute('''
            INSERT INTO QueueNumber (patient_id, doctor_id, queue_number, created_at)
            VALUES 
            (2, 1, 'A001', datetime('now', 'localtime'))
        ''')

    conn.commit()
    print("Data awal berhasil ditambahkan ke database.")

# Panggil fungsi untuk menambahkan data awal ke database
insert_initial_values(conn)

# Cek data dalam tabel Users
cursor.execute("SELECT * FROM Users")
users = cursor.fetchall()
print("Data Users:", users)

# Cek data dalam tabel QueueNumber
cursor.execute("SELECT * FROM QueueNumber")
queue = cursor.fetchall()
print("Data QueueNumber:", queue)

# Cek data dalam tabel PrescriptionPDF
cursor.execute("SELECT * FROM PrescriptionPDF")
pres = cursor.fetchall()
print("Data PrescriptionPDF:", pres)

# Tutup koneksi
conn.close()
