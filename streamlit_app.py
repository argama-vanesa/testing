import streamlit as st
import sqlite3
from fpdf import FPDF
from datetime import datetime
import pytz
import os

def create_tables(conn):
    cursor = conn.cursor()
    # Membuat tabel Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,  -- Gunakan hash password untuk keamanan
            role TEXT NOT NULL,  -- "dokter", "apotek", "pasien"
            hospital_name TEXT,  -- Nama rumah sakit (hanya untuk dokter)
            hospital_address TEXT,  -- Alamat rumah sakit (hanya untuk dokter)
            hospital_contact TEXT,  -- Kontak rumah sakit (hanya untuk dokter)
            doctor_sip TEXT,  -- Hanya untuk dokter
            doctor_name TEXT,  -- Hanya untuk dokter
            patient_name TEXT,  -- Hanya untuk pasien
            patient_age INTEGER,  -- Hanya untuk pasien
            patient_gender TEXT,  -- Hanya untuk pasien
            patient_address TEXT  -- Hanya untuk pasien
        )
    ''')

    # Membuat tabel PrescriptionPDF
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PrescriptionPDF (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_filename TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Menunggu'
        )
    ''')

    # Membuat tabel QueueNumber
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS QueueNumber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            queue_number TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES Users(id),
            FOREIGN KEY(doctor_id) REFERENCES Users(id)
        )
    ''')

    conn.commit()

# Kelas untuk membuat file PDF resep
class DoctorPrescriptionPDF(FPDF):
    def __init__(self, hospital_name=None, doctor_name=None, doctor_sip=None, address=None, contact=None, **kwargs):
        super().__init__(**kwargs)
        self.hospital_name = hospital_name
        self.doctor_name = doctor_name
        self.doctor_sip = doctor_sip
        self.address = address
        self.contact = contact

    def header(self):
        if self.hospital_name:
            self.set_font('Times', 'B', 16)
            self.cell(0, 10, f'{self.hospital_name}', ln=True, align='C')
            self.set_font('Times', 'B', 12)
            self.cell(0, 8, f'Dokter: {self.doctor_name} | SIP: {self.doctor_sip}', ln=True, align='C')
            self.cell(0, 8, f'Alamat: {self.address}', ln=True, align='C')
            self.cell(0, 8, f'Kontak: {self.contact}', ln=True, align='C')
            self.ln(5)
            self.cell(0, 0, '', 'T', 1, 'C')  # Garis horizontal
            self.ln(5)

    def add_date_and_location(self, created_at):
        self.set_y(50)  # Tepat di bawah header
        self.set_x(-70)  # Geser ke kanan (pojok kanan atas)
        self.set_font('Times', 'I', 12)
        self.cell(0, 10, f'{created_at}', ln=True, align='R')

    def add_prescription_details(self, prescriptions):
        self.set_y(70)  # Mulai di tengah halaman
        self.ln(5)
        self.set_font('Times', '', 12)
        for prescription in prescriptions:
            self.cell(0, 10, f'R/ {prescription["nama obat"]}, {prescription["bentuk sediaan"]}, {prescription["wadah penyimpanan"]}, {prescription["jumlah obat"]}', ln=True, align='C')
            self.cell(0, 10, f'S {prescription["frekuensi"]} {prescription["takaran"]} {prescription["keterangan"]}', ln=True, align='C')
            self.ln(5)
            self.cell(0, 0, '', 'T', 1, 'C')  # Garis horizontal
            self.ln(5)

    def add_patient_info(self, patient_name, patient_gender, patient_age, patient_address):
        self.set_y(200)  # Posisikan di bagian bawah halaman
        self.set_font('Times', '', 12)
        self.ln(5)
        self.cell(0, 0, '', 'T', 1, 'C')  # Garis horizontal
        self.ln(5)
        self.cell(0, 10, f'Nama            : {patient_name}', ln=True, align='L')
        self.cell(0, 10, f'Jenis Kelamin: {patient_gender}', ln=True, align='L')
        self.cell(0, 10, f'Umur        : {patient_age} tahun', ln=True, align='L')
        self.cell(0, 10, f'Alamat      : {patient_address}', ln=True, align='L')

    def add_footer(self, hospital_name, doctor_name):
        self.set_y(-30)
        self.set_font('Times', 'I', 12)
        self.cell(0, 10, f'{hospital_name} - {doctor_name}', 0, 0, 'C')

# Fungsi input data resep
def input_prescriptions():
    st.subheader("Input Resep")
    prescriptions = []
    n = st.number_input("Jumlah Obat dalam Resep", min_value=1, step=1)
    for i in range(n):
        nama_obat = st.text_input(f"Nama Obat {i + 1}")
        bentuk_sediaan = st.text_input(f"Bentuk Sediaan {i + 1}")
        wadah_penyimpanan = st.text_input(f"Wadah Penyimpanan {i + 1}")
        jumlah_obat = st.text_input(f"Jumlah Obat {i + 1}")
        frekuensi = st.text_input(f"Frekuensi Penggunaan Obat {i + 1}")
        takaran = st.text_input(f"Takaran {i + 1}")
        keterangan = st.text_area(f"Keterangan Tambahan {i + 1}")
        if nama_obat:
            prescriptions.append({
                'nama obat': nama_obat,
                'bentuk sediaan': bentuk_sediaan,
                'wadah penyimpanan': wadah_penyimpanan,
                'jumlah obat': jumlah_obat,
                'frekuensi': frekuensi,
                'takaran': takaran,
                'keterangan': keterangan,
            })
    return prescriptions

def doctor_prescription_ui(conn, doctor_id, queue_number):
    if not queue_number.strip():
        st.error("Nomor antrian tidak boleh kosong! Masukkan nomor antrian yang valid.")
        return

    try:
        cursor = conn.cursor()

        # Ambil informasi dokter berdasarkan ID
        cursor.execute('''
            SELECT doctor_name, doctor_sip, hospital_address,
                   hospital_contact, hospital_name
            FROM Users
            WHERE id = ? AND role = 'dokter'
        ''', (doctor_id,))
        hospital_info = cursor.fetchone()

        if not hospital_info:
            st.error("Dokter tidak ditemukan! Pastikan ID dokter benar.")
            return

        # Ambil informasi pasien berdasarkan nomor antrian
        cursor.execute('''
            SELECT U.patient_name, U.patient_age, U.patient_gender, U.patient_address
            FROM Users U
            INNER JOIN QueueNumber Q ON U.id = Q.patient_id
            WHERE Q.queue_number = ?
        ''', (queue_number,))
        patient_info = cursor.fetchone()

        if not patient_info:
            st.error("Pasien tidak ditemukan! Pastikan nomor antrian valid.")
            return

        # Informasi dokter dan pasien
        doctor_name, doctor_sip, hospital_address, hospital_contact, hospital_name = hospital_info
        patient_name, patient_age, patient_gender, patient_address = patient_info

        st.write(f"Data Pasien: {patient_name}, {patient_age} tahun, {patient_gender}, {patient_address}")

        # Input resep oleh dokter
        prescriptions = input_prescriptions()

        # Waktu pembuatan resep
        timezone = pytz.timezone('Asia/Jakarta')
        created_at = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')

        # Membuat PDF resep
        pdf = DoctorPrescriptionPDF(
            hospital_name=hospital_name,
            doctor_name=doctor_name,
            doctor_sip=doctor_sip,
            address=hospital_address,
            contact=hospital_contact
        )
        pdf.add_page()
        pdf.add_date_and_location(created_at)
        pdf.add_prescription_details(prescriptions)
        pdf.add_patient_info(patient_name, patient_gender, patient_age, patient_address)

        # Simpan PDF sementara
        folder = './temp_prescriptions'
        if not os.path.exists(folder):
            os.makedirs(folder)

        pdf_filename = f"prescription_{queue_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_filepath = os.path.join(folder, pdf_filename)
        pdf.output(pdf_filepath)

        # Simpan ke database
        cursor.execute('''
            INSERT INTO PrescriptionPDF (pdf_filename, created_at, status)
            VALUES (?, ?, 'Menunggu')
        ''', (pdf_filename, created_at))
        conn.commit()

        st.success(f"Resep berhasil dibuat! File tersimpan sebagai {pdf_filename}")

        with open(pdf_filepath, "rb") as file:
            btn = st.download_button(
                label="Download Resep",
                data=file,
                file_name=pdf_filename,
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
if __name__ == "__main__":
    # Buat koneksi ke database SQLite
    conn = sqlite3.connect("pharmily.db")
    create_tables(conn)

    # Judul aplikasi
    st.title("Aplikasi Resep Dokter Elektronik")

    # Pilihan role pengguna
    role = st.sidebar.selectbox("Pilih Role", ["Dokter", "Apotek", "Pasien"])

    if role == "Dokter":
        doctor_id = st.sidebar.text_input("Masukkan ID Dokter", type="password")
        queue_number = st.text_input("Masukkan Nomor Antrian")
        if st.button("Proses Resep"):
            doctor_prescription_ui(conn, doctor_id, queue_number)

if __name__ == "__main__":
    # Membuat koneksi ke database
    conn = sqlite3.connect('hospital_app.db')

    # Membuat tabel
    create_tables(conn)

    # Tutup koneksi
    conn.close()
