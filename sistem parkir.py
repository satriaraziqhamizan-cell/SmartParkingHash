import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import math
import re
import os

# --------------------------
# KONFIGURASI & DATA AWAL
# --------------------------
slot_sizes = {
    "A": 100,  # Motor utama
    "B": 100,  # Mobil utama
    "C": 50,   # Bus utama
    "D": 50,   # Motor cadangan
    "E": 50,   # Mobil cadangan
    "F": 10    # Bus cadangan
}

# slot_status akan menyimpan None atau dict {'plat': str, 'time_in': datetime, 'jenis': str}
slot_status = {k: [None] * v for k, v in slot_sizes.items()}

# Tarif per jam (pilihan A)
TARIF = {
    "Motor": 2000,
    "Mobil": 3000,
    "Bus": 5000
}

# --------------------------
# HELPER FUNCTIONS
# --------------------------
def hashing(k, size):
    return k % size

def find_free_in_area(area_key, key_value):
    """Cari index kosong di area dengan linear probing mulai dari hash index."""
    size = slot_sizes[area_key]
    start = hashing(key_value, size)
    for i in range(size):
        idx = (start + i) % size
        if slot_status[area_key][idx] is None:
            return idx
    return None  # area penuh

def place_vehicle(jenis, plat):
    """Tempatkan kendaraan berdasarkan jenis; return (area, idx) atau (None, None) jika gagal."""
    angka = "".join(filter(str.isdigit, plat))
    if len(angka) < 4:
        return None, None, "Plat tidak valid (minimal 4 digit angka)."

    key = int(angka[-4:])

    # tentukan area utama dan cadangan
    if jenis == "Motor":
        main, extra = "A", "D"
    elif jenis == "Mobil":
        main, extra = "B", "E"
    else:
        main, extra = "C", "F"

    idx_main = find_free_in_area(main, key)
    if idx_main is not None:
        slot_status[main][idx_main] = {"plat": plat, "time_in": datetime.now(), "jenis": jenis}
        return main, idx_main, None

    idx_extra = find_free_in_area(extra, key)
    if idx_extra is not None:
        slot_status[extra][idx_extra] = {"plat": plat, "time_in": datetime.now(), "jenis": jenis}
        return extra, idx_extra, None

    return None, None, f"❌ Semua area untuk {jenis} penuh!"

def find_vehicle_by_plate(plat):
    """Cari kendaraan berdasarkan plat di semua area. Kembalikan (area, idx, record) atau (None, None, None)."""
    for area, slots in slot_status.items():
        for i, rec in enumerate(slots):
            if rec is not None and rec.get("plat") == plat:
                return area, i, rec
    return None, None, None

def compute_fee(time_in, time_out, jenis):
    """Hitung durasi (jam, pembulatan ke atas) dan biaya."""
    seconds = (time_out - time_in).total_seconds()
    hours = math.ceil(seconds / 3600) if seconds > 0 else 1
    rate = TARIF.get(jenis, 0)
    biaya = hours * rate
    return hours, biaya

def write_ticket_txt(plat, jenis, area, idx, time_in, time_out, hours, biaya):
    """Cetak struk ke file .txt — kembalikan path file."""
    safe_plat = re.sub(r'\s+', '_', plat)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"ticket_{safe_plat}_{timestamp}.txt"
    content = []
    content.append("=== STRUK PARKIR MALL XYZ ===")
    content.append(f"PLAT: {plat}")
    content.append(f"JENIS: {jenis}")
    content.append(f"SLOT: {area}{idx}")
    content.append(f"WAKTU MASUK: {time_in.strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"WAKTU KELUAR: {time_out.strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"DURASI (jam, dibulatkan): {hours} jam")
    content.append(f"BIAYA: Rp {biaya:,}")
    content.append("=============================")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    return os.path.abspath(filename)

# --------------------------
# UI / INTERAKSI
# --------------------------
def update_button_color():
    for kode, buttons in button_grid.items():
        for i, btn in enumerate(buttons):
            rec = slot_status[kode][i]
            if rec is None:
                btn.config(bg="lightgreen")
            else:
                btn.config(bg="red")

def parkir_action():
    jenis = vehicle_type.get()
    plat = input_plat.get().strip()
    if jenis not in ["Motor", "Mobil", "Bus"]:
        output_insert("Jenis kendaraan tidak valid!\n")
        return
    if not plat:
        output_insert("Masukkan plat kendaraan!\n")
        return

    area, idx, err = place_vehicle(jenis, plat)
    if area:
        time_in = slot_status[area][idx]["time_in"]
        msg = f"✅ {plat} ({jenis}) berhasil parkir di slot {area}{idx} pukul {time_in.strftime('%H:%M:%S')}\n"
        output_insert(msg)
        # Popup juga: (sesuai pilihan B -> popup + log)
        messagebox.showinfo("Parkir Berhasil", f"{plat} ditempatkan di {area}{idx}")
    else:
        output_insert(err + "\n")
        messagebox.showwarning("Parkir Gagal", err)

    update_button_color()
    input_plat.delete(0, tk.END)

def keluar_action():
    # minta plat lewat dialog
    plat = simpledialog.askstring("Keluar Parkir", "Masukkan nomor plat kendaraan yang keluar (contoh: BH 1234 ZA):")
    if not plat:
        return
    # cari kendaraan
    area, idx, rec = find_vehicle_by_plate(plat.strip())
    if area is None:
        msg = f"Data kendaraan {plat} tidak ditemukan.\n"
        output_insert(msg)
        messagebox.showerror("Tidak Ditemukan", msg)
        return

    time_in = rec["time_in"]
    time_out = datetime.now()
    jenis = rec["jenis"]
    hours, biaya = compute_fee(time_in, time_out, jenis)

    # tulis tiket .txt
    filepath = write_ticket_txt(plat, jenis, area, idx, time_in, time_out, hours, biaya)

    # kosongkan slot
    slot_status[area][idx] = None
    update_button_color()

    # pesan ke log dan popup
    msg = (f"✅ {plat} keluar dari {area}{idx} | Durasi: {hours} jam | Biaya: Rp {biaya:,}\n"
           f"Struk disimpan: {filepath}\n")
    output_insert(msg)
    messagebox.showinfo("Keluar Parkir", f"{plat} keluar dari {area}{idx}\nDurasi: {hours} jam\nBiaya: Rp {biaya:,}\nStruk: {filepath}")

def output_insert(text):
    output.configure(state='normal')
    output.insert(tk.END, text)
    output.see(tk.END)
    output.configure(state='disabled')

# --------------------------
# BUILD TKINTER UI
# --------------------------
root = tk.Tk()
root.title("Sistem Parkir Cerdas - Tahap 2 (Masuk & Keluar)")
root.geometry("1200x820")

title = tk.Label(root, text="Sistem Parkir Cerdas Mall XYZ - Tahap 2", font=("Arial", 18, "bold"))
title.pack(pady=8)

frame_top = tk.Frame(root)
frame_top.pack(pady=6)

# Dropdown jenis kendaraan
tk.Label(frame_top, text="Jenis Kendaraan:", font=("Arial", 12)).grid(row=0, column=0, padx=6, sticky='e')
vehicle_type = ttk.Combobox(frame_top, values=["Motor", "Mobil", "Bus"], width=12)
vehicle_type.grid(row=0, column=1)
vehicle_type.current(0)

# Input plat
tk.Label(frame_top, text="Plat Nomor:", font=("Arial", 12)).grid(row=1, column=0, padx=6, sticky='e')
input_plat = tk.Entry(frame_top, width=25, font=("Arial", 12))
input_plat.grid(row=1, column=1, pady=4, sticky='w')

# Tombol Parkir Masuk & Keluar
btn_frame = tk.Frame(frame_top)
btn_frame.grid(row=0, column=2, rowspan=2, padx=20)

btn_park = tk.Button(btn_frame, text="Ambil Karcis / Parkir", width=18, height=2, command=parkir_action)
btn_park.grid(row=0, column=0, pady=2, padx=4)

btn_keluar = tk.Button(btn_frame, text="Kendaraan Keluar", width=18, height=2, command=keluar_action)
btn_keluar.grid(row=1, column=0, pady=2, padx=4)

# Status slot label
slot_frame = tk.Frame(root)
slot_frame.pack(pady=6, fill='both', expand=True)

tk.Label(slot_frame, text="Status Slot Parkir (klik tombol slot untuk info)", font=("Arial", 14, "bold")).pack()

# Grid tombol slot
button_grid = {}
for kode, size in slot_sizes.items():
    section_label = tk.Label(slot_frame, text=f"Area {kode} (capacity: {size})", font=("Arial", 11, "bold"))
    section_label.pack(anchor='w', padx=6, pady=(6,0))
    area_frame = tk.Frame(slot_frame)
    area_frame.pack(anchor='w', padx=6, pady=2)
    buttons = []
    cols = 20  # tampil 20 kolom per baris
    for i in range(size):
        def make_callback(a=kode, idx=i):
            def cb():
                rec = slot_status[a][idx]
                if rec:
                    info = (f"Slot {a}{idx}\nPLAT: {rec['plat']}\nJENIS: {rec['jenis']}\n"
                            f"WAKTU MASUK: {rec['time_in'].strftime('%Y-%m-%d %H:%M:%S')}")
                    messagebox.showinfo("Info Slot", info)
                else:
                    messagebox.showinfo("Info Slot", f"Slot {a}{idx} kosong.")
            return cb
        btn = tk.Button(area_frame, text=f"{kode}{i}", width=4, height=1, command=make_callback(kode, i))
        btn.grid(row=i // cols, column=i % cols, padx=1, pady=1)
        buttons.append(btn)
    button_grid[kode] = buttons

update_button_color()

# Output log (read-only)
output_label = tk.Label(root, text="Log Sistem:", font=("Arial", 12, "bold"))
output_label.pack(pady=(8,0))
output = tk.Text(root, height=10, width=140, state='disabled', wrap='word')
output.pack(padx=8, pady=6)

# Jalankan UI
root.mainloop()
