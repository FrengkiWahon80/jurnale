import streamlit as st
import sqlite3
from docxtpl import DocxTemplate
from datetime import datetime
import io

# Konfigurasi Halaman
st.set_page_config(page_title="Jurnal Anak Indonesia Hebat", page_icon="🇮🇩", layout="wide")

# --- DATABASE SETUP (SQLite) ---
conn = sqlite3.connect('jurnal_sekolah.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        nama_lengkap TEXT,
        nip TEXT,
        role TEXT,
        nama_kelas TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_siswa TEXT,
        nisn TEXT UNIQUE,
        nama_kelas TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        tanggal TEXT,
        catatan_harian TEXT
    )
''')

# Masukkan Dummy User & Siswa jika belum ada
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("
