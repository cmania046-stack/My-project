import socket, threading, time, requests
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from datetime import datetime, timedelta
import copy, json, os, hashlib, random, qrcode, barcode, sqlite3, shutil, sys, zipfile, uuid, traceback, ipaddress
import calendar
from barcode.writer import ImageWriter
from passlib.hash import pbkdf2_sha256
from copy import deepcopy
from PIL import Image, ImageOps
from waitress import serve
from flask_cors import CORS
from itertools import product
from pathlib import Path
from io import BytesIO
from tunnel_helper import get_tunnel

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
    
BROADCAST_PORT = 55000  
SERVER_PORT = 5000 
def udp_broadcast_listener():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", BROADCAST_PORT))
    except OSError as e:
        print(f"[UDP BROADCAST ERROR] Gagal bind port {BROADCAST_PORT}: {e}")
        return

    print(f"\n[UDP BROADCAST] Mendengar di port {BROADCAST_PORT}...")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data.decode() == "DISCOVER_SERVER":
                response = f"SERVER_HERE:{SERVER_PORT}"
                sock.sendto(response.encode(), addr)
        except Exception as e:
            print(f"[UDP BROADCAST ERROR] {e}")

def start_udp_broadcast():
    thread = threading.Thread(target=udp_broadcast_listener, daemon=True)
    thread.start()
    
app = Flask(__name__)
CORS(app)

def app_get_data_folder():
	if sys.platform == "win32":
		base = os.path.join(os.environ["LOCALAPPDATA"], "FOLDER DATABASE APP FIXY POINT")
	elif sys.platform == "darwin":
		base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "FOLDER DATABASE APP FIXY POINT")
	else:
		base = os.path.join(os.path.expanduser("~"), ".local", "share", "FOLDER DATABASE APP FIXY POINT")
	return base

basedir = app_get_data_folder()

folder_struk = os.path.join(basedir, "Template struk")
folder_pembayaran = os.path.join(basedir, "Media pembayaran")
folder_foto = os.path.join(basedir, "Kumpulan Gambar Toko")
folder_katalog = os.path.join(basedir, "Katalog produk")
folder_backup = os.path.join(basedir, "Folder backup")
folder_sqlite = os.path.join(basedir, "DATABASE UTAMA")
folder_nota = os.path.join(basedir, "Nota penjualan")
folder_ips = os.path.join(basedir, "Folder IPS Cloudflare")
 
for f in [folder_ips, folder_struk, folder_pembayaran, folder_foto, folder_katalog, folder_backup, folder_sqlite, folder_nota]:
	os.makedirs(f, exist_ok=True)

map_folder = {
	"folder_struk": folder_struk,
	"folder_pembayaran": folder_pembayaran,
	"folder_foto": folder_foto,
	"folder_katalog": folder_katalog,
	"folder_backup": folder_backup,
	"folder_sqlite": folder_sqlite,
	"folder_nota": folder_nota,
	"folder_ips": folder_ips
}

file_desimal = os.path.join(folder_sqlite, "Izin desimal.json")
file_server = os.path.join(folder_sqlite, "Opsi server.json")
session = os.path.join(folder_sqlite, "Status login.json")
file_ips = os.path.join(folder_ips, "ips cloudflare.json")
file_blokir = os.path.join(folder_ips, "Data pemblokiran ip.json")
file_register_guard = os.path.join(folder_ips, "Data penjaga signup.json")

def open_json(path, default):
	if os.path.exists(path):
		try:
			with open(path, "r") as f:
				return json.load(f)
		except:
			return default
	else:
		return default
		
desimal = open_json(file_desimal, {})
opsi_server = open_json(file_server, {"opsi": "Local server"})
ses = open_json(session, [])
ips = open_json(file_ips, [])
blokir = open_json(file_blokir, {})
register_guard = open_json(file_register_guard, {})

#=====Website folders=========

folder_html = "MyHTML"
folder_atribut = "Atributs"
for p in [folder_html, folder_atribut]:
	os.makedirs(p, exist_ok=True)

#=========================

def simpan_semua(path, file):
    with open(path, "w") as f:
    	json.dump(file, f, indent=4, ensure_ascii=False)
  
def path_database():
	path = os.path.join(folder_sqlite, "pos.db")
	return path
	
def get_ips():
	ips.clear()
	try:
		res_ips_v4 = requests.get("https://www.cloudflare.com/ips-v4", timeout=30)
		res_ips_v6 = requests.get("https://www.cloudflare.com/ips-v6", timeout=30)
		if res_ips_v4:
			split_ips_v4 = res_ips_v4.text.split("\n")
			for ips_str in split_ips_v4:
				if ips_str != "":
					ips.append(ips_str)
		if res_ips_v6:
			split_ips_v6 = res_ips_v6.text.split("\n")
			for ips_str in split_ips_v6:
				if ips_str != "":
					ips.append(ips_str)
		simpan_semua(file_ips, ips)
		print("\n====== Ips cloudflare telah disimpan ========\n")
			
	except Exception as e:
		print(e)
		
def request_dari_cloudflare(rem):
	try:
		ip = ipaddress.ip_address(rem)
		return any(ip in ipaddress.ip_network(cidr) for cidr in ips)
	except ValueError:
		return False
		
def get_real_ip():
	if not os.environ.get("APP_ENV") == "production":
		return request.remote_addr
	from_cloudflare = request_dari_cloudflare(request.remote_addr)
	if from_cloudflare and request.headers.get("CF-Connecting-IP"):
		return request.headers.get("CF-Connecting-IP")
	return request.remote_addr

max_gagal = 3
reset_after = 30
lock = threading.Lock()

def catat_gagal_login(ip):
	with lock:
		data = blokir.setdefault(ip, {"gagal": 0, "diblokir_hingga": None})
		data["gagal"] += 1
		if data["gagal"] >= max_gagal:
			data["diblokir_hingga"] = int(time.time()) + reset_after
		simpan_semua(file_blokir, blokir)

def tambah_poin(ip, status):
	with lock:
		data = register_guard.setdefault(ip, {"success": 0, "fail": 0, "diblokir_hingga": None})
		data[status] += 1
		if data["fail"] >= 5 or data["success"] >= 3:
			data["diblokir_hingga"] = int(time.time()) + 86400
			data["fail"] = 0
			data["success"] = 0
		simpan_semua(file_register_guard, register_guard)
		
def reset_percobaan(ip):
	with lock:
		blokir.pop(ip, None)
		simpan_semua(file_blokir, blokir)
			
def cek_blokir(ip):
	with lock:
		data = blokir.get(ip, {})
		if data and data["diblokir_hingga"]:
			sisa = data["diblokir_hingga"] - int(time.time())
			if sisa > 0:
				return True, sisa
			else:
				blokir[ip] = {"gagal": 0, "diblokir_hingga": None}
			simpan_semua(file_blokir, blokir)
		return False, 0
		
def cek_ip_register(ip):
	with lock:
		data = register_guard.get(ip,{})
		if data and data["diblokir_hingga"]:
			sisa = data["diblokir_hingga"] - int(time.time())
			if sisa > 0:
				return True, sisa
			else:
				register_guard[ip] = {"success": 0, "fail": 0, "diblokir_hingga": None}
			simpan_semua(file_register_guard, register_guard)
		return False, 0
		
def periode_bulan():
	sekarang = datetime.now()
	start = sekarang.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	last_day = calendar.monthrange(sekarang.year, sekarang.month)[1]
	end = sekarang.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
	return start, end
	
def periode_minggu():
	sekarang = datetime.now()
	start = (sekarang - timedelta(days=sekarang.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
	end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
	return start, end

def periode_hari():
	sekarang = datetime.now()
	start = sekarang.replace(hour=0, minute=0, second=0, microsecond=0)
	end = sekarang.replace(hour=23, minute=59, second=59, microsecond=999999)
	return start, end
		
def now_str():
	conn = None
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT format_waktu FROM pengaturan_format")
		waktu = cursor.fetchone()
		if not waktu:
			return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		return datetime.now().strftime(waktu["format_waktu"])
	finally:
		if conn is not None:
			conn.close()
						
def parse_date(s):
	list_tanggal = [
		"%d/%m/%Y",
		"%m/%d/%Y",
		"%d-%m-%Y",
		"%m-%d-%Y",
		"%Y/%m/%d",
		"%Y-%m-%d",
		"%d/%m/%y",
		"%d-%m-%y",
		"%m/%d/%y",
		"%m-%d-%y",
		"%y/%m/%d",
		"%y-%m-%d",
		"%A, %d %B %Y"
	]
	list_waktu = [
		"%H:%M:%S",
		"%H/%M/%S",
		"%H.%M.%S",
		"%H:%M",
		"%H/%M",
		"%H.%M",
	]
	formats = [f"{d} {t}" for d, t in product(list_tanggal, list_waktu)]
	formats += list_tanggal
	for p in formats:
		try:
			time_parsed = datetime.strptime(s, p)
			return time_parsed
		except Exception:
			continue
	return None
	
map_periode = {
	"hari_ini": periode_hari,
	"minggu_ini": periode_minggu,
	"bulan_ini": periode_bulan
}
		
conn = sqlite3.connect(path_database())
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def create_table(name, table_header):
	cursor.execute(f"""
	CREATE TABLE IF NOT EXISTS {name} (
		id INTEGER PRIMARY KEY AUTOINCREMENT, {table_header})""")
		
create_table("Pengeluaran", "waktu TEXT, nama TEXT, jumlah INTEGER, satuan_jumlah TEXT, harga INTEGER, total INTEGER, kategori TEXT, keterangan TEXT, operator TEXT, sumber TEXT")
create_table("profil", "nama TEXT, alamat TEXT, kontak TEXT, email TEXT, website TEXT, jenis TEXT")
create_table("produk", "id_produk TEXT, barcode TEXT, nama TEXT, kategori TEXT, catatan TEXT, kadaluarsa TEXT, satuan_beli TEXT, satuan_jual TEXT, isi_satuan INTEGER, supplier TEXT, harga_beli INTEGER, harga_modal INTEGER, harga_jual INTEGER, jumlah INTEGER, jumlah_tertinggi INTEGER, stok_minimum INTEGER, poin INTEGER")
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_produk_nama ON produk(nama)")
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_produk_barcode ON produk(barcode)")
create_table("riwayat", "waktu TEXT, aksi TEXT, nama TEXT, nama_lama TEXT, jumlah INTEGER, jumlah_lama INTEGER, modal_lama INTEGER, harga_modal INTEGER, jual_lama INTEGER, harga_jual INTEGER, catatan_lama TEXT, catatan TEXT, stok_terbaru INTEGER, barcode TEXT, operator TEXT, sumber TEXT")
create_table("margin", "kategori TEXT, margin INTEGER")
create_table("produk_diskon", "barcode TEXT, nama TEXT, harga_jual INTEGER, persen INTEGER, min INTEGER")
create_table("keuangan", "pemasukan INTEGER DEFAULT 0, keuntungan INTEGER DEFAULT 0, total_pengeluaran INTEGER DEFAULT 0, saldo INTEGER DEFAULT 0")
cursor.execute("SELECT COUNT(*) FROM keuangan")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO keuangan DEFAULT VALUES")
create_table("operator", "nama TEXT, status TEXT, inisial_code TEXT")   
create_table("user", "nama TEXT, status TEXT, inisial TEXT, inisial_code TEXT, password TEXT, pertanyaan TEXT, jawaban TEXT")
create_table("device", "id_device TEXT")
create_table("customer", "id_user TEXT, nama TEXT, alamat TEXT, kontak TEXT, email TEXT, id_device TEXT, status_login INTEGER, password TEXT, poin INTEGER")
create_table("supplier", "nama TEXT, alamat TEXT, kontak TEXT, email TEXT, medsos TEXT, bidang TEXT")
create_table("pajak", "persen INTEGER, aktif INTEGER DEFAULT 0")
cursor.execute("SELECT COUNT(*) FROM pajak")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO pajak DEFAULT VALUES")   
create_table("riwayat_pajak", "waktu TEXT, nama TEXT, pajak INTEGER")
create_table("riwayat_penjualan_campuran", "waktu TEXT, total REAL, total_laba REAL, no_trans TEXT, operator TEXT, sumber TEXT, pembeli TEXT, bayar REAL, kembali REAL, data_belanja TEXT, kena_pajak REAL, status_pajak INTEGER")
create_table("media_bayar", "bank TEXT, nama_pemilik TEXT, nomor_rekening TEXT")
create_table("cadangan_keranjang", "no TEXT, nama_pembeli TEXT, jumlah_dibayar INTEGER, status TEXT, keranjang TEXT")
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_no ON cadangan_keranjang(no)")

create_table("hak_akses", "status TEXT, izin TEXT")
create_table("status_qr", "status INTEGER, tipe TEXT")
create_table("riwayat_login", "id_pengenal TEXT, nama TEXT, inisial_code TEXT, waktu TEXT, device TEXT, login_menggunakan TEXT, kesalahan_login INTEGER, waktu_logout TEXT")
create_table("shift", "id_shift TEXT, nama_shift TEXT, anggota TEXT, waktu_mulai TEXT, waktu_selesai TEXT")
create_table("produk_tingkat", "barcode TEXT, nama TEXT, satuan TEXT, minimum_qty INTEGER, harga_jual REAL, harga_modal REAL, stok INTEGER, poin INTEGER, kategori TEXT, kadaluarsa TEXT")
create_table("tingkat_a", "id_produk TEXT, barcode TEXT, nama TEXT, harga_modal REAL, harga_jual REAL, min_beli INTEGER")
create_table("tingkat_b", "id_produk TEXT, barcode TEXT, nama TEXT, harga_modal REAL, harga_jual REAL, min_beli INTEGER")
create_table("validasi_owner", "status INTEGER")
create_table("pengaturan_nota", "judul TEXT, catatan TEXT, penerima TEXT, penerbit TEXT")
create_table("riwayat_retur", "waktu TEXT, no_trans TEXT, pembeli TEXT, data TEXT, alasan TEXT")
create_table("pengaturan_format", "bahasa TEXT, format_uang TEXT, format_waktu TEXT")
create_table("riwayat_keuangan", "waktu TEXT, jumlah REAL, sumber TEXT, jenis TEXT, saldo_awal REAL, saldo_akhir REAL, pihak_terkait TEXT, keterangan TEXT, id_keuangan TEXT")
create_table("permintaan", "waktu TEXT, jenis TEXT, data TEXT, status TEXT, oleh TEXT")
create_table("permintaan_pendaftaran_user", "waktu TEXT, ip TEXT, data TEXT")

conn.commit()

#GET

#======================================
def is_valid_table(conn, table):
	cursor = conn.cursor()
	cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table, ))
	return cursor.fetchone() is not None
	
def translator(table):
	conn = None
	try:
		conn = sqlite3.connect(path_database())
		if not is_valid_table(conn, table):
			return {"status": "Gagal", "data": "Link Anda tidak valid"}, 400
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute(f"SELECT * FROM {table}")
		rows = cursor.fetchall()
		data = [dict(row) for row in rows]
		return {"status": "OK", "data": data}, 200
	except sqlite3.Error as e:
		return {"status": "Error", "data": []}, 500
	except Exception as e:
		return {"status": "Error", "data": []}, 500
	finally:
		if conn:
			conn.close()

@app.route("/lihat_data/<table>", methods=["GET"])
def lihat_data(table):
	hasil, status_code = translator(table)
	if table.lower() in ["permintaan", "riwayat_penjualan_campuran"]:
		return jsonify(sorted(hasil["data"], key=lambda x: parse_date(x["waktu"]), reverse=True)), status_code 
	return jsonify(hasil["data"]), status_code
	
#======================================
def get_paths(folder):
    paths = []
    for p in os.listdir(folder):
    	path = os.path.join(folder, p)
    	if os.path.isfile(path):
    		paths.append(path)
    	elif os.path.isdir(path):
    		if os.path.basename(path) != "Folder backup":
	    		paths.extend(get_paths(path))
    return paths
    
def get_folders(main_folder):
    paths = []
    for p in os.listdir(main_folder):
    	pt = os.path.join(main_folder, p)
    	if os.path.isdir(pt):
    		paths.append(pt)
    		paths.extend(get_folders(pt))
    return paths
    
    
    

#-----/ BAGIAN HTML /------#

default_url = "http://127.0.0.1:5000"

def get_link():
	global default_url
	link, _ = get_tunnel()
	if link:
		default_url = link

@app.route("/send_link", methods=["GET"])		
def send_link():
	return default_url

@app.route("/<path:filename>")
def file(filename):
	return send_from_directory(folder_atribut, filename)
	
@app.route("/")
def index():
	path_file = os.path.join(folder_html, "Customer2.html")
	return send_file(path_file)
	
@app.route("/login_user")
def login_user():
	path_file = os.path.join(folder_html, "Login.html")
	return send_file(path_file)
	
@app.route("/dashboard_admin")
def dashboard_admin():
	path_file = os.path.join(folder_html, "proyek_fixed.html")
	return send_file(path_file)

#------------------------------#

	    
	    	   
#---------- PEMROSES DATA KERANJANG -----------#

def get_db():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	return conn

def get_pajak_config(conn):
	row = conn.execute("SELECT persen, aktif FROM pajak LIMIT 1").fetchone()
	return row["aktif"], row["persen"]

def kena_pajak(harga, status_pajak, persen_pajak):
	if status_pajak == 1:
		return harga * (1 + persen_pajak / 100)
	return harga

def hitung_potongan_tingkat(harga, qty, promo, status_pajak, persen_pajak):
	if status_pajak == 1:
		return (harga * qty - promo) * (1 + persen_pajak / 100)
	return harga * qty - promo

@app.route("/tambahkan_second_keranjang", methods=["POST"])
def tambahkan_second_keranjang():
	keranjang = request.get_json()
	if not isinstance(keranjang, list):
		return jsonify({"stat": "Gagal", "pesan": "Format data tidak valid"}), 400

	conn = get_db()
	status_pajak, persen_pajak = get_pajak_config(conn)
	second_keranjang = []
	
	for item in keranjang:
		id_produk = item.get("id")
		qty_sisa = item.get("qty", 0)
		nama = item.get("nama", "")
		barcode = item.get("barcode", "")
		harga = item.get("harga", 0)

		find_b = conn.execute(
			"SELECT * FROM tingkat_b WHERE id_produk = ? AND min_beli <= ? LIMIT 1",
			(id_produk, qty_sisa)
		).fetchone()

		if find_b:
			qty_b = qty_sisa // find_b["min_beli"]
			qty_sisa %= find_b["min_beli"]
			harga_satuan = kena_pajak(find_b["harga_jual"], status_pajak, persen_pajak)
			subtotal_modal = find_b["harga_modal"] * qty_b

			second_keranjang.append({
				"id": id_produk,
				"nama": f'{find_b["nama"]} x{find_b["min_beli"]}',
				"barcode": find_b["barcode"],
				"qty": qty_b,
				"qty_asli": qty_b * find_b["min_beli"],
				"harga_jual": round(harga_satuan),
				"subtotal_jual": round(harga_satuan * qty_b),
				"harga_modal": round(find_b["harga_modal"]),
				"subtotal_modal": round(subtotal_modal),
				"laba": round((find_b["harga_jual"] * qty_b) - subtotal_modal),
				"harga_asli": round(harga),
				"potongan_tingkat": round(hitung_potongan_tingkat(harga, find_b["min_beli"], find_b["harga_jual"], status_pajak, persen_pajak) * qty_b),
				"potongan_diskon": round(0),
				"min_diskon": "",
				"min_tingkat": find_b["min_beli"],
				"tipe_promo": "tingkat",
				"persen_pajak": persen_pajak
			})

		find_a = conn.execute(
			"SELECT * FROM tingkat_a WHERE id_produk = ? AND min_beli <= ? LIMIT 1",
			(id_produk, qty_sisa)
		).fetchone()

		if find_a:
			qty_a = qty_sisa // find_a["min_beli"]
			qty_sisa %= find_a["min_beli"]
			harga_satuan = kena_pajak(find_a["harga_jual"], status_pajak, persen_pajak)
			subtotal_modal = find_a["harga_modal"] * qty_a

			second_keranjang.append({
				"id": id_produk,
				"nama": f'{find_a["nama"]} x{find_a["min_beli"]}',
				"barcode": find_a["barcode"],
				"qty": qty_a,
				"qty_asli": qty_a * find_a["min_beli"],
				"harga_jual": round(harga_satuan),
				"subtotal_jual": round(harga_satuan * qty_a),
				"harga_modal": round(find_a["harga_modal"]),
				"subtotal_modal": round(subtotal_modal),
				"laba": round((find_a["harga_jual"] * qty_a) - subtotal_modal),
				"harga_asli": round(harga),
				"potongan_tingkat": round(hitung_potongan_tingkat(harga, find_a["min_beli"], find_a["harga_jual"], status_pajak, persen_pajak) * qty_a),
				"potongan_diskon": round(0),
				"min_diskon": "",
				"min_tingkat": find_a["min_beli"],
				"tipe_promo": "tingkat",
				"persen_pajak": persen_pajak
			})

		if qty_sisa > 0:
			produk_row = conn.execute(
				"SELECT * FROM produk WHERE id_produk = ?", (id_produk,)
			).fetchone()
			harga_modal = produk_row["harga_modal"] if produk_row else 0
			subtotal_modal = harga_modal * qty_sisa

			find_diskon = conn.execute(
				"""SELECT * FROM produk_diskon
				   WHERE LOWER(nama) = LOWER(?) AND barcode = ? AND min <= ?
				   LIMIT 1""",
				(nama, barcode, qty_sisa)
			).fetchone()

			if find_diskon:
				harga_setelah_diskon = find_diskon["harga_jual"] * (1 - find_diskon["persen"] / 100)
				harga_jual = kena_pajak(harga_setelah_diskon, status_pajak, persen_pajak)

				second_keranjang.append({
					"id": id_produk,
					"nama": nama,
					"barcode": barcode,
					"qty": qty_sisa,
					"qty_asli": qty_sisa,
					"harga_jual": round(harga_jual),
					"subtotal_jual": round(harga_jual * qty_sisa),
					"harga_modal": round(harga_modal),
					"subtotal_modal": round(subtotal_modal),
					"laba": round((harga_jual * qty_sisa) - subtotal_modal),
					"harga_asli": round(harga),
					"potongan_tingkat": round(0),
					"potongan_diskon": round((find_diskon["harga_jual"] - harga_setelah_diskon) * qty_sisa),
					"min_diskon": find_diskon["min"],
					"min_tingkat": "",
					"tipe_promo": "diskon",
					"persen_pajak": persen_pajak
				})
			else:
				harga_jual = kena_pajak(harga, status_pajak, persen_pajak)

				second_keranjang.append({
					"id": id_produk,
					"nama": nama,
					"barcode": barcode,
					"qty": qty_sisa,
					"qty_asli": qty_sisa,
					"harga_jual": round(harga_jual),
					"subtotal_jual": round(harga_jual * qty_sisa),
					"harga_modal": round(harga_modal),
					"subtotal_modal": round(subtotal_modal),
					"laba": round((harga * qty_sisa) - subtotal_modal),
					"harga_asli": round(harga),
					"potongan_tingkat": round(0),
					"potongan_diskon": round(0),
					"min_diskon": "",
					"min_tingkat": "",
					"tipe_promo": "",
					"persen_pajak": persen_pajak
				})
				
	total = sum(p["subtotal_jual"] for p in second_keranjang)
	conn.close()

	return jsonify({
		"total": round(total),
		"data": second_keranjang
	})
	
#-------------- END -----------------#


@app.route("/get_time", methods=["GET"])
def get_time():
	return jsonify({
		"waktu": now_str()
	})
	
@app.route("/get_all_pictures/<file_sent>", methods=["GET"])
def get_all_pictures(file_sent):
	file_info = json.loads(file_sent)
	if not file_info:
		return "File kosong", 400
	fold = file_info.get("folder","")
	filename = file_info.get("file","")
	age = file_info.get("age", 0)
	
	if not filename:
		return "File kosong", 400
	if not fold:
		return "folder kosong", 400
				
	folder_real = map_folder.get(fold, None)
	if not folder_real:
		return "Folder tidak ditemukan", 400
	if filename in os.listdir(folder_real):
		return send_from_directory(folder_real, filename, max_age=age)
	return send_from_directory(folder_atribut, "noimage.png")
		
@app.route("/lihat_gambar_rekening", methods=["GET"])
def lihat_gambar_rekening(): #dijadwalkan
	name = request.args.get("name")
	file_path = os.path.join(folder_pembayaran, name)
	if not os.path.exists(file_path):
		return "Kosong", 404
	return send_file(file_path, mimetype="image/jpeg")
										
@app.route("/generate_number", methods=["GET"])
def generate_number():
	alpha = random.choice(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"])
	low = random.choice(["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"])
	num = random.choice(["1","2","3","4","5","6","7","8","9","0"])
	number = alpha + low + num + "_" + datetime.now().strftime("%S")
	return jsonify({"time": number}), 200
	
@app.route("/download_foto_profil", methods=["GET"])
def download_foto_profil():
	file_path = os.path.join(folder_foto, "foto profil.png")
	if not os.path.exists(file_path):
		return send_from_directory(folder_atribut, "default_wallpaper.png", max_age=3600)
	return send_from_directory(folder_foto, "foto profil.png", max_age=86400)
	
@app.route("/ambil_struk/<struk>")
def ambil_struk(struk):
	filepath = os.path.join(folder_struk, f"{struk}.txt")
	return send_file(filepath, as_attachment=True)
	
@app.route("/ambil_gambar_qr", methods=["GET"])
def ambil_gambar_qr(): #dijadwalkan
	nama = request.args.get("nama", "")
	id = request.args.get("id", "")
	nama_gambar = f"{nama} {id}.jpeg"
	path = os.path.join(folder_foto, nama_gambar)
	if not os.path.exists(path):
		return "Kosong", 400
	return send_from_directory(path, nama_gambar, max_age=86400)

@app.route("/ambil_gambar_katalog", methods=["GET"])
def ambil_gambar_katalog():
	with zipfile.ZipFile("gambar_katalog.zip", "w") as z:
		file_list = os.listdir(folder_katalog)
		if not file_list:
			return "Tidak ada gambar", 404
			
		for file in file_list:
			if file.lower().endswith((".jpeg", ".jpg", ".png")):
				file_path = os.path.join(folder_katalog, file)
				if os.path.isfile(file_path):
					z.write(file_path, file)
	return send_file("gambar_katalog.zip", as_attachment=True)

@app.route("/lihat_backup", methods=["GET"])
def lihat_backup():
	if os.path.isdir(folder_backup):
		semua_item = os.listdir(folder_backup)
		daftar_file = []
		for item in semua_item:
			item_lengkap = os.path.join(folder_backup, item)
			if os.path.isfile(item_lengkap):
				daftar_file.append(item)
		return jsonify(daftar_file)
	else:
		return "Folder tidak ditemukan", 401

@app.route("/see_main_database", methods=["GET"])
def see_main_database():
	if os.path.isdir(basedir):
		folder = os.listdir(basedir)
		daftar_folder = []
		for f in folder:
			daftar_folder.append(f)
		
		list_folder_and_files = []	
		for p in daftar_folder:
			item_path = os.path.join(basedir, p)
			if os.path.isdir(item_path):
				all_files = os.listdir(item_path)
				list_folder_and_files.append({
					"folder": p,
					"files": all_files,
				})

		return jsonify({"folder": daftar_folder, "folder_and_file": list_folder_and_files})
	else:
		return "Not found", 400
	
@app.route("/lihat_izin_desimal", methods=["GET"])
def lihat_izin_desimal():
	return jsonify(desimal)
	
@app.route("/get_all_paths", methods=["GET"])
def get_all_paths():
	path = get_paths(basedir)
	return jsonify(path)

@app.route("/get_path_folders", methods=["GET"])
def get_path_folders():
	path = get_folders(basedir)
	return jsonify(path)
		
@app.route("/ambil_info_backup", methods=["GET"])
def ambil_info_backup():
	folders = []
	for p in os.listdir(folder_backup):
		path = os.path.join(folder_backup, p)
		if os.path.isdir(path):
			folders.append(path)
	return jsonify(folders)

@app.route("/get_riwayat_filter/<aspek>", methods=["GET"])
def get_riwayat_filter(aspek):
	aspek = json.loads(aspek)
	periode = aspek.get("periode", "semua periode").lower().replace(" ", "_")
	operator = aspek.get("operator", "semua operator").lower()
	
	data, _ = translator("riwayat_penjualan_campuran")
	data = data["data"]
	if isinstance(data, list):
		filtered = data
		if periode != "semua_periode":
			start, end = map_periode[periode]()
			filtered = [p for p in data if start <= parse_date(p["waktu"]) <= end]
			
		opr_filter = []
		if operator == "semua operator":
			opr_filter = filtered
		else:
			opr_filter = [p for p in filtered if p["operator"].lower() == operator]
		return jsonify(sorted(opr_filter, key=lambda x: parse_date(x["waktu"]), reverse=True))
	return jsonify([])	
	
@app.route("/get_data_sold_out_today/<period>", methods=["GET"])
def get_data_sold_out_today(period):
	data, status = translator("riwayat_penjualan_campuran")
	data = data["data"]
	if isinstance(data, list):
		start, end = map_periode[period]()
		data_filtered = [p for p in data if start <= parse_date(p["waktu"]) <= end]
		total, laba = 0, 0
		terjual, dt = 0, []
		for p in data_filtered:
			total += p["total"]
			laba += p["total_laba"]
			krj = json.loads(p["data_belanja"])
			for k in krj:
				terjual += k.get("qty_asli", 0)
				for d in dt:
					if d.get("id_produk", "") == k.get("id", ""):
						d["terjual"] += int(k.get("qty_asli", 0))
						d["total"] += round(k.get("subtotal_jual", 0))
						d["laba"] += round(k.get("laba", 0))
						break
				else:
					dt.append({
						"id_produk": k.get("id", ""),
						"nama": k.get("nama", ""),
						"terjual": int(k.get("qty_asli", 0)),
						"total": round(k.get("subtotal_jual", 0)),
						"laba": round(k.get("laba", 0))
					})
		return jsonify({
			"total": round(total),
			"laba": round(laba),
			"terjual": int(terjual),
			"data": sorted(dt, key=lambda x: x["terjual"], reverse=True)
		})
	return jsonify({})
	
@app.route("/lihat_validasi_login", methods=["GET"])
def lihat_validasi_login():
	return jsonify(ses)
	
@app.route("/download_nota/<nama>")
def download_nota(nama):
	path = os.path.join(folder_nota, nama)
	if not os.path.exists(path):
		return "Kosong", 400
	return send_file(path, as_attachment=True)
	
@app.route("/get_files/<folder>", methods=["GET"])
def get_files(folder):
	map_group = {
		"folder_foto": folder_foto,
		"folder_struk": folder_struk,
		"folder_katalog": folder_katalog
	}
	fold = map_group.get(folder, None)
	if fold is None:
		return jsonify({}), 400
	os.makedirs(fold, exist_ok=True)
	files = []
	for p in os.listdir(fold):
		path = os.path.join(fold, p)
		if os.path.isfile(path):
			files.append(path)
	return jsonify(files), 200
	
@app.route("/permintaan_pendaftaran_user", methods=["GET"])
def permintaan_pendaftaran_user():
	conn = None
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		
		cursor.execute("SELECT * FROM permintaan_pendaftaran_user")
		dtt = cursor.fetchall()
		
		data = [dict(row) for row in dtt]
		dt = []
		for item in data:
			dict_save = {}
			
			for key, value in json.loads(item.get("data","")).items():
				if key.lower() in ["password", "konf", "answer"]:
					dict_save[key] = "*" * 10 if value else ""
				else:
					dict_save[key] = value
			dt.append({
				"id": item.get("id",""),
				"ip": item.get("ip",""),
				"waktu": item.get("waktu",""),
				"data": json.dumps(dict_save)
			})
		return jsonify(dt)
	except Exception as e:
		print(e)
		return []
	finally:
		if conn:
			conn.close()
	
#POST
allowed_methods = [
	"edit_rekening",
	"hapus_rekening",
	"reupload_qr",
	"hapus_anggota_shift",
	"hapus_seluruh_shift",
	"hapus_shift_tertentu",
	"edit_customer",
	"edit_supplier",
	"hapus_customer",
	"hapus_supplier",
	"tambah_supplier",
	"tambah_customer",
	"hapus_seluruh",
	"proses_retur",
	"tambah_pengeluaran",
	"edit_pengeluaran",
	"hapus_pengeluaran",
	"tambah_stok",
	"edit_produk",
	"tambah_produk_diskon",
	"upload_foto_katalog",
	"tambah_tingkat_produk",
	"tambah_user_baru",
	"tambah_profil",
	"hapus_profil",
	"edit_user",
	"hapus_user",
	"hapus_foto",
	"ganti_nama_file",
	"validasi_login",
	"validasi_signup",
	"hapus_permintaan_user",
	"approve_new_user",
	"hapus_seluruh_permintaan_daftar",
	"pajak_selalu_aktif",
	"cetak_qr_di_struk",
	"hapus_produk_diskon",
	"hapus_produk_tingkat",
	"tambah_produk_baru",
	"pajak_persen",
	"simpan_keranjang",
	"ganti_status_cadangan",
	"generate_barcode"
]

def convert_to_jpeg(picture=None):
	if picture is None:
		return None
	img = Image.open(picture.stream)
	img = ImageOps.exif_transpose(img)
	if img.mode in ("RGBA", "P"):
		img = img.convert("RGB")
	output = BytesIO()
	img.save(output, format="JPEG", quality=85, optimize=True)
	output.seek(0)
	return output

class PostData:
	def __init__(self, data):
		self.data = data
		self.conn = sqlite3.connect(path_database())
		self.conn.row_factory = sqlite3.Row
		self.cursor = self.conn.cursor()
		
	def generate_barcode(self):
		data = self.data
		try:
			nama = data.get("nama","").split()
			teks_barcode = nama[0] + datetime.now().strftime("%f")
			
			self.cursor.execute("UPDATE produk SET barcode = ? WHERE id_produk = ?", (teks_barcode, data.get("id", "")))
			self.conn.commit()
		
			barcode_type = "code128"
			filename = data.get("nama", "")
			barcode_class = barcode.get(barcode_type, teks_barcode, writer=ImageWriter())
			filepath = os.path.join(folder_foto, filename)
			barcode_class.save(filepath)
			file_return = os.path.join(folder_foto, filename + ".png")
			return send_file(file_return, mimetype="image/png"), 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": "Terjadi kesalahan " + str(e)
			}, 500
	
	def ganti_status_cadangan(self):
		try:
			self.cursor.execute("UPDATE cadangan_keranjang SET status = ? WHERE no = ?", (self.data.get("status", "Sudah dilunasi"),self.data.get("no","")))
			self.conn.commit()
			return {}, 200
		except Exception:
			self.conn.rollback()
			return {}, 500
			
	def simpan_keranjang(self):
		d = self.data
		keranjang = d.get("dt","")
		if not isinstance(keranjang, list):
			return {
				"stat": "Gagal",
				"pesan": "Format data keranjang tidak valid"
			}, 400
			
		if not isinstance(keranjang, str):
			keranjang = json.dumps(keranjang)
		try:
			self.cursor.execute("""
				INSERT INTO cadangan_keranjang (
					no,
					nama_pembeli,
					jumlah_dibayar,
					status,
					keranjang
				) VALUES (?, ?, ?, ?, ?)
				ON CONFLICT(no) DO UPDATE SET
					jumlah_dibayar = excluded.jumlah_dibayar,
					keranjang = excluded.keranjang
				""",
				(
					d.get("no",""),
					d.get("nama",""),
					d.get("dibayar",0),
					d.get("status",""),
					keranjang
				)
			)
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": f"Data keranjang atas nama {d.get('nama','')} telah disimpan"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan.\n{e}"
			}, 500
					
	def pajak_persen(self):
		d = self.data
		try:
			self.cursor.execute("INSERT INTO pajak (id, persen) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET persen = excluded.persen", (1, d.get("persen",0)))
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": f"Persentase PPN telah diperbarui dengan {d.get('persen',0)}%"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan. {e}"
			}, 500
			
	def tambah_produk_baru(self):
		d = self.data
		try:
			kadaluarsa = d.get("kadaluarsa","")
			exp = datetime.strptime(kadaluarsa, "%Y-%m-%d").strftime("%m/%d/%y")
			
			self.cursor.execute("""
				INSERT INTO produk (
				id_produk,
				barcode,
				nama,
				kategori,
				catatan,
				kadaluarsa,
				satuan_beli,
				satuan_jual,
				isi_satuan,
				supplier,
				harga_beli,
				harga_modal,
				harga_jual,
				jumlah,
				jumlah_tertinggi,
				stok_minimum,
				poin
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
				(
					datetime.now().strftime("%f"),
					d.get("barcode",""),
					d.get("nama",""),
					d.get("kategori",""),
					d.get("catatan",""),
					exp,
					d.get("satuan_beli",""),
					d.get("satuan_jual",""),
					d.get("isi_satuan",0),
					d.get("supplier",""),
					d.get("harga_beli",0),
					d.get("harga_modal",0),
					d.get("harga_jual",0),
					d.get("jumlah",0),
					d.get("jumlah",0),
					d.get("stok_minimum",0),
					d.get("poin",0)
				)
			)
			kategori = d.get("kategori", "")
			self.cursor.execute("""
				INSERT INTO margin (kategori, margin)
				SELECT ?, 0 WHERE NOT EXISTS (SELECT 1 FROM margin WHERE kategori = ?)
			""", (kategori, kategori))

			supplier = d.get("supplier", "")
			self.cursor.execute("""
				INSERT INTO supplier (nama)
				SELECT ? WHERE NOT EXISTS (SELECT 1 FROM supplier WHERE nama = ?)
			""", (supplier, supplier))
			
			self.cursor.execute("""
				INSERT INTO riwayat (
				waktu,
				aksi,
				nama,
				barcode,
				jumlah,
				operator,
				sumber) VALUES (?, ?, ?, ?, ?, ?, ?)""",
				(
					now_str(),
					"Tambah produk baru",
					d.get("nama",""),
					d.get("barcode",""),
					d.get("jumlah",0),
					d.get("operator",""),
					d.get("sumber","")
				)
			)
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": f"Produk baru {d.get('nama','')} telah disimpan"
			}, 200
		
		except sqlite3.IntegrityError:
			self.conn.rollback()
			return {
				"stat": "Gagal",
				"pesan": "Terdeteksi duplikasi nama atau barcode produk."
			}, 400
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan. {e}"
			}, 500
								
	def hapus_produk_tingkat(self):
		d = self.data
		try:
			self.cursor.execute(f"DELETE FROM {d.get('path','')} WHERE id_produk = ?", (d.get("id",""),))
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": f"Produk telah dihapus dari {d.get('path','').replace('_', ' ')}"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": str(e)
			}, 500
			
	def hapus_produk_diskon(self):
		try:
			self.cursor.execute("DELETE FROM produk_diskon WHERE id = ?", (self.data.get("id",0), ))
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": "Produk telah dihapus dari daftar produk diskon"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan. {e}"
			}, 500
				
	def cetak_qr_di_struk(self):
		try:
			self.cursor.execute(
				"INSERT INTO status_qr(id, status) VALUES(?, ?) ON CONFLICT(id) DO UPDATE SET status = excluded.status",
				(1, self.data.get("status",0))
			)
			self.conn.commit()
			return {
				"stat": "",
				"pesan": ""
			}, 200
		except Exception:
			self.conn.rollback()
			return {
				"stat": "",
				"pesan": ""
			}, 500
		
	def pajak_selalu_aktif(self):
		try:
			self.cursor.execute(
				"INSERT INTO pajak(id, aktif) VALUES(?, ?) ON CONFLICT(id) DO UPDATE SET aktif = excluded.aktif",
				(1, self.data.get("aktif",0))
			)
			self.conn.commit()
			return {
				"stat": "",
				"pesan": ""
			}, 200
		except Exception:
			self.conn.rollback()
			return {
				"stat": "",
				"pesan": ""
			}, 500				
	
	def hapus_seluruh_permintaan_daftar(self):
		try:
			self.cursor.execute("DELETE FROM permintaan_pendaftaran_user")
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": "Permintaan pendaftaran pengguna telah dihapus"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Gagal",
				"pesan": f"Terjadi kesalahan saat menghapus data.\n{e}"
			}, 500
	
	def validasi_signup(self):
		d = self.data
		ip = get_real_ip()
		result, sisa = cek_ip_register(ip)
		if result:
			return {
				"stat": "Gagal",
				"pesan": f"Pendaftaran ditolak. Silahkan mendaftar kembali dalam {sisa} detik"
			}, 400
		try:
			self.cursor.execute("SELECT * FROM user")
			user = self.cursor.fetchall()
			if not user:
				if d.get("status","").lower() != "owner":
					tambah_poin(ip, "fail")
					return {
						"stat": "Gagal",
						"pesan": "Anda adalah pendaftar pertama. Silahkan pastikan Anda memasukkan status sebagai owner"
					}, 400
				if d.get("password","") != d.get("konf",""):
					tambah_poin(ip, "fail")
					return {
						"stat": "Gagal",
						"pesan": "Password dan konfirmasi password harus sama"
					}, 400
				first_name = d.get("nama","").split()[0]
				inisial = first_name[0]
				inisial_code = datetime.now().strftime(f"{inisial}%S_%f")
				self.cursor.execute("""INSERT INTO user (
					inisial,
					inisial_code,
					jawaban,
					nama,
					password,
					pertanyaan,
					status
					) VALUES (?, ?, ?, ?, ?, ?, ?)""",
					(
						inisial,
						inisial_code,
						pbkdf2_sha256.hash(d.get("answer","")),
						d.get("nama",""),
						pbkdf2_sha256.hash(d.get("password","")),
						d.get("question",""),
						d.get("status","")
					)
				)
				self.conn.commit()
				tambah_poin(ip, "success")
				return {
					"stat": "Berhasil",
					"pesan": f"Pendaftaran berhasil. Selamat datang {d.get('nama','')}"
				}, 200
			else:
				self.cursor.execute("""INSERT INTO permintaan_pendaftaran_user (
					waktu,
					ip,
					data
					) VALUES (?, ?, ?)""",
					(
						now_str(),
						ip,
						json.dumps(d)
					)
				)
				self.conn.commit()
				tambah_poin(ip, "success")
				return {
					"stat": "Berhasil",
					"pesan": "Pendaftaran berhasil. Data Anda telah disimpan dan dalam tahap peninjauan"
				}, 200
		except Exception as e:
			tambah_poin(ip, "fail")
			self.conn.rollback()
			return {
				"stat": "Gagal",
				"pesan": f"Terjadi kesalahan. {e}"
			}, 500
				
	def validasi_kredensial_login(self, username, password, idev):
		try:
			self.cursor.execute("SELECT password, nama, inisial_code FROM user WHERE inisial_code = ? OR nama = ?", (username,username))
			pw = self.cursor.fetchone()
			if not pw:
				return False, None
			if pbkdf2_sha256.verify(password, pw["password"]):
				for p in ses:
					if p.get("idDevice", "").lower() == idev.lower():
						p["pengguna"] = pw["nama"]
						p["inisial_code"] = pw["inisial_code"]
						p["login"] = 1
						break
				else:
					ses.append({
						"login": 1,
						"pengguna": pw["nama"],
						"inisial_code": pw["inisial_code"],
						"idDevice": idev
					})
				return True, pw["nama"]
			return False, None
		except Exception as e:
			print(e)
			return False, None
	
	def validasi_login(self):
		d = self.data
		ip = get_real_ip()
		blocked, sisa = cek_blokir(ip)
		if blocked:
			return {
				"stat": "Gagal",
				"pesan": f"Login ditolak. Silahkan login kembali dalam {sisa} detik."
			}, 400
		validasi, nama = self.validasi_kredensial_login(d.get("username",""), d.get("password",""), d.get("id",""))
		if validasi:
			reset_percobaan(ip)
			return {
				"stat": "Berhasil",
				"pesan": f"Login berhasil.\nSelamat datang kembali {nama}"
			}, 200
		else:
			catat_gagal_login(ip)
			return {
				"stat": "Gagal",
				"pesan": "Login gagal. Username atau password salah"
			}, 400
		
	def ganti_nama_file(self):
		d = self.data
		path_lama = d.get("path_lama","")
		nama_baru = d.get("nama_baru","").strip()
		ekstensi = d.get("ekstensi","").strip()
		nama_for_rename = nama_baru + ekstensi
		
		if os.path.exists(path_lama):
			old_path = Path(path_lama)
			old_path.rename(old_path.with_name(nama_for_rename))
			return {
				"stat": "Berhasil",
				"pesan": f"File {nama_for_rename} telah disimpan"
			}, 200
		return {
			"stat": "Gagal",
			"pesan": "File tidak ditemukan"
		}, 400
			
	def hapus_foto(self):
		path = self.data.get("path","")
		if os.path.exists(path):
			os.remove(path)
			return {
				"stat": "Berhasil",
				"pesan": "Foto telah dihapus"
			}, 200
		return {
			"stat": "Gagal",
			"pesan": "File tidak ditemukan"
		}, 400
					
	def hapus_user(self):
		d = self.data
		try:
			self.cursor.execute("DELETE FROM user WHERE inisial_code = ?", (d.get("id",""),))
			self.conn.commit()
			nama_qr = d.get("nama","") + " " + d.get("id","") + ".jpeg"
			path = os.path.join(folder_foto, nama_qr)
			if os.path.exists(path):
				os.remove(path)
				return {
					"stat": "Berhasil",
					"pesan": "Data dan gambar QR Code berhasil dihapus"
				}, 200
			else:
				return {
					"stat": "Berhasil",
					"pesan": "Data berhasil dihapus dan gambar QR Code tidak ditemukan"
				}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan saat penghapusan.\n{e}"
			}, 500
		
	def edit_user(self):
		d = self.data
		try:
			self.cursor.execute("""
				UPDATE user SET
				nama = ?,
				status = ?,
				pertanyaan = ?,
				jawaban = ?
				WHERE inisial_code = ?""",
				(
					d.get("nama",""),
					d.get("status",""),
					d.get("pertanyaan",""),
					pbkdf2_sha256.hash(d.get("jawaban","")),
					d.get("id","")
				)
			)
			self.conn.commit()
			nama_lama = d.get("namaLama","") + " " + d.get("id","") + ".jpeg"
			nama_baru = d.get("nama","") + " " + d.get("id","") + ".jpeg"
			path_lama = os.path.join(folder_foto, nama_lama)
			path_baru = os.path.join(folder_foto, nama_baru)
			if os.path.exists(path_lama):
				os.rename(path_lama, path_baru)
				
			return {
				"stat": "Berhasil",
				"pesan": f"Data {d.get('nama','')} telah diperbarui"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan saat update user.\n{e}"
			}, 500
			
	def hapus_profil(self):
		try:
			self.cursor.execute("DELETE FROM profil")
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": "Profil telah dihapus"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan saat menghapus profil.\n{e}"
			}, 500
	
	def tambah_profil(self):
		d = self.data
		try:
			self.cursor.execute("""
				INSERT INTO profil (
					id,
					nama,
					alamat,
					kontak,
					email,
					website,
					jenis
				) VALUES (?, ?, ?, ?, ?, ?, ?)
				ON CONFLICT(id) DO UPDATE SET
					nama = excluded.nama,
					alamat = excluded.alamat,
					kontak = excluded.kontak,
					email = excluded.email,
					website = excluded.website,
					jenis = excluded.jenis
				""",
				(
					1,
					d.get("nama",""),
					d.get("alamat",""),
					d.get("kontak",""),
					d.get("email",""),
					d.get("website",""),
					d.get("jenis","")
				)
			)
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": "Profil toko telah diupdate"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan.\n{e}"
			}, 500
			
	def hapus_permintaan_user(self):
		id = self.data.get("id",0)
		try:
			self.cursor.execute("DELETE FROM permintaan_pendaftaran_user WHERE id = ?", (id,))
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": "Data telah dihapus"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Gagal",
				"pesan": "Terjasi kesalahan saat penghapusan.\n{e}"
			}, 500
	
	def approve_new_user(self):
		self.cursor.execute("SELECT data FROM permintaan_pendaftaran_user WHERE id = ?", (self.data.get("id",0),))	
		data = self.cursor.fetchone()
		dataParse = json.loads(data["data"])
		self.data = dataParse
		return self.tambah_user_baru()
							
	def tambah_user_baru(self):
		d = self.data
		nama = d.get("nama","").split()
		nama_pertama = nama[0]
		inisial_code = nama_pertama[0] + datetime.now().strftime("%S_%f")
		try:
			self.cursor.execute("""
				INSERT INTO user (
					nama,
					status,
					inisial,
					inisial_code,
					password,
					pertanyaan,
					jawaban
				) VALUES (?, ?, ?, ?, ?, ?, ?)""",
				(
					d.get("nama",""),
					d.get("status",""),
					nama_pertama[0],
					inisial_code,
					pbkdf2_sha256.hash(d.get("password","")),
					d.get("question",""),
					pbkdf2_sha256.hash(d.get("answer",""))
				)
			)
			self.cursor.execute("""
				INSERT INTO riwayat (
					waktu,
					aksi,
					nama,
					jumlah,
					barcode,
					operator,
					sumber
				) VALUES (?, ?, ?, ?, ?, ?, ?)""",
				(
					now_str(),
					"Tambah user baru",
					d.get("nama",""),
					1,
					inisial_code,
					d.get("operator",""),
					d.get("sumber","")
				)
			)
			self.conn.commit()
			teks = f"{inisial_code} {d.get('password', '')}"
			qr_teks = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
			qr_teks.add_data(teks)
			qr_teks.make(fit=True)

			img = qr_teks.make_image(fill_color="black", back_color="white")
			path = os.path.join(folder_foto, f"{d.get('nama','')} {inisial_code}.jpeg")
			img.save(path, "jpeg", quality=90, optimize=True)
			return {
				"stat": "Berhasil",
				"pesan": f"Pengguna {d.get('nama','')} telah ditambahkan"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan. {e}"
			}, 500
      
	def upload_foto_katalog(self):
		foto = self.data
		if not foto:
			return {
				"stat": "Gagal",
				"pesan": "Gambar kosong"
			}, 400
	
		nama_file = foto.filename
		if not nama_file:
			return {
				"stat": "Gagal",
				"pesan": "Wajib menambahkan nama file gambar"
			}, 400
	
		os.makedirs(folder_katalog, exist_ok=True)
		jpeg_file = convert_to_jpeg(foto)
	
		base_name = os.path.splitext(nama_file)[0]
		filename = base_name + ".jpeg"
	
		path = os.path.join(folder_katalog, filename)
	
		with open(path, "wb") as f:
			f.write(jpeg_file.read())
	
		jpeg_file.seek(0)
	
		img = Image.open(jpeg_file)
	
		img_thumb = img.resize((300, 300), Image.LANCZOS)
		path_thumb = os.path.join(folder_katalog, base_name + "_thumb.jpeg")
	
		img_thumb.save(path_thumb, "JPEG", quality=85, optimize=True)
	
		return {
			"stat": "Berhasil",
			"pesan": "Gambar telah disimpan"
		}, 200
				
	def tambah_produk_diskon(self):
		data = self.data.get("data",{})
		riwayat = self.data.get("riwayat",{})
		if not all([data, riwayat]):
			return {
				"stat": "Gagal",
				"pesan": "Data kosong"
			}, 400
		try:
			self.cursor.execute("""INSERT OR REPLACE INTO produk_diskon
				(
					barcode,
					nama,
					harga_jual,
					persen,
					min
				) VALUES (?, ?, ?, ?, ?)""",
				(
					data.get("barcode", ""),
					data.get("nama", ""),
					data.get("harga_jual", 0),
					data.get("persen", 0),
					data.get("min", 0)
				)
			)
			self.cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, barcode, jumlah, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)",
				(
					riwayat.get("waktu",""),
					riwayat.get("aksi",""),
					riwayat.get("nama",""),
					riwayat.get("barcode",""),
					riwayat.get("jumlah",0),
					riwayat.get("operator",""),
					riwayat.get("sumber","")
				)
			)
			self.conn.commit()
			
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan saat menambahkan produk diskon:\n{e}"
			}, 500
		return {
			"stat": "Berhasil",
			"pesan": f"Produk {data.get('nama','')} telah ditambahkan dengan diskon {data.get('persen',0)} %"
		}, 200
		
	def tambah_tingkat_produk(self):
		d = self.data
		if not d.get("id_produk",""):
			return {
				"stat": "Gagal",
				"pesan": "Id produk diperlukan untuk menyimpan data"
			}, 400
		path = d.get("path","")
		if not path:
			return {
				"stat": "Gagal",
				"pesan": "Path perlu di isi"
			}, 400
		try:
			self.cursor.execute(f"""INSERT OR REPLACE INTO {path}
				(
					id_produk,
					barcode,
					nama,
					harga_modal,
					harga_jual,
					min_beli
				) VALUES (?, ?, ?, ?, ?, ?)""",
				(
					d.get("id_produk",""),
					d.get("barcode",""),
					d.get("nama",""),
					d.get("harga_modal",0),
					d.get("harga_jual",0),
					d.get("min_beli",0)
				)
			)
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": "Produk telah ditambahkan"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan:\n{e}"
			}, 500
						
	def edit_produk(self):
		d = self.data.get("data",{})
		r = self.data.get("riwayat",{})
		if not d or not r:
			return {
				"stat": "Gagal",
				"pesan": "Data kosong"
			}, 400
		try:
			md = float(d.get("harga_beli", 0)) / int(d.get("isi_satuan", 0))
			self.cursor.execute("""UPDATE produk SET
				barcode = ?,
				nama = ?,
				catatan = ?,
				kategori = ?,
				kadaluarsa = ?,
				satuan_beli = ?,
				satuan_jual = ?,
				isi_satuan = ?,
				harga_beli = ?,
				harga_jual = ?,
				jumlah = ?,
				stok_minimum = ?,
				supplier = ?,
				jumlah_tertinggi = ?,
				harga_modal = ?,
				poin = ?
				WHERE id = ?""",
				(
					d.get("barcode", ""),
					d.get("nama", ""),
					d.get("catatan", ""),
					d.get("kategori", ""),
					d.get("kadaluarsa", ""),
					d.get("satuan_beli", ""),
					d.get("satuan_jual", ""),
					d.get("isi_satuan", 0),
					d.get("harga_beli", 0),
					d.get("harga_jual", 0),
					d.get("jumlah", 0),
					d.get("stok_minimum", 0),
					d.get("supplier", ""),
					d.get("jumlah_tertinggi", 0),
					md,
					d.get("poin", 0),
					d.get("id", "")
				)
			)
			self.cursor.execute("""INSERT INTO riwayat
				(
					waktu,
					aksi,
					nama_lama,
					nama,
					jumlah_lama,
					jumlah,
					modal_lama,
					harga_modal,
					jual_lama,
					harga_jual,
					catatan_lama,
					catatan,
					barcode,
					operator,
					sumber
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
				(
					r.get("waktu", ""),
					r.get("aksi", ""),
					r.get("nama_lama", ""),
					r.get("nama", ""),
					r.get("jumlah_lama", 0),
					r.get("jumlah", 0),
					r.get("modal_lama", 0),
					r.get("harga_modal", 0),
					r.get("jual_lama", 0),
					r.get("harga_jual", 0),
					r.get("catatan_lama", ""),
					r.get("catatan", ""),
					r.get("barcode", ""),
					r.get("operator", ""),
					r.get("sumber", "")
				)
			)
			self.conn.commit()
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan saat edit data:\n{e}"
			}, 500
		return {
			"stat": "Berhasil",
			"pesan": f"Data produk {r.get('nama_lama','')} telah diperbarui"
		}, 200
		
	def tambah_stok(self):
		d = self.data
		data = d.get("data_tambah", {})
		r = d.get("riwayat",{})
		id_produk = data.get("id_produk","")
		if not id_produk:
			return {
				"stat": "Gagal",
				"pesan": "Id diperlukan untuk tambah stok produk"
			}, 400
		try:
			self.cursor.execute("UPDATE produk SET jumlah = jumlah + ?, jumlah_tertinggi = ? WHERE id_produk = ?",
				(
					data.get("tambahan",0),
					data.get("jumlah_tertinggi",0),
					data.get("id_produk","")
				)
			)
			self.cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, stok_terbaru, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
				(
					r.get("waktu", now_str()),
					r.get("aksi", ""),
					r.get("nama", ""),
					r.get("jumlah", 0),
					r.get("barcode", ""),
					r.get("stok_terbaru", 0),
					r.get("operator", ""),
					r.get("sumber", "")
				)
			)
			self.conn.commit()
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kegagalan saat menambah stok: {e}"
			}, 500
		return {
			"stat": "Berhasil",
			"pesan": f"Stok produk {r.get('nama','')} berhasil ditambahkan sebanyak {data.get('tambahan',0)} unit.\n Stok saat ini: {r.get('stok_terbaru',0)} unit"
		}, 200
			
	def edit_rekening(self):
		d = self.data
		self.cursor.execute("SELECT nama_pemilik, bank FROM media_bayar WHERE id = ?", (d.get("id", 0),))
		info = self.cursor.fetchone()
		if not info:
			return {"stat": "Gagal", "pesan": "Perubahan QR tidak dapat dilakukan karena data tidak ditemukan"}, 400
			
		nama_lama = info["bank"] + info["nama_pemilik"] + ".jpeg"
		nama_baru = d.get("bank", "") + d.get("nama", "") + ".jpeg"
		os.rename(os.path.join(folder_pembayaran, nama_lama), os.path.join(folder_pembayaran, nama_baru))
			
		self.cursor.execute("UPDATE media_bayar SET nama_pemilik = ?, bank = ?, nomor_rekening = ? WHERE id = ?", (d.get("nama", ""), d.get("bank", ""), d.get("norek", ""), d.get("id", 0)))
		self.conn.commit()
		return {"stat": "Berhasil", "pesan": "Data rekening telah diperbarui"}, 200
	
	def hapus_rekening(self):
		d = self.data
		try:
			os.remove(os.path.join(folder_pembayaran, d.get("nama", "")))
			self.cursor.execute("DELETE FROM media_bayar WHERE id = ?", (d.get("id",0),))
			self.conn.commit()
			return {"stat": "Berhasil", "pesan": f"Data rekening {d.get('nama', '').replace('.jpeg', '')} telah dihapus"}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan. {e}"
			}, 500
	
	def reupload_qr(self):
		d = self.data
		nama = d.filename
		filepath = os.path.join(folder_pembayaran, nama)
		d.save(filepath)
		return {"stat": "Berhasil", "pesan": "Gambar baru telah disimpan"}, 200
	
	def hapus_anggota_shift(self):
		self.cursor.execute("SELECT anggota FROM shift WHERE id_shift = ?",(self.data.get("id",""),))
		member = self.cursor.fetchone()
		if not member:
			return {"stat": "Gagal", "pesan": "Anggota tidak ditemukan"}, 400
			
		anggota = json.loads(member["anggota"])
		new_anggota = [p for p in anggota if p["inisial_code"].lower() != self.data.get("inisial_code","").lower()]
		self.cursor.execute("UPDATE shift SET anggota = ? WHERE id_shift = ?",(json.dumps(new_anggota), self.data.get("id","")))
		self.conn.commit()
		return {"stat": "Berhasil", "pesan": "Member telah dihapus"}, 200
		
	def hapus_seluruh_shift(self):
		self.cursor.execute("DELETE FROM shift")
		self.conn.commit()
		return {"stat": "Berhasil", "pesan": "Seluruh data shift telah dihapus"}, 200
	
	def hapus_shift_tertentu(self):
		self.cursor.execute("DELETE FROM shift WHERE id_shift = ?",(self.data.get("id",""),))
		self.conn.commit()
		return {
			"stat": "Berhasil",
			"pesan": f"Shift {self.data.get('id','')} telah dihapus"
		}, 200
	
	def edit_customer(self):
		d = self.data
		if not d:
			return {"stat": "Gagal", "pesan": "Data kosong"}, 400
		try:
			self.cursor.execute("""
				UPDATE customer SET
				nama = ?,
				alamat = ?,
				kontak = ?,
				email = ? 
				WHERE id = ?""",
				(
					d.get("nama",""),
					d.get("alamat",""),
					d.get("kontak",""),
					d.get("email",""),
					d.get("id",0)
				)
			)
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": f"Data customer {d.get('nama','')} telah diubah"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": f"Terjadi kesalahan. {e}"
			}, 500
		
	def edit_supplier(self):
		d = self.data
		if not d:
			return {"stat": "Gagal", "pesan": "Data kosong"}, 400
		try:
			self.cursor.execute("""
				UPDATE supplier SET
				nama = ?,
				alamat = ?,
				kontak = ?,
				email = ?,
				bidang = ?,
				medsos = ?
				WHERE id = ?""",
				(
					d.get("nama",""),
					d.get("alamat",""),
					d.get("kontak",""),
					d.get("email",""),
					d.get("bidang",""),
					d.get("medsos",""),
					d.get("id",0)
				)
			)
			self.conn.commit()
			return {
				"stat": "Berhasil",
				"pesan": f"Data supplier {d.get('nama','')} telah diubah"
			}, 200
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Error",
				"pesan": "Terjadi kesalahan. {e}"
			}, 500
	
	def hapus_customer(self):
		if not self.data:
			return {
				"stat": "Gagal",
				"pesan": "Data kosong"
			}, 400
		self.cursor.execute("DELETE FROM customer WHERE id = ?", (self.data.get("id",""),))
		self.conn.commit()
		return {
			"stat": "Berhasil",
			"pesan": "Customer telah dihapus"
		}, 200
	
	def hapus_supplier(self):
		if not self.data:
			return {
				"stat": "Gagal",
				"pesan": "Data kosong"
			}, 400
		self.cursor.execute("DELETE FROM supplier WHERE id = ?", (self.data.get("id",""),))
		self.conn.commit()
		return {
			"stat": "Berhasil",
			"pesan": "Supplier telah dihapus"
		}, 200
		
	def tambah_supplier(self):
		d = self.data
		if not d or not d.get("nama",""):
			return {
				"stat": "Gagal",
				"pesan": "Data tidak boleh kosong atau minimal nama harus diisi"
			}, 400
		self.cursor.execute("INSERT INTO supplier (nama, alamat, kontak, email, bidang, medsos) VALUES (?, ?, ?, ?, ?, ?)",
			(
				d.get("nama",""),
				d.get("alamat",""),
				d.get("kontak",""),
				d.get("email",""),
				d.get("bidang",""),
				d.get("medsos","")
			)
		)
		self.conn.commit()
		return {
			"stat": "Berhasil",
			"pesan": f"Supplier {d.get('nama','')} telah ditambahkan"
		}, 200
		
	def tambah_customer(self):
		d = self.data
		if d.get("password","") != d.get("konfirmasi password",""):
			return {
				"stat": "Gagal",
				"pesan": "Password dan konfirmasi password harus sama"
			}, 400
		if len(d.get("password","")) < 6:
			return {
				"stat": "Gagal",
				"pesan": "Password harus berisi minimal 6 karakter"
			}, 400
		self.cursor.execute("SELECT * FROM customer WHERE email = ? OR kontak = ?",(d.get("email",""), d.get("kontak","")))
		exist = self.cursor.fetchone()
		if exist:
			return {
				"stat": "Gagal",
				"pesan": "Nomor telepon atau email yang Anda gunakan telah terdaftar. Silahkan login"
			}, 400
		id_user = "user-" + str(uuid.uuid4())[:10]
		if d.get("password",""):
			password = pbkdf2_sha256.hash(d.get("password",""))
		else:
			password = ""
		
		self.cursor.execute("""
			INSERT INTO customer (id_user, nama, alamat, kontak, email, id_device, status_login, password, poin)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
			(
				id_user,
				d.get("nama",""),
				d.get("alamat",""),
				d.get("kontak",""),
				d.get("email",""),
				d.get("idDev",""),
				0,
				password,
				0
			)
		)
		self.conn.commit()
		return {
			"stat": "Berhasil",
			"pesan": f"Customer {d.get('nama','')} telah ditambahkan",
			"id": id_user
		}, 200
	
	def hapus_seluruh(self):
		self.cursor.execute(f"DELETE FROM {self.data.get('mode','')}")
		self.conn.commit()
		return {
			"stat": "Berhasil",
			"pesan": f"Seluruh data {self.data.get('mode','')} telah dihapus"
		}, 200
		
	def hitung_pajak(self, harga_jual, status_pajak, persen_pajak):
		if status_pajak == 1:
			harga_awal = harga_jual / (1 + persen_pajak / 100)
			nilai_pajak = harga_jual - harga_awal
			return round(nilai_pajak)
		else:
			return 0
	
	def proses_retur(self):
		d = self.data
		data = d.get("belanja",{})
		retur = d.get("retur",[])
		status_pajak = data.get("status_pajak",0)
		keranjang = json.loads(data["data_belanja"])
				
		for p in retur:
			self.cursor.execute("SELECT jumlah FROM produk WHERE id_produk = ?",(p.get("id",""),))
			jumlah = self.cursor.fetchone()
			if not jumlah:
				self.conn.rollback()
				return {
					"stat": "Tidak ditemukan",
					"pesan": f"Produk {p.get('id','')} tidak ditemukan"
				}, 400
			self.cursor.execute("UPDATE produk SET jumlah = ? WHERE id_produk = ?",(jumlah["jumlah"] + p.get("jumlah",0), p.get("id","")))
			
			item_jual = next((k for k in keranjang if k["id"] == p["id"]), None)
			if status_pajak == 1:
				if item_jual.get("tipe_promo","").lower() == "tingkat":
					harga_jual_peritem = item_jual.get("harga_jual",0) / item_jual.get("qty_asli",0)
					nilai_pajak = self.hitung_pajak(harga_jual_peritem, status_pajak, item_jual.get("persen_pajak",0))
				else:
					nilai_pajak = self.hitung_pajak(item_jual.get("harga_jual",0), status_pajak, item_jual.get("persen_pajak",0))
				
				self.cursor.execute("INSERT INTO riwayat_pajak (waktu, nama, pajak) VALUES (?, ?, ?)",
					(
						now_str(),
						p.get("nama",""),
						-nilai_pajak * p.get("jumlah",0)
					)
				)
			laba_terkurang = item_jual["laba"] / item_jual["qty_asli"] * p["jumlah"]
			pemasukan_terkurang = p.get("subtotal", 0)
			self.cursor.execute("SELECT pemasukan, keuntungan FROM keuangan")
			keuangan = self.cursor.fetchone()
			
			self.cursor.execute("UPDATE keuangan SET pemasukan = ?, keuntungan = ? WHERE id = ?",
				(
					(keuangan["pemasukan"] if keuangan else 0) - pemasukan_terkurang,
					(keuangan["keuntungan"] if keuangan else 0) - laba_terkurang,
					1
				)
			)
			
		self.cursor.execute("INSERT INTO riwayat_retur (waktu, no_trans, pembeli, data, alasan) VALUES (?, ?, ?, ?, ?)",
			(
				now_str(),
				data.get("no_trans",""),
				data.get("pembeli", ""),
				json.dumps(retur),
				d.get("alasan","")
			)
		)
		self.cursor.execute("SELECT * FROM keuangan")
		uang = self.cursor.fetchone()
		total_retur = sum(p["subtotal"] for p in retur)
		saldo_awal = (uang["keuntungan"] - uang["total_pengeluaran"] + uang["saldo"]) if uang else 0
		
		self.cursor.execute("INSERT INTO riwayat_keuangan (waktu, jumlah, jenis, sumber, saldo_awal, saldo_akhir, pihak_terkait, keterangan, id_keuangan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
			(
				now_str(),
				total_retur,
				"Retur produk",
				"Saldo kas",
				saldo_awal,
				saldo_awal - total_retur,
				json.dumps([data.get("pembeli",""), d.get("operator","")]),
				"Refund dari retur yang dilakukan customer",
				str(uuid.uuid4())[:5]
			)
		)				
				
		self.conn.commit()
		return {
			"stat": "Berhasil",
			"pesan": "Proses retur berhasil"
		}, 200
		
	def tambah_pengeluaran(self):
		data = self.data
		try:
			self.cursor.execute("INSERT INTO Pengeluaran (waktu, nama, jumlah, satuan_jumlah, harga, total, kategori, keterangan, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (data.get("waktu",""), data.get("nama", ""), data.get("jumlah", 0), data.get("satuan_jumlah", ""), data.get("harga", 0), data.get("total", 0), data.get("kategori", ""), data.get("keterangan", ""), data.get("operator", ""), data.get("sumber", "")))
			self.cursor.execute("UPDATE keuangan SET total_pengeluaran = total_pengeluaran + ? WHERE id = ?", (data.get("total",0), 1))
			self.conn.commit()
		except Exception:
			self.conn.rollback()
			raise
			
		return {
			"stat": "Berhasil",
			"pesan": f"Pengeluaran {data.get('nama','')} telah ditambahkan"
		}, 200
		
	def edit_pengeluaran(self):
		d = self.data
		total_lama = d.get("total_awal",0)
		id_data = d.get("id",0)
		if not id_data:
			return {
				"stat": "Gagal",
				"pesan": "Update data pengeluaran ditolak. Id data tidak dikenali"
			}, 400
		try:
			self.cursor.execute("UPDATE keuangan SET total_pengeluaran = total_pengeluaran - ? + ? WHERE id = ?", (total_lama, d.get("total",0), 1))
			self.cursor.execute("UPDATE Pengeluaran SET waktu = ?, nama = ?, jumlah = ?, harga = ?, total = ?, kategori = ?, keterangan = ?, operator = ?, sumber = ?, satuan_jumlah = ? WHERE id = ?", (d.get("waktu", ""), d.get("nama", ""), d.get("jumlah", 0), d.get("harga", 0), d.get("total", 0), d.get("kategori", ""), d.get("keterangan", ""), d.get("operator", ""), d.get("sumber", ""), d.get("satuan_jumlah", ""), id_data))
			self.conn.commit()
		except Exception:
			self.conn.rollback()
			raise
		return {
			"stat": "Berhasil",
			"pesan": "Data pengeluaran telah diperbarui"
		}, 200
		
	def hapus_pengeluaran(self):
		d = self.data
		if not d.get("id",0):
			return {
				"stat": "Gagal",
				"pesan": "Id diperlukan untuk menghapus pengeluaran"
			}, 400
		try:
			self.cursor.execute("UPDATE keuangan SET total_pengeluaran = total_pengeluaran - ? WHERE id = ?", (d.get("total",0), 1))
			self.cursor.execute("DELETE FROM Pengeluaran WHERE id = ?", (d.get("id",0),))
			self.conn.commit()
		except Exception as e:
			self.conn.rollback()
			return {
				"stat": "Gagal",
				"pesan": f"Terjadi kesalahan saat penghapusan:\n {e}"
			}, 500
		return {
			"stat": "Berhasil",
			"pesan": f"Pengeluaran dengan id {d.get('id',0)} telah dihapus"
		}, 200
		
	def close(self):
		self.conn.close()
		
@app.route("/post_data/<func>", methods=["POST"])
def post_data(func):
	if func not in allowed_methods:
		return jsonify({"stat": "Gagal", "pesan": "Link Anda tidak tersedia"}), 403
	data = request.json
	if not data:
		return jsonify({"stat": "Gagal", "pesan": "Data kosong"}), 400
	olah = PostData(data)
	try:
		method = getattr(olah, func, None)
		if method is None:
			return jsonify({"stat": "Gagal", "pesan": f"Fungsi {func} tidak ditemukan!"}), 400
		result, code = method()
		return jsonify(result), code
	except Exception as e:
		print(e)
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	finally:
		olah.close()
		
@app.route("/post_file/<func>", methods=["POST"])
def post_file(func):
	if func not in allowed_methods:
		return jsonify({"stat": "Gagal", "pesan": "Link Anda tidak tersedia"}), 403
	file = request.files["file"]
	if not file:
		return jsonify({"stat": "Gagal", "pesan": "Data kosong"}), 400
	olah = PostData(file)
	try:
		method = getattr(olah, func, None)
		if method is None:
			return jsonify({"stat": "Gagal", "pesan": f"Fungsi {func} tidak ditemukan!"}), 400
		result, kode = method()
		return jsonify(result), kode
	except Exception as e:
		print(e)
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	finally:
		olah.close()
		
@app.route("/get_file", methods=["POST"])
def get_file(): #dijadwalkan
	data = request.json
	path = data.get("path_file","")
	if not os.path.exists(path):
		return "Not Found", 400
	return send_file(path)
		
@app.route("/lakukan_restore", methods=["POST"])
def lakukan_restore():
	data = request.json
	if not data:
		return "Data kosong", 400
	file = data.get("pilih", [])
	map_asal = {p.split("/")[-1].lower(): p for p in data.get("path", [])}
	map_tujuan = {p.split("/")[-1].lower(): p for p in data.get("path ori", [])}
	for p in file:
		shutil.copy(map_asal.get(p.lower(), ""), map_tujuan.get(p.lower(), ""))
	return "Berhasil", 200

@app.route("/ubah_status_sudah_dibayar", methods=["POST"])
def ubah_status_sudah_dibayar():
	data = request.json
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("UPDATE permintaan SET status = ? WHERE id = ?", ("Sudah dibayar", data.get("id", 0)))
		conn.commit()
		return jsonify({"stat": "Berhasil", "pesan": "Pesanan telah dibayar!"}), 200
	except sqlite3.Error as e:
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	except Exception as e:
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	finally:
		if conn:
			conn.close()
			
@app.route("/upload_bukti_bayar/<nama>", methods=["POST"])
def upload_bukti_bayar(nama):
	file = request.files["file"]
	nama_file = "Pembayaran_" + nama +".jpeg"
	path_file = os.path.join(folder_nota, nama_file)
	file.save(path_file)
	return jsonify({"stat": "Berhasil", "pesan": "Bukti pembayaran telah diterima!"}), 200
	
@app.route("/update_status_permintaan", methods=["POST"])
def update_status_permintaan():
	data = request.json
	if data:
		id = data.get("id", 0)
		data_asli = data.get("data", {})
		keranjang = data.get("keranjang", [])
		data_asli["belanjaan"] = keranjang
		try:
			conn = sqlite3.connect(path_database())
			conn.row_factory = sqlite3.Row
			cursor = conn.cursor()
			
			cursor.execute("UPDATE permintaan SET data = ?, status = ? WHERE id = ?", (json.dumps(data_asli), "Diproses", id))
			conn.commit()
			return "Berhasil", 200
			
		except sqlite3.Error as e:
			return jsonify({"stat": "Error", "pesan": f"Simpan nota berhasil. {e}"}), 400
		except Exception as e:
			return jsonify({"stat": "Error", "pesan": f"Simpan nota berhasil. {e}"}), 400
		finally:
			if conn:
				conn.close()
	else:
		return jsonify({"stat": "Gagal", "pesan": "Data kosong"}), 400
					
@app.route("/simpan_nota", methods=["POST"])
def simpan_nota():
	file = request.files["file"]
	nama_file = file.filename
	path_tujuan = os.path.join(folder_nota, nama_file)
	file.save(path_tujuan)
	return jsonify({"stat": "Berhasil", "pesan": "File telah disimpan"}), 200
	
@app.route("/periksa_file", methods=["POST"])
def periksa_file():
	data = request.json
	if not data:
		return jsonify({"ada": False}), 400
	path_file = os.path.join(folder_nota, data.get("nama", ""))
	if not os.path.exists(path_file):
		return jsonify({"ada": False})
	return jsonify({"ada": True})

@app.route("/logout_delete", methods=["POST"])
def logout_delete():
	data = request.json
	nama = ""
	for p in ses:
		if p.get("idDevice", "").lower() == data.get("id", "").lower():
			p["login"] = 0
			nama = p.get("pengguna", "")
			break
	simpan_semua(session, ses)
	return jsonify({"stat": "Berhasil", "pesan": f"Sampai jumpa lagi {nama}"}), 200
						
@app.route("/cek_login", methods=["POST"])
def cek_login(): #dijadwalkan
	data = request.json
	if not data:
		return jsonify({"lolos": False, "pesan": "Data kosong"}), 400
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		
		cursor.execute("SELECT * FROM user")
		user = cursor.fetchall()
		pengguna = next((p for p in user if p["inisial_code"] == data.get("username", "") or p["nama"].lower() == data.get("username", "").lower()), None)
		if not pengguna:
			return jsonify({"stat": "Gagal", "lolos": False, "pesan": "Username tidak ditemukan"}), 400
		if pbkdf2_sha256.verify(data.get("password", ""), pengguna["password"]):
			for p in ses:
				if p.get("idDevice", "").lower() == data.get("id", "").lower():
					p["pengguna"] = pengguna["nama"]
					p["inisial_code"] = pengguna["inisial_code"]
					p["login"] = 1
					break
			else:
				ses.append({
					"login": 1,
					"pengguna": pengguna["nama"],
					"inisial_code": pengguna["inisial_code"],
					"idDevice": data.get("id", "")
				})
			simpan_semua(session, ses)
			return jsonify({"stat": "Berhasil", "lolos": True, "pesan": f"Selamat datang {pengguna['nama']}", "pengguna": pengguna["nama"], "inisial_code": pengguna["inisial_code"]}), 200
		else:
			return jsonify({"stat": "Gagal", "lolos": False, "pesan": "Kata sandi salah"}), 400
	except sqlite3.Error as e:
		return jsonify({"stat": "Gagal", "pesan": str(e)}), 500
	except Exception as e:
		return jsonify({"stat": "Gagal", "pesan": str(e)}), 500
	finally:
		if conn:
			conn.close()
			
@app.route("/edit_permintaan", methods=["POST"])
def edit_permintaan():
	data = request.json
	if not data:
		return "Kosong", 400
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		if data.get("status", "") == "approved":
			cursor.execute("UPDATE permintaan SET status = ? WHERE id = ?", (data.get("status", ""), data.get("id", "")))
		else:
			cursor.execute("DELETE FROM permintaan WHERE id = ?", (data.get("id", ""), ))
		conn.commit()
		return "Berhasil", 200
	except sqlite3.Error as e:
		return str(e), 500
	except Exception as e:
		return str(e), 500
	finally:
		if conn:
			conn.close()

@app.route("/olah_data_pesanan_sampai_selesai", methods=["POST"])
def olah_data_pesanan_sampai_selesai():
	data = request.json
	if not data:
		return jsonify({"stat": "Gagal", "pesan": "Data kosong"}), 400
	bayar = data.get("bayar", 0)
	sumber = data.get("sumber", "")
	opr = data.get("operator", "")
	
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		
		cursor.execute("SELECT data, oleh FROM permintaan WHERE id = ?", (data.get("id", ""), ))
		dt = cursor.fetchone()
		data_olah = json.loads(dt["data"])
		keranjang = data_olah.get("belanjaan", [])
		
		total_poin, kena_pajak, masuk, untung, total = 0, 0, 0, 0, 0
		for k in keranjang:
			id = k.get("id", "")
			qty = k.get("qty_asli", 0)
			cursor.execute("SELECT jumlah, poin FROM produk WHERE id_produk = ?", (id, ))
			jml = cursor.fetchone()
			cursor.execute("UPDATE produk SET jumlah = ? WHERE id_produk = ?", (jml["jumlah"] - qty, id))
			total_poin += jml["poin"] * qty
			subtotal_asli = k.get("harga_asli", 0) * qty
			
			if data_olah.get("status_pajak", 0) == 1:
				nilai_pajak = round(k.get("subtotal_jual", 0) - subtotal_asli)
				kena_pajak += nilai_pajak
				cursor.execute("INSERT INTO riwayat_pajak (waktu, nama, pajak) VALUES (?, ?, ?)", (now_str(), k.get("nama", ""), nilai_pajak))
			masuk += subtotal_asli
			untung += k.get("laba", 0)
			total += round(k.get("subtotal_jual", 0))
		
		cursor.execute("""
		INSERT INTO riwayat_penjualan_campuran
		(waktu, total, total_laba, no_trans, operator, sumber, pembeli,
		bayar, kembali, data_belanja, kena_pajak, status_pajak)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
			(
				now_str(),
				total,
				untung,
				data_olah.get("no_trans", ""),
				opr,
				sumber,
				data_olah.get("nama", ""),
				bayar,
				bayar - total,
				json.dumps(keranjang),
				round(data_olah.get("kena_pajak", 0)),
				data_olah.get("status_pajak", 0)
			)
		)
		cursor.execute("SELECT keuntungan, pemasukan FROM keuangan")
		money = cursor.fetchone()
		cursor.execute("UPDATE keuangan SET keuntungan = ?, pemasukan = ? WHERE id = ?", (money["keuntungan"] + untung, money["pemasukan"] + masuk, 1))
		
		if dt["oleh"]:
			cursor.execute("SELECT poin FROM customer WHERE id_user = ?", (dt["oleh"], ))
			pn = cursor.fetchone()
			cursor.execute("UPDATE customer SET poin = ? WHERE id_user = ?", (pn["poin"] + total_poin, dt["oleh"]))
		
		cursor.execute("UPDATE permintaan SET status = ? WHERE id = ?", ("Sedang diantar", data.get("id", "")))
		conn.commit()
		return jsonify({"stat": "Berhasil", "pesan": f"Data pesanan {data_olah.get('nama', '')} telah selesai diproses"}), 200
	
	except sqlite3.Error as e:
		print(traceback.format_exc())
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	except Exception as e:
		print(traceback.format_exc())
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	finally:
		if conn:
			conn.close()
		
@app.route("/tambahkan_pesanan", methods=["POST"])
def tambahkan_pesanan():
	data = request.json
	oleh = data.get("oleh", "")
	if not data:
		return jsonify({"stat": "Gagal", "pesan": "Data kosong"}), 400
	
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("INSERT INTO permintaan (waktu, jenis, data, status, oleh) VALUES (?, ?, ?, ?, ?)", (now_str(), "Pesanan pembeli", json.dumps(data), "Ditangguhkan", oleh))
		conn.commit()
		return jsonify({"stat": "Berhasil", "pesan": "Data pesanan telah diterima. Kami akan segera meninjau pesanan Anda. Terima kasih telah menunggu!!"}), 200
	except sqlite3.Error as e:
		return jsonify({"stat": "Gagal", "pesan": str(e)}), 401
	except Exception as e:
		return jsonify({"stat": "Gagal", "pesan": str(e)}), 401
	finally:
		if conn:
			conn.close()
					
@app.route("/tambah_user_baru", methods=["POST"])
def tambah_user_baru():
	data = request.json
	if not data:
		return "Kosong", 400
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("INSERT INTO permintaan (waktu, jenis, data, status, oleh) VALUES (?, ?, ?, ?, ?)", (now_str(), "Pendaftaran pengguna baru", json.dumps(data), "Pending", ""))
		conn.commit()
		return "Berhasil", 200
	except sqlite3.Error as e:
		return str(e), 500
	except Exception as e:
		return str(e), 500
	finally:
		if conn:
			conn.close()
			
@app.route("/opsi_server_utama", methods=["POST"])
def opsi_server_utama():
	data = request.json
	if not data:
		return "Gagal", 400
	opsi_server["opsi"] = data.get("opsi", "Local server")
	simpan_semua(file_server, opsi_server)
	return "Berhasil", 200
	
@app.route("/ambil_path_file_backup", methods=["POST"])
def ambil_path_file_backup():
	data = request.json
	path = data.get("path", "")
	def get_files(folder):
		paths = []
		for p in os.listdir(folder):
			pt = os.path.join(folder, p)
			if os.path.isfile(pt):
				paths.append(pt)
			elif os.path.isdir(pt):
				paths.extend(get_files(pt))
		return paths	
	files = get_files(path)
	info = os.path.join(path, "Info.json")
	if info in files:
		files.remove(info)
	try:
		with open(info, "r") as f:
			info_backup = json.load(f)
		return jsonify({
			"waktu": info_backup.get("waktu", ""),
			"path files": files,
			"path original": info_backup.get("original path", [])
		})		
	except Exception as e:
		return str(e), 500
		
@app.route("/lakukan_backup", methods=["POST"])
def lakukan_backup():
	data = request.json
	if not data:
		return "Gagal", 400
	try:
		folder = datetime.now().strftime("Backup %A, %d %B %Y %H_%M_%S")
		path_folder = os.path.join(folder_backup, folder)
		os.makedirs(path_folder, exist_ok=True)
		
		for p in data:
			nama_file = os.path.basename(p)
			path_tujuan = os.path.join(path_folder, nama_file)
			shutil.copy(p, path_tujuan)
		info_backup = os.path.join(path_folder, "Info.json")
		dt = {
			"waktu": now_str(),
			"original path": data
		}
		with open(info_backup, "w", encoding="utf-8") as f:
			json.dump(dt, f, indent=4, ensure_ascii=False)
					
		return "Berhasil", 200
	except FileNotFoundError:
		return "Tidak ditemukan", 400
	except Exception as e:
		print(e)
		return str(e), 500
			
@app.route("/hapus_folder", methods=["POST"])
def hapus_folder():
	data = request.json
	if not data:
		return jsonify({"status": "Kosong", "pesan": "Folder kosong"})
	try:
		shutil.rmtree(data.get("path", ""))
		return "Berhasil", 200
	except FileNotFoundError:
		return "Tidak ditemukan", 400
	except PermissionError:
		return "Tidak diizinkan", 400
	except Exception:
		return "Gagal", 401
	
@app.route("/hapus_file", methods=["POST"])
def hapus_file():
	data = request.json
	if not data:
		return jsonify({"status": "Kosong", "pesan": "File kosong"})
	try:
		os.remove(data.get("path", ""))
		return "Berhasil", 200
	except FileNotFoundError:
		return "Tidak ditemukan", 400
	except PermissionError:
		return "Tidak diizinkan", 400
	except Exception:
		return "Gagal", 401
		
@app.route("/take_file", methods=["POST"])
def take_file():
	data = request.json
	path = data.get("path", "")
	if not path:
		return jsonify({"status": 400, "pesan": "File kosong"})
	return send_file(path)
	
@app.route("/hapus_riwayat_penjualan", methods=["POST"])
def hapus_riwayat_penjualan():
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		data = request.json
		for p in data:
			no = p["no_trans"]
			cursor.execute("DELETE FROM riwayat_penjualan_campuran WHERE no_trans = ?", (no, ))
		conn.commit()
		return "Berhasil", 200
	except sqlite3.Error as e:
		return f"Database error: {str(e)}", 500
	except Exception as e:
		return f"Error: {str(e)}", 500
	finally:
		if conn:
			conn.close()
	
@app.route("/hapus_data_produk", methods=["POST"])
def hapus_data_produk():
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		data = request.json
		for p in data:
			id_produk = p["id_produk"]
			cursor.execute("DELETE FROM produk WHERE id_produk = ?", (id_produk, ))
		conn.commit()
		return "Berhasil", 200
		
	except sqlite3.Error as e:
		return f"Database error: {str(e)}", 500
	except Exception as e:
		return f"Error: {str(e)}", 500
	finally:
		if conn:
			conn.close()
	
@app.route("/tambah_stok_cepat", methods=["POST"])
def tambah_stok_cepat():
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()

		data = request.json
		if not data or not isinstance(data, list):
			return "Data harus berupa list of objects", 400

		for p in data:
			id_produk = p.get("id")
			tambahan = p.get("tambahan")

			if id_produk is None or tambahan is None:
				return "Setiap item harus memiliki 'id' dan 'tambahan'", 400

			try:
				id_produk = id_produk
				tambahan = int(tambahan)
			except (TypeError, ValueError):
				return f"ID dan tambahan harus berupa angka untuk item {p}", 400

			if tambahan < 0:
				return f"Tambahan stok tidak boleh negatif untuk ID {id_produk}", 400

			cursor.execute("SELECT jumlah FROM produk WHERE id_produk = ?", (id_produk,))
			row = cursor.fetchone()

			if row is None:
				return f"Produk dengan ID {id_produk} tidak ditemukan", 404

			jumlah_baru = row["jumlah"] + tambahan

			cursor.execute("UPDATE produk SET jumlah = ? WHERE id_produk = ?", (jumlah_baru, id_produk))

			if cursor.rowcount == 0:
				return f"Gagal update produk ID {id_produk}", 404

		conn.commit()
		return "Berhasil", 200

	except sqlite3.Error as e:
		return f"Database error: {str(e)}", 500
	except Exception as e:
		return f"Error: {str(e)}", 500
	finally:
		if conn:
			conn.close()
	
@app.route("/tambah_format_waktu", methods=["POST"])
def tambah_format_waktu():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	data = request.json
	cursor.execute("SELECT format_waktu FROM pengaturan_format")
	frmt = cursor.fetchone()
	if frmt:
		cursor.execute("UPDATE pengaturan_format SET format_waktu = ? WHERE id = ?", (data.get("format", ""), 1))
	else:
		cursor.execute("INSERT INTO pengaturan_format (format_waktu) VALUES (?)", (data.get("format", ""), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200
				
@app.route("/tambah_mata_uang", methods=["POST"])
def tambah_mata_uang():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	data = request.json
	
	cursor.execute("SELECT format_uang FROM pengaturan_format")
	d = cursor.fetchone()
	if d:
		cursor.execute("UPDATE pengaturan_format SET format_uang = ? WHERE id = ?", (data.get("data", ""), 1))
	else:
		cursor.execute("INSERT INTO pengaturan_format (format_uang) VALUES (?)", (data.get("data", ""), ))
	conn.commit()
	conn.close()
	desimal["approved"] = data.get("use_decimal", True)
	simpan_semua(file_desimal, desimal)
	return "Berhasil", 200
	
@app.route("/ganti_bahasa", methods=["POST"])
def ganti_bahasa():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	data = request.json
	lg = data.get("bahasa", "")
	cursor.execute("SELECT bahasa FROM pengaturan_format")
	b = cursor.fetchone()
	if b:
		cursor.execute("UPDATE pengaturan_format SET bahasa = ? WHERE id = ?", (lg.lower(), 1))
	else:
		cursor.execute("INSERT INTO pengaturan_format (bahasa) VALUES (?)", (lg.lower(), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200
				
@app.route("/bersihkan_folder", methods=["POST"])
def bersihkan_folder():
	data = request.json
	path = os.path.join(basedir, data.get("folder", ""))
	all_files = os.listdir(path)
	for x in all_files:
		full_path = os.path.join(path, x)
		os.remove(full_path)
	return "Berhasil", 200
	
@app.route("/hapus_transaksi_tertentu", methods=["POST"])
def hapus_transaksi_tertentu():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	data = request.json
	cursor.execute("DELETE FROM riwayat_penjualan_campuran WHERE no_trans = ?", (data.get("no", ""), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/tambah_retur", methods=["POST"])
def tambah_retur():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT persen FROM pajak")
	p = cursor.fetchone()
	persen = p["persen"]
	
	def cek_pajak(h, s, p):
		real_price = round(h / (1 + p / 100)) if s == 1 else h
		return real_price
	def hitung_pajak(h, s):
		price = round(h * (1 + persen / 100)) if s == 1 else h
		return price
		
	data = request.json
	data_retur = data.get("data", [])
	no_trans = data.get("no_trans", "")
	pemasukan, keuntungan, total_retur, pajak, total_qty_retur= 0, 0, 0, 0, 0
	for p in data_retur:
		nama = p.get("nama", "")
		barcode = p.get("barcode", "")
		jumlah = p.get("qty", 0)
		total_qty_retur += jumlah
		cursor.execute("SELECT * FROM produk WHERE nama = ?", (nama, ))
		produk = cursor.fetchone()
		cursor.execute("UPDATE produk SET jumlah = ? WHERE id_produk = ?", (produk["jumlah"] + jumlah, produk["id_produk"]))
		cursor.execute("SELECT * FROM riwayat_penjualan_campuran WHERE no_trans = ?", (data.get("no_trans", "").upper(), ))
		riwayat = cursor.fetchone()
		keranjang = json.loads(riwayat["data_belanja"])
		for k in keranjang:
			if k.get("nama", "").lower() == nama.lower():
				harga_jual = k.get("harga_jual", 0)
				harga_modal = k.get("harga_modal", 0)
				subtotal_modal = jumlah * harga_modal
				sjtp = jumlah * harga_jual
				total_retur += sjtp
				sjsp = cek_pajak(sjtp, riwayat["status_pajak"], persen)
				nilai_pajak = sjtp - sjsp
				pajak += nilai_pajak
				pemasukan += sjsp
				keuntungan += sjsp - subtotal_modal
				k["status_retur"] = "Pernah retur"
				k["qty_asli"] -= jumlah
				cursor.execute("SELECT * FROM riwayat_pajak WHERE nama = ?", (nama, ))
				pjk = cursor.fetchall()
				if pjk:
					for k in pjk:
						if k["pajak"] >= nilai_pajak:
							cursor.execute("UPDATE riwayat_pajak SET pajak = ? WHERE id = ?", (k["pajak"] - nilai_pajak, k["id"]))
							break
		for k in keranjang[:]:
			if k.get("qty_asli", 0) <= 0:
				keranjang.remove(k)
				
		cursor.execute("UPDATE riwayat_penjualan_campuran SET data_belanja = ? WHERE no_trans = ?", (json.dumps(keranjang), riwayat["no_trans"]))
		conn.commit()
	
	cursor.execute("SELECT * FROM riwayat_penjualan_campuran WHERE no_trans = ?", (no_trans.upper(), ))
	stts = cursor.fetchone()
	status = stts["status_pajak"]
		
	new_total = stts["total"] - hitung_pajak(pemasukan, status)
	new_total_laba = stts["total_laba"] - keuntungan
	cursor.execute("UPDATE riwayat_penjualan_campuran SET total = ?, total_laba = ? WHERE no_trans = ?", (new_total, new_total_laba, no_trans.upper()))	
	cursor.execute("SELECT pemasukan, keuntungan FROM keuangan")
	uang = cursor.fetchone()
	cursor.execute("UPDATE keuangan SET pemasukan = ?, keuntungan = ? WHERE id = ?", (uang["pemasukan"] - pemasukan, uang["keuntungan"] - keuntungan, 1))
	cursor.execute("INSERT INTO riwayat_retur (waktu, no_trans, pembeli, data, alasan) VALUES (?, ?, ?, ?, ?)", (data.get("waktu", ""), data.get("no_trans", "").upper(), data.get("pembeli", ""), json.dumps(data_retur), data.get("alasan", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/bersihkan_riwayat_penjualan", methods=["POST"])
def bersihkan_riwayat_penjualan():
	conn = sqlite3.connect(path_database())
	cursor = conn.cursor()
	cursor.execute("DELETE FROM riwayat_penjualan_campuran")
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/penjualan_campuran", methods=["POST"])
def penjualan_campuran():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	data = request.json

	keranjang = data.get("items", [])
	total = data.get("total", 0)
	bayar = data.get("bayar", 0)
	kembali = data.get("kembali", 0)
	sumber = data.get("sumber", "")
	operator = data.get("operator", "")
	no_trans = data.get("no_trans", "")
	waktu = data.get("waktu", now_str())
	pembeli = data.get("pembeli", "")

	cursor.execute("SELECT persen, aktif FROM pajak")
	pjk = cursor.fetchone()

	masuk, untung, total_poin, kena_pajak, status_pajak = 0, 0, 0, 0, 0
	for k in keranjang:
		id = k.get("id", "")
		qty = k.get("qty_asli", 0)

		cursor.execute("SELECT poin FROM produk WHERE id_produk = ?", (id, ))
		prd = cursor.fetchone()
		total_poin += prd["poin"] * qty

		cursor.execute("UPDATE produk SET jumlah = jumlah - ? WHERE id_produk = ? AND jumlah >= ?", (qty, id, qty))
		if cursor.rowcount == 0:
			conn.rollback()
			conn.close()
			return "Stok tidak cukup", 400

		subtotal = k.get("subtotal_jual", 0)
		if pjk["aktif"] == 1:
			harga = subtotal / (1 + pjk["persen"] / 100)
			status_pajak = pjk["aktif"]
			nilai_pajak = subtotal - harga
			kena_pajak += nilai_pajak
			cursor.execute("INSERT INTO riwayat_pajak (waktu, nama, pajak) VALUES (?, ?, ?)", (waktu, k.get("nama", ""), nilai_pajak))
		else:
			harga = subtotal
		masuk += harga
		untung += k.get("laba", 0)

	cursor.execute("INSERT INTO riwayat_penjualan_campuran (waktu, total, total_laba, no_trans, operator, sumber, pembeli, bayar, kembali, data_belanja, kena_pajak, status_pajak) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (waktu, total, untung, no_trans, operator, sumber, pembeli if pembeli.lower() != "customer" else "", bayar, kembali, json.dumps(keranjang), kena_pajak, status_pajak))
	
	cursor.execute("UPDATE keuangan SET keuntungan = keuntungan + ?, pemasukan = pemasukan + ? WHERE id = ?", (untung, masuk, 1))
	cursor.execute("SELECT * FROM keuangan WHERE id = ?", (1, ))
	q = cursor.fetchone()
	
	cursor.execute("INSERT INTO riwayat_keuangan (waktu, jumlah, sumber, jenis, saldo_awal, saldo_akhir, pihak_terkait, keterangan, id_keuangan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
		(
			waktu,
			masuk,
			"Penjualan produk",
			"Transaksi penjualan produk dari operator",
			q["pemasukan"],
			q["pemasukan"] + masuk,
			pembeli + ", " + operator,
			f"Transaksi telah selesai pada {waktu}",
			str(uuid.uuid4())[:5]
		)
	)

	cs = pembeli.strip()
	if cs.lower() != "customer" and cs != "":
		cust = cs.split()
		if len(cust) < 2:
			conn.rollback()
			conn.close()
			return "Gagal", 400
		nama = " ".join(cust[:-1])
		kontak = cust[-1]
		cursor.execute("SELECT * FROM customer WHERE nama = ? AND kontak = ?", (nama, kontak))
		pbeli = cursor.fetchone()
		if pbeli:
			cursor.execute("UPDATE customer SET poin = poin + ? WHERE id = ?", (total_poin, pbeli["id"]))
		else:
			cursor.execute("INSERT INTO customer (nama, kontak, poin) VALUES (?, ?, ?)", (nama, kontak, total_poin))

	saldo_terakhir = q["saldo"]
	saldo_baru = saldo_terakhir + untung

	cursor.execute("""
	INSERT INTO riwayat_keuangan (waktu, jumlah, sumber,
	jenis, saldo_awal, saldo_akhir, pihak_terkait, keterangan,
	id_keuangan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (now_str(), untung, "Transaksi", "Keuntungan transaksi", saldo_terakhir, saldo_baru, "Customer", "Pemasukan dari keuntungan transaksi", datetime.now().strftime("%f")))

	conn.commit()
	conn.close()
	return jsonify({
		"stat":"Berhasil",
		"pesan": "Transaksi berhasil. Cetak struk penjualan?"
	}), 200
				
@app.route("/hapus_foto_profil", methods=["POST"])
def hapus_foto_profil():
	path = os.path.join(folder_foto, "foto profil.png")
	if os.path.exists(path):
		os.remove(path)
	else:
		return jsonify({"stat": "Kosong", "pesan": "File tidak tersedia"}), 400
	return jsonify({"stat": "berhasil", "pesan": "Foto profil telah dihapus"}), 200
	
@app.route("/tambah_pengaturan_nota", methods=["POST"])
def tambah_pengaturan_nota():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	data = request.json
	cursor.execute("SELECT * FROM pengaturan_nota")
	d = cursor.fetchall()
	if not d:
		cursor.execute("INSERT INTO pengaturan_nota (judul, catatan, penerima, penerbit) VALUES (?, ?, ?, ?)", (data.get("judul", ""), data.get("catatan", ""), data.get("penerima", ""), data.get("penerbit", "")))
	else:
		cursor.execute("UPDATE pengaturan_nota SET judul = ?, catatan = ?, penerima = ?, penerbit = ? WHERE id = ?", (data.get("judul", ""), data.get("catatan", ""), data.get("penerima", ""), data.get("penerbit", ""), 1))
	conn.commit()
	conn.close()
	return "Berhasil", 200
		
@app.route("/tambah_margin", methods=["POST"])
def tambah_margin():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM margin WHERE kategori = ?", (data.get("kategori", ""), ))
	d = cursor.fetchone()
	if not d:
		cursor.execute("INSERT INTO margin (kategori, margin) VALUES (?, ?)", (data.get("kategori", ""), data.get("margin", 0) / 100))
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/aktifkan_validasi_owner", methods=["POST"])
def aktifkan_validasi_owner():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM validasi_owner")
	d = cursor.fetchone()
	if not d:
		cursor.execute("INSERT INTO validasi_owner (status) VALUES (?)", (data.get("status", ""), ))
	else:
		cursor.execute("UPDATE validasi_owner SET status = ? WHERE id = ?", (data.get("status", ""), 1))
	conn.commit()
	conn.close()
	return "Berhasil", 200
							
@app.route("/hpt", methods=["POST"])
def hpt():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	data = request.json
	
	placeholder = ",".join(["?"] * len(data))
	cursor.execute(f"DELETE FROM produk WHERE id IN ({placeholder})", data)
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/hsp", methods=["POST"])
def hsp():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute("SELECT * FROM produk")
	jumlah = cursor.fetchall()
	jumlah_data = len(jumlah)
	
	cursor.execute("DELETE FROM produk")
	cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES(?, ?, ?, ?, ?, ?, ?)", (now_str(), "Hapus seluruh produk", "Seluruh produk", jumlah_data, "-", data.get("operator", ""), data.get("sumber", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/hapus_produk_diskon", methods=["POST"])
def hapus_produk_diskon():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	data = request.json
	
	cursor.execute("DELETE FROM produk_diskon WHERE nama = ? OR barcode = ?", (data.get("nama", ""), data.get("barcode", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
		
@app.route("/reset_keuangan", methods=["POST"])
def reset_keuangan():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE keuangan SET pemasukan = ?, keuntungan = ?, total_pengeluaran = ?, saldo = ? WHERE id = ?", (0, 0, 0, 0, 1))
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/reset_database", methods=["POST"])
def reset_database():
	database = path_database()
	if not os.path.exists(database):
		return "Tidak ada", 400
	else:
		os.remove(database)
		return "Berhasil", 200
			

@app.route("/hapus_tingkat", methods=["POST"])
def hapus_tingkat():
	c = sqlite3.connect(path_database())
	c.row_factory = sqlite3.Row
	crs = c.cursor()
	data = request.json
	
	crs.execute(f"DELETE FROM {data.get('path', '')} WHERE id_produk = ?", (data.get("id", ""), ))
	c.commit()
	c.close()
	return "Berhasil", 200
		
@app.route("/tambah_tingkat_produk", methods=["POST"])
def tambah_tingkat_produk(): #dijadwalkan
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	path = data.get("path", "")
	cursor.execute(f"SELECT * FROM {path} WHERE id_produk = ?", (data.get("id_produk", ""), ))
	prod = cursor.fetchone()
	if not prod:
		cursor.execute(f"INSERT INTO {path} (id_produk, barcode, nama, harga_modal, harga_jual, min_beli) VALUES (?, ?, ?, ?, ?, ?)", (data.get("id_produk", ""), data.get("barcode", ""), data.get("nama", ""), data.get("harga_modal", 0), data.get("harga_jual", 0), data.get("min_beli", 0)))
	else:
		return "Gagal", 400
		
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/hapus_produk_bertingkat", methods=["POST"])
def hapus_produk_bertingkat():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	data = request.json
	cursor.execute("DELETE FROM produk_tingkat WHERE nama = ?", (data.get("nama", ""), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200
		
@app.route("/penjualan_tingkat", methods=["POST"])
def penjualan_tingkat():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	data = request.json
	
	keranjang = data.get("items", [])
	
	cursor.execute("SELECT * FROM produk")
	produk = cursor.fetchall()
	cursor.execute("SELECT * FROM produk_tingkat")
	produk_tingkat = cursor.fetchall()
	cursor.execute("SELECT persen, aktif FROM pajak")
	pjk = cursor.fetchone()
	
	untung, masuk, total_poin = 0, 0, 0
	for k in keranjang:
		nama = k.get("nama", "")
		qty = k.get("qty", 0)
		harga = k.get("harga", 0)
		
		if pjk["aktif"] == 1:
			harga_asli = harga / (1 + pjk["persen"] / 100)
			nilai_pajak = harga - harga_asli
			cursor.execute("INSERT INTO riwayat_pajak (waktu, nama, pajak) VALUES (?, ?, ?)", (data.get("waktu", ""), nama, nilai_pajak * qty))
		else:
			harga_asli = harga
			
		satuan = k.get("satuan", "")
		
		for p in produk_tingkat:
			if p["nama"].lower() == nama.lower() and p["satuan"].lower() == satuan.lower():
				min = p["minimum_qty"]
				qty_asli = min * qty
				
				nama_pisah = p["nama"].split()
				nama_asli = " ".join(nama_pisah[:-1])
				
				for q in produk:
					if q["nama"].lower() == nama_asli.lower() or q["barcode"] == p["barcode"]:
						jumlah_baru = q["jumlah"] - qty_asli
						cursor.execute("UPDATE produk SET jumlah = ? WHERE id = ?", (jumlah_baru, q["id"]))
						harga_modal = q["harga_modal"]
						barcode = q["barcode"]
						subtotal_modal = harga_modal * qty_asli
						subtotal = harga_asli * qty
						laba = subtotal - subtotal_modal
						untung += laba
						masuk += subtotal
						total_poin += q["poin"] * qty_asli
						cursor.execute("INSERT INTO detail_riwayat_penjualan (operator, sumber, waktu, no_trans, produk, barcode, qty, harga_modal, subtotal_modal, harga_jual, subtotal, laba) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (data.get("operator", ""), data.get("sumber", ""), data.get("waktu", ""), data.get("no_trans", ""), nama, barcode, qty, harga_modal, subtotal_modal, harga, harga * qty, laba))
						break
						
	cursor.execute("SELECT pemasukan, keuntungan FROM keuangan")
	money = cursor.fetchone()
	pemasukan_baru = money["pemasukan"] + masuk
	keuntungan_baru = money["keuntungan"] + untung
	cursor.execute("UPDATE keuangan SET pemasukan = ?, keuntungan = ? WHERE id = ?", (pemasukan_baru, keuntungan_baru, 1))
	
	pembeli = data.get("pembeli", "")
	if pembeli.lower() != "customer":
		parts = pembeli.split()
		if len(parts) < 2:
			return "Gagal", 400
			
		nama = " ".join(parts[:-1])
		kontak = parts[-1]
		cursor.execute("SELECT * FROM customer WHERE nama = ? OR kontak = ?", (nama, kontak))
		cust = cursor.fetchone()
		if cust:
			cursor.execute("UPDATE customer SET poin = ? WHERE id = ?", (cust["poin"] + total_poin, cust["id"]))
		else:
			cursor.execute("INSERT INTO customer (nama, kontak, poin) VALUES (?, ?, ?)", (nama, kontak, total_poin))
	else:
		nama = ""
	cursor.execute("INSERT INTO riwayat_penjualan (waktu, aksi, total, total_laba, no_trans, operator, sumber, pembeli) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (data.get("waktu", ""), "Closing produk", data.get("total", 0), round(untung), data.get("no_trans", ""), data.get("operator", ""), data.get("sumber", ""), nama))

	conn.commit()
	conn.close()
	return "Berhasil", 200				

@app.route("/tambah_stok", methods=["POST"])
def tambah_stok(): #dijadwalkan
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	data = request.json
	d = data.get("data_tambah", {})
	r = data.get("riwayat", {})
	
	cursor.execute("SELECT jumlah FROM produk WHERE nama = ? OR barcode = ?", (d.get("nama", ""), d.get("barcode", "")))
	produk = cursor.fetchone()
	jumlah_baru = produk["jumlah"] + d.get("tambahan", 0)
	
	cursor.execute("UPDATE produk SET jumlah = ?, jumlah_tertinggi = ? WHERE nama = ? OR barcode = ?", (jumlah_baru, d.get("jumlah_tertinggi", 0), d.get("nama", ""), d.get("barcode", "")))
	
	cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, stok_terbaru, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (r.get("waktu", ""), r.get("aksi", ""), r.get("nama", ""), r.get("jumlah", 0), r.get("barcode", ""), r.get("stok_terbaru", 0), r.get("operator", ""), r.get("sumber", "")))
	
	conn.commit()
	conn.close()
	return jsonify({"status": "Berhasil", "pesan": f"Stok produk {d.get('nama', '')} saat ini: {r.get('stok_terbaru', 0)}"}), 200
		
@app.route("/tulis_struk", methods=["POST"])
def tulis_struk():
	d = request.json
	nama = d.get("nama", "")
	struk = d.get("struk", "")
	
	os.makedirs(folder_struk, exist_ok=True)
	file_path = os.path.join(folder_struk, nama + ".txt")
	try:
		with open(file_path, "w", encoding="utf-8") as f:
			f.write(struk)
	except Exception:
		return "Gagal", 400
	return "Berhasil", 200
	
@app.route("/tambah_anggota_shift", methods=["POST"])
def tambah_anggota_shift():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE shift SET anggota = ? WHERE id_shift = ?", (json.dumps(data.get("data", [])), data.get("shift", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/tambah_shift", methods=["POST"])
def tambah_shift():
	data = request.json
	nama = data.get("nama", "")
	id = datetime.now().strftime("%f")
	list_data = []
	for (i, v) in data.get("anggota", []):
		list_data.append({
			"nama": i,
			"inisial_code": v
		})
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("INSERT INTO shift (id_shift, nama_shift, anggota, waktu_mulai, waktu_selesai) VALUES (?, ?, ?, ?, ?)", (id, nama, json.dumps(list_data), data.get("mulai", ""), data.get("selesai", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/riwayat_logout", methods=["POST"])
def riwayat_logout():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE riwayat_login SET waktu_logout = ? WHERE nama = ? or inisial_code = ?", (data.get("waktu", ""), data.get("nama", ""), data.get("inisial_code", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/hapus_riwayat_login", methods=["POST"])
def hapus_riwayat_login():
	conn = sqlite3.connect(path_database())
	cursor = conn.cursor()
	cursor.execute("DELETE FROM riwayat_login")
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/tambah_riwayat_login", methods=["POST"])
def tambah_riwayat_login():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT nama, inisial_code FROM user")
	ident = cursor.fetchall()
	
	pengenal = data.get("pengenal", "")
	
	identitas_pengenal, nama, inisial_code = None, None, None
	for p in ident:
		if p["nama"].lower() == pengenal.lower():
			identitas_pengenal = pengenal
			nama = p["nama"]
			inisial_code = p["inisial_code"]
			break
		elif p["inisial_code"] == pengenal:
			identitas_pengenal = pengenal
			nama = p["nama"]
			inisial_code = p["inisial_code"]
			break
		else:
			identitas_pengenal = "Unknown"
			nama = pengenal
			inisial_code = pengenal	

	cursor.execute("INSERT INTO riwayat_login (id_pengenal, nama, inisial_code, waktu, device, login_menggunakan, kesalahan_login) VALUES (?, ?, ?, ?, ?, ?, ?)", (identitas_pengenal, nama, inisial_code, data.get("waktu", ""), data.get("device", ""), data.get("tipe_login", ""), data.get("poin_kesalahan", 0)))
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/logout_customer", methods=["POST"])
def logout_customer():
	data = request.json
	if not data:
		return jsonify({"stat": "Kosong", "pesan": "Data kosong!"}), 400
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("UPDATE customer SET status_login = ? WHERE id_device = ? OR id_user = ?", (False, data.get("idev", ""), data.get("idUser", "")))
		conn.commit()
		return jsonify({"stat": "Berhasil", "pesan": "Sampai jumpa lagi!!"}), 200
	except sqlite3.Error as e:
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	except Exception as e:
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	finally:
		if conn:
			conn.close()
			
@app.route("/login_customer", methods=["POST"])
def login_customer():
	data = request.json
	if not data:
		return jsonify({"stat": "Gagal", "pesan": "Data kosong"}), 400
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT password, nama, id_user FROM customer WHERE kontak = ? OR email = ?", (data.get("username", ""), data.get("username", "")))
		cs = cursor.fetchone()
		if cs:
			if pbkdf2_sha256.verify(data.get("password", ""), cs["password"]):
				cursor.execute("UPDATE customer SET status_login = ? WHERE kontak = ? OR email = ?", (True, data.get("username", ""), data.get("username", "")))
				conn.commit()
				return jsonify({"stat": "Berhasil", "pesan": f"Selamat datang kembali {cs['nama']}", "id": cs["id_user"]}), 200
			else:
				return jsonify({"stat": "Gagal", "pesan": "Kata sandi salah!"}), 400
		else:
			return jsonify({"stat": "Gagal", "pesan": "Nomor telepon atau email tidak terdaftar!"}), 400
	except sqlite3.Error as e:
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	except Exception as e:
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	finally:
		if conn:
			conn.close()
	
@app.route("/hapus_produk_macet", methods=["POST"])
def hapus_produk_macet():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("DELETE FROM produk WHERE nama = ?", (data.get("nama", ""), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/hapus_produk_perkategori", methods=["POST"])
def hapus_produk_perkategori():
	data = request.json
	
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	placeholder = ",".join(["?"] * len(data.get("data", [])))
	cursor.execute(f"DELETE FROM produk WHERE kategori IN ({placeholder})", data.get("data", []))
	conn.commit()
	conn.close()
	return "Berhasil", 200 
	
@app.route("/tambah_saldo", methods=["POST"])
def tambah_saldo():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT saldo FROM keuangan")
	da = cursor.fetchone()
	saldo_baru = da["saldo"] + int(data.get("uang", 0))
	cursor.execute("UPDATE keuangan SET saldo = ? WHERE id = ?", (saldo_baru, 1))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/tambah_tipe_gambar_struk", methods=["POST"])
def tambah_tipe_gambar_struk():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute("SELECT * FROM status_qr")
	d = c.fetchall()
	if not d:
		c.execute("INSERT INTO status_qr (status, tipe) VALUES (?, ?)", (1, data.get("tipe", "")))
	else:
		c.execute("UPDATE status_qr SET tipe = ? WHERE id = ?", (data.get("tipe", ""), 1))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/cetak_qr_di_struk", methods=["POST"])
def cetak_qr_di_struk():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM status_qr")
	d = cursor.fetchall()
	if not d:
		cursor.execute("INSERT INTO status_qr (status, tipe) VALUES (?, ?)", (data.get("status", 0), "Barcode"))
	else:
		cursor.execute("UPDATE status_qr SET status = ? WHERE id = ?", (data.get("status", 0), 1))	
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/get_gambar_detail", methods=["POST"])
def get_gambar_detail():
	data = request.json
	if not data:
		return jsonify({"stat": "Gagal", "pesan": "Data kosong"}), 400
		
	path = os.path.join(folder_katalog, data.get("nama", "") + ".jpeg")
	if not os.path.exists(path):
		return send_file("MyHTML/defaultProduk.jpeg", mimetype="image/jpeg")
	return send_file(path, mimetype="image/jpeg")
	
@app.route("/pajak_selalu_aktif", methods=["POST"])
def pajak_selalu_aktif():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE pajak SET aktif = ? WHERE id = ?", (data.get("aktif", 0), 1))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/create_barcode", methods=["POST"])
def create_barcode():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE produk SET barcode = ? WHERE nama = ?", (data.get("kar", ""), data.get("nama", "")))
	conn.commit()
	
	barcode_type = "code128"
	filename = data.get("nama", "")
	barcode_class = barcode.get(barcode_type, data.get("kar", ""), writer=ImageWriter())
	filepath = os.path.join(folder_foto, filename)
	barcode_class.save(filepath)
	file_return = os.path.join(folder_foto, filename + ".png")
	conn.close()
	return send_file(file_return, mimetype="image/png")

@app.route("/ganti_barcode", methods=["POST"])
def ganti_barcode():
	conn = None
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()	
		file = request.files["file"]
		if not file:
			return "File kosong", 400
			
		barcode = request.form.get("barcode", "")
		id = request.form.get("id", "")
		if not all([barcode, id]):
			return "Barcode dan id kosong", 400
	
		cursor.execute("SELECT nama FROM produk WHERE id_produk = ?", (id, ))
		n = cursor.fetchone()
		file_name = n["nama"] + ".png"
		path = os.path.join(folder_foto, file_name)
		file.save(path)
		
		cursor.execute("UPDATE produk SET barcode = ? WHERE id_produk = ?", (barcode, id))
		conn.commit()
		return "Berhasil", 200
	except Exception as e:
		conn.rollback()
		return str(e), 500
	finally:
		if conn:
			conn.close()		
		
@app.route("/reset_izin", methods=["POST"])
def reset_izin():
	conn = sqlite3.connect(path_database())
	cursor = conn.cursor()
	cursor.execute("DELETE FROM hak_akses")
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/pulihkan_backup", methods=["POST"])
def pulihkan_backup():
	data = request.json
	nama = data.get("nama", "")
	try:
		backup_file = f"Folder backup/{nama}"
		if not backup_file:
			return "File kosong", 401
		db_main = "pos.db"
		try:
			with open(db_main, "r+b") as f:
				pass
		except PermissionError:
			return "Database sedang digunakan!", 401
		if os.path.exists(db_main):
			shutil.copy2(db_main, f"Pos sementara {datetime.now().strftime('%d%m%y')}")
		shutil.copy2(backup_file, db_main)
		return "Berhasil", 200
	except Exception:
		return "Gagal", 500
	
@app.route("/buat_backup", methods=["POST"])
def buat_backup():
	data = request.json
	conn = sqlite3.connect(path_database())
	try:
		path = os.path.join(folder_backup, f"Pos_{data.get('waktu', '')}.db")
		crm = sqlite3.connect(path)
		conn.backup(crm)
		return "Berhasil", 200
	except Exception:
		return "Gagal", 401
		
@app.route("/tambah_izin", methods=["POST"])
def tambah_izin():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("DELETE FROM hak_akses WHERE status = ?", (data.get("status", ""), ))
	cursor.execute("INSERT INTO hak_akses (status, izin) VALUES (?, ?)", (data.get("status", ""), data.get("izin", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/upload_foto_profil", methods=["POST"])
def upload_foto_profil():
	file = request.files.get("file")
	if not file:
		return jsonify({"stat": "Gagal", "pesan": "File kosong"}), 400
	os.makedirs(folder_foto, exist_ok=True)
	img = Image.open(file.stream).convert("RGB")
	img = img.resize((300, 300), Image.LANCZOS)
	file_name = "foto profil.png"
	file_path = os.path.join(folder_foto, file_name)
	img.save(file_path, "png", quality=90, optimize=True)
	return jsonify({"stat": "Berhasil", "pesan": "Foto profil toko telah diperbarui"}), 200

@app.route("/get_katalog", methods=["POST"])
def get_katalog():
	data = request.json
	if not data:
		return jsonify({"error": "No data provided"}), 400
	real_path = os.path.join(folder_katalog, data.get("nama", "") + ".jpeg")
	thumb_path = os.path.join(folder_katalog, data.get("nama", "") + "_thumb.jpeg")
	if not os.path.exists(thumb_path):
		if os.path.exists(real_path):
			img = Image.open(real_path)
			img.thumbnail((300, 300))
			img.save(thumb_path, optimize=True, quality=85)
		else:
			return send_from_directory(folder_atribut, "defaultProdukthumb.png", max_age=3600)
	return send_from_directory(folder_katalog, data.get("nama", "") + "_thumb.jpeg", max_age=3600)

@app.route("/get_gambar", methods=["POST"])
def get_gambar():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    nama_file = data.get("nama", "")
    path = f"/storage/emulated/0/proyekku/MyHTML/{nama_file}"
    
    if not os.path.exists(path):
        return send_file("MyHTML/defaultProduk.jpeg", mimetype="image/jpeg")
    
    return send_file(path, mimetype="image/jpeg")

@app.route("/upload_foto_katalog", methods=["POST"])
def upload_foto_katalog(): #dijadwalkan
	nama = request.form.get("nama")
	file = request.files.get("foto")
	if not nama or not file:
		return jsonify({"Error": "Data tidak lengkap!"}), 400
	os.makedirs(folder_katalog, exist_ok=True)
	img = Image.open(file.stream).convert("RGB")
	
	path = os.path.join(folder_katalog, nama + ".jpeg")
	img.save(path, "jpeg", quality=90, optimize=True)
	
	img_crop = img.resize((300,300), Image.LANCZOS)
	thumb_path = os.path.join(folder_katalog, nama + "_thumb.jpeg")
	img_crop.save(thumb_path, "jpeg", quality=90, optimize=True)
	
	return jsonify({"status": "Berhasil"}), 200

@app.route("/hapus_cadangan", methods=["POST"])
def hapus_cadangan():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("DELETE FROM cadangan_keranjang WHERE no = ?", (data.get("no", ""), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/pajak_persen", methods=["POST"])
def pajak_persen():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT persen FROM pajak")
	pjk = cursor.fetchone()
	if pjk:
		cursor.execute("UPDATE pajak SET persen = ? WHERE id = ?", (data.get("persen_pajak", 0), 1))
	else:
		cursor.execute("INSERT INTO pajak (persen) VALUE (?)", (data.get("persen_pajak", 0), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/cadangkan_keranjang", methods=["POST"])
def cadangkan_keranjang():
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		
		data = request.json
		keranjang = json.dumps(data.get("keranjang", []))
		cursor.execute("SELECT * FROM cadangan_keranjang WHERE no = ?", (data.get("no", ""), ))
		d = cursor.fetchone()
		if d:
			cursor.execute("UPDATE cadangan_keranjang SET nama_pembeli = ?, jumlah_dibayar = ?, status = ?, keranjang = ? WHERE no = ?", (data.get("nama", ""), d["jumlah_dibayar"] + data.get("dibayar", 0), "Belum lunas", keranjang, data.get("no", "")))
		else:
			cursor.execute("INSERT INTO cadangan_keranjang (no, nama_pembeli, jumlah_dibayar, status, keranjang) VALUES (?, ?, ?, ?, ?)", (data.get("no", ""), data.get("nama", ""), data.get("dibayar", 0), data.get("status", ""), keranjang))
		conn.commit()
		return jsonify({
			"stat": "Berhasil",
			"pesan": "Keranjang telah disimpan"
		}), 200
		
	except Exception as e:
		conn.rollback()
		return jsonify({
			"stat": "Error",
			"pesan": f"Error: {str(e)}"
		}), 500
	finally:
		if conn:
			conn.close()
			
@app.route("/hapus_rekening", methods=["POST"])
def hapus_rekening():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("DELETE FROM media_bayar WHERE nomor_rekening = ?", (data.get("rekening", ""), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/upload_pembayaran", methods=["POST"])
def upload_pembayaran():
	data = request.files.get("data_json")
	if data:
		try:
			data_json = json.load(data)
		except Exception as e:
			return jsonify({
				"stat": "error",
				"pesan": f"Gagal membaca JSON: {e}"
			}), 400
			
	else:
		return jsonify({
			"stat": "error",
			"pesan": "File JSON tidak ditemukan"
		}), 400
		
	img_file = request.files.get("data_qr")
	if img_file:
		img_path = os.path.join(folder_pembayaran, img_file.filename)
		img_file.save(img_path)
	else:
		return jsonify({
			"stat": "error",
			"pesan": "File QR tidak ditemukan"
		}), 400
	conn = None
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT nomor_rekening FROM media_bayar")
		data_pembayaran = cursor.fetchall()
		same = False
		for x in data_pembayaran:
			if x["nomor_rekening"] == data_json.get("norek", ""):
				same = True
				break
		if not same:
			cursor.execute("INSERT INTO media_bayar (bank, nama_pemilik, nomor_rekening) VALUES (?, ?, ?)", (data_json.get("bank", ""), data_json.get("nama", ""), data_json.get("norek", "")))
		conn.commit()
		return jsonify({
			"stat": "Berhasil",
			"pesan": "Data media pembayaran baru telah ditambahkan"
		}), 200
	except Exception as e:
		conn.rollback()
		return jsonify({
			"stat": "Error",
			"pesan": str(e)
		}), 500
	finally:
		if conn:		
			conn.close()
		
@app.route("/penjualan", methods=["POST"])
def penjualan():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	data = request.json
	data_jual = data.get("data", [])
	bayar = data.get("bayar", 0)
	waktu = data.get("waktu", "")
	pajak_value = data_jual.get("pajak", 0)
	keranjang = data_jual.get("items", [])
	
	cursor.execute("SELECT * FROM produk")
	produk = cursor.fetchall()
	cursor.execute("SELECT persen FROM pajak")
	pjk = cursor.fetchone()
	
	total_poin, pemasukan, keuntungan = 0, 0, 0
	for k in keranjang:
		nama = k.get("nama", "")
		barcode = k.get("barcode", "")
		qty = k.get("qty", 0)
		harga = k.get("harga", 0)
		
		if pajak_value == 1:
			harga_asli = harga / (1 + pjk["persen"] / 100)
			nilai_pajak = harga - harga_asli
			cursor.execute("INSERT INTO riwayat_pajak (waktu, nama, pajak) VALUES (?, ?, ?)", (waktu, nama, nilai_pajak * qty))
		else:
			harga_asli = harga
			
		for p in produk:
			if p["nama"].lower() == nama.lower() or p["barcode"] == barcode:
				jumlah_baru = p["jumlah"] - qty
				cursor.execute("UPDATE produk SET jumlah = ? WHERE id = ?", (jumlah_baru, p["id"]))
				harga_modal = p["harga_modal"]
				subtotal_modal = harga_modal * qty
				subtotal = harga_asli * qty
				laba = subtotal - subtotal_modal
				keuntungan += laba
				pemasukan += subtotal
				total_poin += p["poin"] * qty
				cursor.execute("INSERT INTO detail_riwayat_penjualan (operator, sumber, waktu, no_trans, produk, barcode, qty, harga_modal, subtotal_modal, harga_jual, subtotal, laba) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (data_jual.get("operator", ""), data_jual.get("sumber", ""), waktu, data_jual.get("no_trans", ""), nama, barcode, qty, harga_modal, subtotal_modal, harga, harga * qty, laba))
				break
	
	cursor.execute("SELECT pemasukan, keuntungan FROM keuangan")
	money = cursor.fetchone()
	pemasukan_baru = money["pemasukan"] + pemasukan
	keuntungan_baru = money["keuntungan"] + keuntungan
	cursor.execute("UPDATE keuangan SET pemasukan = ?, keuntungan = ? WHERE id = ?", (pemasukan_baru, keuntungan_baru, 1))
	
	pembeli = data_jual.get("pembeli", "")
	if pembeli.lower() != "customer":
		parts = pembeli.split()
		if len(parts) < 2:
			return "Gagal", 400
			
		nama = " ".join(parts[:-1])
		kontak = parts[-1]
		cursor.execute("SELECT * FROM customer WHERE nama = ? OR kontak = ?", (nama, kontak))
		cust = cursor.fetchone()
		if cust:
			cursor.execute("UPDATE customer SET poin = ? WHERE id = ?", (cust["poin"] + total_poin, cust["id"]))
		else:
			cursor.execute("INSERT INTO customer (nama, kontak, poin) VALUES (?, ?, ?)", (nama, kontak, total_poin))
	else:
		nama = ""
	cursor.execute("INSERT INTO riwayat_penjualan (waktu, aksi, total, total_laba, no_trans, operator, sumber, pembeli) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (waktu, "Closing produk", data_jual.get("total", 0), round(keuntungan), data_jual.get("no_trans", ""), data_jual.get("operator", ""), data_jual.get("sumber", ""), nama))

	conn.commit()
	conn.close()
	return "Berhasil", 200
			
@app.route("/tambah_profil", methods=["POST"])
def tambah_profil():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM profil")
	p = cursor.fetchone()
	if not p:
		cursor.execute("INSERT INTO profil (nama, alamat, kontak, email, website, jenis) VALUES (?, ?, ?, ?, ?, ?)", (data.get("nama", ""), data.get("alamat", ""), data.get("kontak", ""), data.get("email", ""), data.get("website", ""), data.get("jenis", "")))
	else:
		cursor.execute("UPDATE profil SET nama = ?, alamat = ?, kontak = ?, email = ?, website = ?, jenis = ? WHERE id = ?", (data.get("nama", ""), data.get("alamat", ""), data.get("kontak", ""), data.get("email", ""), data.get("website", ""), data.get("jenis", ""), 1))
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/ekspor_produk_terpilih", methods=["POST"])
def ekspor_produk_terpilih():
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()	
	data = request.json
	if not data:
		return "Kosong", 400
	command = data.get("command", "")
	data_sama = data.get("sama", [])
	data_tidak_sama = data.get("tidak_sama", [])
	
	def insert_produk(p, j):
		data_insert = (
			p["id_produk"],
			p["barcode"],
			p["nama"],
			p["kategori"],
			p["catatan"],
			p["kadaluarsa"],
			p["satuan_beli"],
			p["satuan_jual"],
			p["isi_satuan"],
			p["harga_beli"],
			p["harga_modal"],
			p["harga_jual"],
			j,
			p["jumlah_tertinggi"],
			p["stok_minimum"],
			p["poin"],
			p["supplier"]
		)
		cursor.execute("""INSERT INTO produk
		(id_produk, barcode, nama, kategori,
		catatan, kadaluarsa, satuan_beli, satuan_jual,
		isi_satuan, harga_beli, harga_modal, harga_jual,
		jumlah, jumlah_tertinggi, stok_minimum, poin, supplier)
		values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data_insert)
		
	if command == "overwrite":
		for p in data_sama:
			cursor.execute("DELETE FROM produk WHERE id_produk = ?", (p["id_produk"], ))
			insert_produk(p, p["jumlah"])
		for p in data_tidak_sama:
			insert_produk(p, p["jumlah"])
	elif command == "merge":
		for p in data_sama:
			cursor.execute("SELECT jumlah FROM produk WHERE id_produk = ?", (p["id_produk"], ))
			jml = cursor.fetchone()
			jumlah_baru = jml["jumlah"] + p["jumlah"]
			cursor.execute("DELETE FROM produk WHERE id_produk = ?", (p["id_produk"], ))
			insert_produk(p, jumlah_baru)
		for p in data_tidak_sama:
			insert_produk(p, p["jumlah"])
	else:
		for p in data_tidak_sama:
			insert_produk(p, p["jumlah"])
	conn.commit()
	conn.close()
	return "Berhasil", 200
											
@app.route("/ekspor_produk", methods=["POST"])
def ekspor_produk():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("DELETE FROM produk")
	
	cursor.executemany("INSERT INTO produk (id_produk, barcode, nama, kategori, catatan, kadaluarsa, satuan_beli, satuan_jual, isi_satuan, supplier, harga_beli, harga_modal, harga_jual, jumlah, jumlah_tertinggi, stok_minimum, poin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
	conn.commit()
	conn.close()
		
	return "Berhasil", 200
	
@app.route("/tambah_produk_tingkat", methods=["POST"])
def tambah_produk_bertingkat():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()

	cursor.execute("INSERT INTO produk_tingkat (barcode, nama, satuan, minimum_qty, harga_jual, harga_modal, stok, poin, kategori, kadaluarsa) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (data.get("barcode", ""), data.get("nama", ""), data.get("satuan", ""), data.get("min", 0), data.get("harga_jual", 0), data.get("harga_modal", 0), data.get("stok", 0), data.get("poin", 0), data.get("kategori", ""), data.get("kadaluarsa", "")))
	
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/tambah_produk_diskon", methods=["POST"])
def tambah_produk_diskon(): #dijadwalkan
	data = request.json
	d = data.get("data", {})
	r = data.get("riwayat", {})
	
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute("SELECT * FROM produk_diskon WHERE barcode = ? OR nama = ?", (d.get("barcode", ""), d.get("nama", "")))
	ex = cursor.fetchone()
	if ex:
		cursor.execute("UPDATE produk_diskon SET persen = ?, min = ? WHERE id = ?", (d.get("persen", 0), d.get("min", 0), ex["id"]))
	else:
		cursor.execute("INSERT INTO produk_diskon (barcode, nama, harga_jual, persen, min) VALUES (?, ?, ?, ?, ?)", (d.get("barcode", ""), d.get("nama", ""), d.get("harga_jual", 0), d.get("persen", 0), d.get("min", 0)))
	cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, barcode, jumlah, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (r.get("waktu", ""), r.get("aksi", ""), r.get("nama", ""), r.get("barcode", ""), r.get("jumlah", 0), r.get("operator", ""), r.get("sumber", "")))

	conn.commit()
	conn.close()
	return "Berhasil", 200
		
@app.route("/edit_produk", methods=["POST"])
def edit_produk(): #dijadwalkan
	data = request.json
	e = data.get("data", {})
	r = data.get("riwayat", {})
	md = int(e.get("harga_beli", 0)) / int(e.get("isi_satuan", 0))
	
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE produk SET barcode = ?, nama = ?, catatan = ?, kategori = ?, kadaluarsa = ?, satuan_beli = ?, satuan_jual = ?, isi_satuan = ?, harga_beli = ?, harga_jual = ?, jumlah = ?, stok_minimum = ?, supplier = ?, jumlah_tertinggi = ?, harga_modal = ?, poin = ? WHERE id = ?", (e.get("barcode", ""), e.get("nama", ""), e.get("catatan", ""), e.get("kategori", ""), e.get("kadaluarsa", ""), e.get("satuan_beli", ""), e.get("satuan_jual", ""), e.get("isi_satuan", 0), e.get("harga_beli", 0), e.get("harga_jual", 0), e.get("jumlah", 0), e.get("stok_minimum", 0), e.get("supplier", ""), e.get("jumlah_tertinggi", 0), md, e.get("poin", 0), e.get("id", "")))
	
	cursor.execute("INSERT INTO riwayat (waktu, aksi, nama_lama, nama, jumlah_lama, jumlah, modal_lama, harga_modal, jual_lama, harga_jual, catatan_lama, catatan, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (r.get("waktu", ""), r.get("aksi", ""), r.get("nama_lama", ""), r.get("nama", ""), r.get("jumlah_lama", 0), r.get("jumlah", 0), r.get("modal_lama", 0), r.get("harga_modal", 0), r.get("jual_lama", 0), r.get("harga_jual", 0), r.get("catatan_lama", ""), r.get("catatan", ""), r.get("barcode", ""), r.get("operator", ""), r.get("sumber", "")))
	conn.commit()	
	conn.close()
	return "Berhasil", 200

@app.route("/hapus_produk", methods=["POST"])
def hapus_produk():
	data = request.json
	if not data:
		return jsonify({
			"stat": "Kosong",
			"pesan": "Data kosong"
		}), 400
		
	conn = None
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (data.get("waktu", now_str()), data.get("aksi", ""), data.get("nama", ""), data.get("jumlah", 0), data.get("barcode", ""), data.get("operator", ""), data.get("sumber", "")))
		cursor.execute("DELETE FROM produk WHERE id = ?", (data.get("id", ""), ))
		conn.commit()
		return jsonify({"stat": "Berhasil", "pesan": "Data produk telah dihapus"}), 200
	
	except sqlite3.Error as e:
		conn.rollback()
		return jsonify({"stat": "Gagal", "pesan": str(e)}), 500

	except Exception as e:
		conn.rollback()
		return jsonify({"stat": "Gagal", "pesan": str(e)}), 500
	finally:
		if conn:
			conn.close()

@app.route("/ubah_password", methods=["POST"])
def ubah_password():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE user SET password = ? WHERE id = ?", (data.get("password_baru", ""), data.get("id", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/edit_margin", methods=["POST"])
def edit_margin():
	d = request.json
	data = d.get("data", {})
	riw = d.get("riwayat", {})
	
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute("UPDATE margin SET kategori = ?, margin = ? WHERE id = ?", (data.get("kategori", ""), data.get("margin", 0), data.get("id", "")))
	cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (riw.get("waktu", ""), riw.get("aksi", ""), riw.get("nama", ""), riw.get("jumlah", 0), riw.get("barcode", ""), riw.get("operator", ""), riw.get("sumber", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/tambah_user", methods=["POST"])
def tambah_user():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("INSERT INTO user (nama, status, inisial, inisial_code, password, pertanyaan, jawaban) VALUES (?, ?, ?, ?, ?, ?, ?)", (data.get("nama", ""), data.get("status", ""), data.get("inisial", ""), data.get("inisial_code", ""), data.get("password", ""), data.get("pertanyaan", ""), data.get("jawaban", "")))
	cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Tambah pengguna", data.get("nama", ""), 1, data.get("inisial_code", ""), data.get("operator", ""), data.get("sumber", "")))
	conn.commit()
	conn.close()
	
	def choose_color():
		return random.choice(["darkblue", "black", "darkred", "purple"])
	teks = f"{data.get('inisial_code', '')} {data.get('pw', '')}"
	qr_teks = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
	qr_teks.add_data(teks)
	qr_teks.make(fit=True)
	
	img = qr_teks.make_image(fill_color=choose_color(), back_color="white")
	path = os.path.join(folder_foto, f"{data.get('nama', '')} {data.get('inisial_code', '')}.jpeg")
	img.save(path, "jpeg", quality=90, optimize=True)
	
	return "Berhasil", 200
	
@app.route("/lupa_password", methods=["POST"])
def lupa_password():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE user SET password = ? WHERE inisial_code = ?", (pbkdf2_sha256.hash(data.get("pass", "")), data.get("inisial_code", "")))
	
	teks = data.get("inisial_code", "") + " " + data.get("pass", "")
	qr_teks = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
	qr_teks.add_data(teks)
	qr_teks.make(fit=True)
	
	img = qr_teks.make_image(fill_color="black", back_color="white")
	path = os.path.join(folder_foto, f"{data.get('nama', '')} {data.get('inisial_code', '')}.jpeg")
	img.save(path, "jpeg", quality=90, optimize=True)
	conn.commit()
	conn.close()
	return "Berhasil", 200	

@app.route("/edit_user", methods=["POST"])
def edit_user():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE user SET nama = ?, status = ?, pertanyaan = ?, jawaban = ? WHERE inisial_code = ?", (data.get("nama", ""), data.get("status", ""), data.get("pertanyaan", ""), data.get("jawaban", ""), data.get("inisial_code", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/hapus_user", methods=["POST"])
def hapus_user():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("DELETE FROM user WHERE inisial_code = ?", (data.get("id", ""), ))
	conn.commit()
	conn.close()
	return "Berhasil", 200

@app.route("/hapus_profil", methods=["POST"])
def hapus_profil():
	conn = sqlite3.connect(path_database())
	cursor = conn.cursor()
	cursor.execute("DELETE FROM profil")
	conn.commit()
	conn.close()
	return "Berhasil", 200
	
@app.route("/edit_supplier", methods=["POST"])
def edit_supplier():
	data = request.json
	conn = sqlite3.connect(path_database())
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("UPDATE supplier SET nama = ?, alamat = ?, kontak = ?, email = ?, medsos = ?, bidang = ? WHERE id = ?", (data.get("nama", ""), data.get("alamat", ""), data.get("kontak", ""), data.get("email", ""), data.get("medsos", ""), data.get("bidang", ""), data.get("id", "")))
	cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Edit supplier", data.get("nama", ""), 1, "-", data.get("operator", ""), data.get("sumber", "")))
	conn.commit()
	conn.close()
	return "Berhasil", 200
			
@app.route("/tambah_produk", methods=["POST"])
def tambah_produk(): #dijadwalkan
	data = request.json
	id_prd = datetime.now().strftime("%f")
	
	try:
		conn = sqlite3.connect(path_database())
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("SELECT barcode, nama FROM produk")
		p = cursor.fetchall()
		for x in p:
			if x["barcode"] == data.get("barcode", "") or x["nama"].lower() == data.get("nama", "").lower():
				return jsonify({"stat": "Gagal", "pesan": "Produk sudah ada"}), 401

		cursor.execute("INSERT INTO produk (id_produk, barcode, nama, kategori, catatan, kadaluarsa, satuan_beli, satuan_jual, isi_satuan, supplier, harga_beli, harga_modal, harga_jual, jumlah, jumlah_tertinggi, stok_minimum, poin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id_prd, data.get("barcode", ""), data.get("nama", ""), data.get("kategori", ""), data.get("catatan", ""), data.get("kadaluarsa", ""), data.get("satuan_beli", ""), data.get("satuan_jual", ""), data.get("isi_satuan", 0), data.get("supplier", ""), data.get("harga_beli", 0), data.get("harga_modal", 0), data.get("harga_jual", 0), data.get("jumlah", 0), data.get("jumlah", 0), data.get("stok_minimum", 0), 0))
		cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, barcode, jumlah, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Tambah produk baru", data.get("nama", ""), data.get("barcode", ""), data.get("jumlah", 0), data.get("operator", ""), data.get("sumber", "")))

		cursor.execute("SELECT kategori FROM margin")
		d = cursor.fetchall()
		for y in d:
			if y["kategori"].lower() == data.get("kategori", "").lower():
				break
		else:
			cursor.execute("INSERT INTO margin (kategori, margin) VALUES (?, ?)", (data.get("kategori", ""), 0))

		cursor.execute("SELECT nama FROM supplier")
		d = cursor.fetchall()
		for z in d:
			if z["nama"].lower() == data.get("supplier", "").lower():
				break
		else:
			cursor.execute("INSERT INTO supplier (nama) VALUES (?)", (data.get("supplier", ""), ))
		conn.commit()
		return jsonify({"stat": "Berhasil", "pesan": f"Data produk {data.get('nama', '')} telah ditambahkan"}), 200
	except sqlite3.Error as e:
		return jsonify({"stat": "Gagal", "pesan": str(e)}), 500
	except Exception as e:
		return jsonify({"stat": "Error", "pesan": str(e)}), 500
	finally:
		if conn:
			conn.close()
			
if __name__ == "__main__":
	mode = opsi_server.get("opsi", "local server").lower()
	if mode != "local server" or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
		start_udp_broadcast()
		get_ips()
		get_link()
		print("\n---------------------------")
		print("Link: " + default_url)
		print("---------------------------\n")
	if mode == "local server":
		app.run(host="0.0.0.0", debug=True, port=5000, use_reloader=True)
	else:
		serve(app, host="0.0.0.0", port=5000)
		
		