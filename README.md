# SmartParkingHash

Sistem Parkir Cerdas dengan Fungsi Hash  
Anggota: [Nama Kamu] – Mahasiswa Sistem Informasi  

## Fitur
- Slot parkir Motor, Mobil, Bus (utama & cadangan)  
- Fungsi hash: `h(k) = k mod m` dimana `k` = 4 digit terakhir plat nomor  
- Penanganan kolisi dengan linear‐probing  
- Antarmuka sederhana dengan tombol & status slot  

## Cara Menjalankan
1. Pastikan kode berada di `src/main.cpp`.  
2. Jalankan:
   ```bash
   g++ src/main.cpp -o SmartParking./SmartParking
