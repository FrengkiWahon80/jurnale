from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from docxtpl import DocxTemplate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci-rahasia-sekolah-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jurnal_sekolah.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== DATABASE MODELS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    nip = db.Column(db.String(50))
    role = db.Column(db.String(20), default='guru_wali') # 'guru_wali' / 'kepsek'
    nama_kelas = db.Column(db.String(50)) # Isolasi Kelas untuk Guru Wali

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_siswa = db.Column(db.String(100), nullable=False)
    nisn = db.Column(db.String(20), unique=True, nullable=False)
    nama_kelas = db.Column(db.String(50), nullable=False)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    tanggal = db.Column(db.String(20), nullable=False)
    catatan_harian = db.Column(db.Text) # CATATAN HARIAN WALI KELAS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== ROUTES / ALUR APLIKASI ====================

@app.route('/')
@login_required
def index():
    # ISOLASI DATA: Guru hanya bisa melihat siswa di kelasnya sendiri
    if current_user.role == 'guru_wali':
        siswa_list = Student.query.filter_by(nama_kelas=current_user.nama_kelas).all()
    else:
        siswa_list = Student.query.all() # Kepsek bisa lihat semua
    
    return render_template('index.html', siswa=siswa_list)

@app.route('/simpan-jurnal-harian', methods=['POST'])
@login_required
def simpan_jurnal_harian():
    student_id = request.form.get('student_id')
    tanggal = request.form.get('tanggal')
    catatan_harian = request.form.get('catatan_harian')

    entry = JournalEntry(
        student_id=student_id,
        tanggal=tanggal,
        catatan_harian=catatan_harian
    )
    db.session.add(entry)
    db.session.commit()
    flash('Catatan harian berhasil disimpan!')
    return redirect(url_for('index'))

# ==================== GENERATE MS WORD (.DOCX) ====================
@app.route('/download-word/<int:student_id>')
@login_required
def download_word(student_id):
    siswa = Student.query.get_or_404(student_id)
    guru = current_user
    kepsek = User.query.filter_by(role='kepsek').first()

    # Ambil seluruh catatan harian siswa ini
    catatan_list = JournalEntry.query.filter_by(student_id=student_id).all()
    
    # Format data catatan harian untuk template Word
    catatan_data = []
    for c in catatan_list:
        if c.catatan_harian:
            catatan_data.append({
                'tanggal': c.tanggal,
                'isi': c.catatan_harian
            })

    # Load Template Word
    doc = DocxTemplate("template_laporan.docx")

    # Context Data yang akan dikirim ke MS Word
    context = {
        'NAMA_SISWA': siswa.nama_siswa,
        'NISN': siswa.nisn,
        'NAMA_KELAS': siswa.nama_kelas,
        'PERIODE': datetime.now().strftime("%B %Y"),
        'NAMA_GURU': guru.nama_lengkap,
        'NIP_GURU': guru.nip,
        'NAMA_KEPSEK': kepsek.nama_lengkap if kepsek else 'Kepala Sekolah',
        'NIP_KEPSEK': kepsek.nip if kepsek else '-',
        'CATATAN_HARIAN': catatan_data # Array untuk looping di Word
    }

    doc.render(context)
    
    output_filename = f"Laporan_{siswa.nama_siswa.replace(' ', '_')}.docx"
    doc.save(output_filename)

    return send_file(output_filename, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Membuat database SQLite otomatis jika belum ada
    app.run(debug=True)
