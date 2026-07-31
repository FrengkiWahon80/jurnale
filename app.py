# --- MENU 1: DATA SISWA (Lengkap dengan Edit & Hapus) ---
if menu == "Data Siswa":
    st.header("Manajemen Data Siswa")
    
    # 1. Form Tambah Siswa
    with st.expander("➕ Tambah Siswa Baru"):
        with st.form("tambah_siswa"):
            nama_baru = st.text_input("Nama Siswa Baru")
            nisn_baru = st.text_input("NISN")
            if st.form_submit_button("Simpan Siswa"):
                if nama_baru:
                    new_row = pd.DataFrame({"Nama": [nama_baru], "NISN": [nisn_baru]})
                    df_siswa = pd.concat([df_siswa, new_row], ignore_index=True)
                    save_data(df_siswa, "siswa.csv")
                    st.success("Siswa berhasil ditambahkan!")
                    st.rerun()

    st.divider()

    # 2. Tabel Edit Data (Inline Editing)
    st.subheader("Edit Biodata Siswa")
    st.info("💡 Klik pada sel tabel di bawah untuk mengubah Nama atau NISN, lalu tekan tombol 'Simpan Perubahan'.")
    
    # Menampilkan data editor
    edited_df = st.data_editor(df_siswa, num_rows="dynamic", key="editor_siswa")
    
    if st.button("💾 Simpan Perubahan"):
        # Logika Sinkronisasi: Jika nama berubah, update juga di jurnal.csv
        for index, row in edited_df.iterrows():
            if index < len(df_siswa):
                old_name = df_siswa.iloc[index]["Nama"]
                new_name = row["Nama"]
                
                if old_name != new_name:
                    # Update nama di file jurnal
                    df_jurnal.loc[df_jurnal["Nama"] == old_name, "Nama"] = new_name
                    save_data(df_jurnal, "jurnal.csv")
        
        # Simpan perubahan biodata
        save_data(edited_df, "siswa.csv")
        st.success("Perubahan biodata dan riwayat jurnal berhasil disinkronkan!")
        st.rerun()

    st.divider()

    # 3. Fitur Hapus Siswa
    st.subheader("🗑️ Hapus Siswa")
    if not df_siswa.empty:
        siswa_hapus = st.selectbox("Pilih Siswa yang akan dihapus", df_siswa["Nama"].tolist())
        konfirmasi = st.checkbox(f"Saya yakin ingin menghapus {siswa_hapus} dan semua catatan jurnalnya.")
        
        if st.button("Hapus Permanen"):
            if konfirmasi:
                # Hapus dari data siswa
                df_siswa = df_siswa[df_siswa["Nama"] != siswa_hapus]
                save_data(df_siswa, "siswa.csv")
                
                # Hapus dari data jurnal
                df_jurnal = df_jurnal[df_jurnal["Nama"] != siswa_hapus]
                save_data(df_jurnal, "jurnal.csv")
                
                st.error(f"Data {siswa_hapus} telah dihapus dari sistem.")
                st.rerun()
            else:
                st.warning("Silakan centang kotak konfirmasi terlebih dahulu.")
