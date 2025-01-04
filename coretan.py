import sqlite3

# Cek koneksi database dan isi tabel Users
conn = sqlite3.connect("pharmily.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM Users")
users = cursor.fetchall()
print(users)
cursor.execute("SELECT * FROM QueueNumber")
queue = cursor.fetchall()
print(queue)
cursor.execute("SELECT * FROM PrescriptionPDF")
pres = cursor.fetchall()
print(pres)
conn.close()