from PySide6.QtWidgets import QMessageBox as QMB
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QToolButton,
    QLineEdit, QTextEdit, QComboBox, QRadioButton, QButtonGroup,
    QFrame, QScrollArea, QFileDialog, QMessageBox, QMessageBox as QMB,
    QProgressBar, QSizePolicy,
    QHBoxLayout, QVBoxLayout, QGridLayout,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QSize, QTimer, QDate, QPropertyAnimation
from PySide6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut, QStandardItem

from PIL.ImageQt import ImageQt
from PIL import Image, ImageTk
from barcode.writer import ImageWriter
import traceback, shutil, zipfile, sys, random, requests, urllib3, csv, os, json, socket, sqlite3, copy, qrcode, barcode, uuid
from datetime import datetime, timedelta
from Atribut import *
from io import BytesIO
from escpos.printer import Usb, Serial
import usb.core
import usb.util
from passlib.hash import pbkdf2_sha256 as pks
from reportlab.platypus import Table, Spacer, TableStyle, SimpleDocTemplate, Image as RLImage, Paragraph
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.utils import ImageReader
from terbilang import Terbilang
from itertools import product
from Core import LoadingSpinner, LoadingOverlay, diagram_batang, diagram_bolu

"""
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

original_request = requests.Session.request
def new_request(self, method, url, *args, **kwargs):
    kwargs['verify'] = False
    return original_request(self, method, url, *args, **kwargs)
requests.Session.request = new_request
"""

def app_get_data_folder():
	if sys.platform == "win32":
		base = os.path.join(os.environ["LOCALAPPDATA"], "FOLDER DATABASE APP FIXY POINT SINGLE")
	elif sys.platform == "darwin":
		base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "FOLDER DATABASE APP FIXY POINT SINGLE")
	else:
		base = os.path.join(os.path.expanduser("~"), ".local", "share", "FOLDER DATABASE APP FIXY POINT SINGLE")
	return base

basedir = app_get_data_folder()

folder_game = os.path.join(basedir, "Tetris data")
folder = os.path.join(basedir, "Pengaturan Dasar")
folder_foto_profil = os.path.join(basedir, "Foto Profil")
folder_struk = os.path.join(basedir, "Template struk")
folder_katalog = os.path.join(basedir, "Katalog produk")
folder_backup = os.path.join(basedir, "Folder backup")
folder_sqlite = os.path.join(basedir, "DATABASE UTAMA")

for p in [folder_game, folder, folder_foto_profil, folder_struk, folder_katalog, folder_backup, folder_sqlite]:
	os.makedirs(p, exist_ok=True)

file_koneksi = os.path.join(folder, "Koneksi.json")
file_animasi = os.path.join(folder, "Animasi.json")
file_printer = os.path.join(folder_struk, "Printer aktif.json")
file = os.path.join(folder_game, "skor.json")
file_customer = os.path.join(folder, "Customer.json")
file_produk_data = os.path.join(folder, "Produk data.json")
file_A = os.path.join(folder, "Tingkat A.json")
file_B = os.path.join(folder, "Tingkat B.json")
file_diskon_data = os.path.join(folder, "Diskon data.json")
file_profil_data = os.path.join(folder, "Profil data.json")
file_pajak = os.path.join(folder, "Pajak data.json")
file_cadangan_transaksi = os.path.join(folder, "Cadangan transaksi.json")
file_desimal = os.path.join(folder, "Gunakan desimal.json")
file_server = os.path.join(folder_sqlite, "Opsi server.json")

def load_json(path, default):
	if os.path.exists(path):
		try:
			with open(path, "r") as f:
				return json.load(f)
		except:
			return default
	else:
		return default
		
koneksi = load_json(file_koneksi, {"connect": 0})
printer = load_json(file_printer, [])
skor_tertinggi = load_json(file, {"skor": 0})
customer = load_json(file_customer, [])
produk_data = load_json(file_produk_data, [])
A = load_json(file_A, [])
B = load_json(file_B, [])
diskon_data = load_json(file_diskon_data, [])
profil_data = load_json(file_profil_data, [])
pjk = load_json(file_pajak, [])
cadangan_transaksi = load_json(file_cadangan_transaksi, [])
desimal = load_json(file_desimal, {})
animasi = load_json(file_animasi, {"yes": 0})
opsi_server = load_json(file_server, {"opsi": "Local server"})
izin_akses = []

def simpan_semua(path, file):
	if file and isinstance(file, list) and hasattr(file[0], 'keys'):
		file = [dict(row) for row in file]
	
	with open(path, "w") as f:
		json.dump(file, f, indent=4, ensure_ascii=False)

def path_database():
	path = os.path.join(folder_sqlite, "pos.db")
	return path
		
conn = sqlite3.connect(path_database(), check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def create_table(name, table_header):
	cursor.execute(f"""
	CREATE TABLE IF NOT EXISTS {name} (
		id INTEGER PRIMARY KEY AUTOINCREMENT, {table_header})""")
		
create_table("Pengeluaran", "waktu TEXT, nama TEXT, jumlah INTEGER, satuan_jumlah TEXT, harga INTEGER, total INTEGER, kategori TEXT, keterangan TEXT, operator TEXT, sumber TEXT")
create_table("profil", "nama TEXT, alamat TEXT, kontak TEXT, email TEXT, website TEXT, jenis TEXT")
create_table("produk", "id_produk TEXT, barcode TEXT, nama TEXT, kategori TEXT, catatan TEXT, kadaluarsa TEXT, satuan_beli TEXT, satuan_jual TEXT, isi_satuan INTEGER, supplier TEXT, harga_beli INTEGER, harga_modal INTEGER, harga_jual INTEGER, jumlah INTEGER, jumlah_tertinggi INTEGER, stok_minimum INTEGER, poin INTEGER")
create_table("riwayat", "waktu TEXT, aksi TEXT, nama TEXT, nama_lama TEXT, jumlah INTEGER, jumlah_lama INTEGER, modal_lama INTEGER, harga_modal INTEGER, jual_lama INTEGER, harga_jual INTEGER, catatan_lama TEXT, catatan TEXT, stok_terbaru INTEGER, barcode TEXT, operator TEXT, sumber TEXT")
create_table("margin", "kategori TEXT, margin INTEGER")
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
create_table("validasi_owner", "status INTEGER")
create_table("cadangan_keranjang", "no TEXT, nama_pembeli TEXT, jumlah_dibayar INTEGER, status TEXT, keranjang TEXT")
create_table("hak_akses", "status TEXT, izin TEXT")
create_table("universal_printer", "tipe TEXT, info TEXT, status TEXT")
create_table("status_qr", "status INTEGER, tipe TEXT")
create_table("Jenis_font", "nama TEXT, ukuran INTEGER")
create_table("riwayat_login", "id_pengenal TEXT, nama TEXT, inisial_code TEXT, waktu TEXT, device TEXT, login_menggunakan TEXT, kesalahan_login INTEGER, waktu_logout TEXT")
create_table("shift", "id_shift TEXT, nama_shift TEXT, anggota TEXT, waktu_mulai TEXT, waktu_selesai TEXT")
create_table("produk_tingkat", "barcode TEXT, nama TEXT, satuan TEXT, minimum_qty INTEGER, harga_jual REAL, harga_modal REAL, stok INTEGER, poin INTEGER, kategori TEXT, kadaluarsa TEXT")
create_table("tingkat_a", "id_produk TEXT, barcode TEXT, nama TEXT, harga_modal REAL, harga_jual REAL, min_beli INTEGER")
create_table("tingkat_b", "id_produk TEXT, barcode TEXT, nama TEXT, harga_modal REAL, harga_jual REAL, min_beli INTEGER")
create_table("pengaturan_nota", "judul TEXT, catatan TEXT, penerima TEXT, penerbit TEXT")
create_table("riwayat_retur", "waktu TEXT, no_trans TEXT, pembeli TEXT, data TEXT, alasan TEXT")
create_table("pengaturan_font_size", "mono INTEGER, judul INTEGER, subjudul INTEGER, font_bold INTEGER, button INTEGER, label INTEGER")
create_table("pengaturan_format", "bahasa TEXT, format_uang TEXT, format_waktu TEXT")
create_table("pengaturan_tema", "latar TEXT, warna_huruf TEXT, font_normal INTEGER, font_judul INTEGER, ikon INTEGER")
create_table("produk_diskon", "barcode TEXT, nama TEXT, harga_jual INTEGER, persen INTEGER, min INTEGER")
create_table("riwayat_keuangan", "waktu TEXT, jumlah REAL, sumber TEXT, jenis TEXT, saldo_awal REAL, saldo_akhir REAL, pihak_terkait TEXT, keterangan TEXT, id_keuangan TEXT")
create_table("permintaan", "waktu TEXT, jenis TEXT, data TEXT, status TEXT")
conn.commit()

BROADCAST_PORT = 55000  
DISCOVER_MSG = "DISCOVER_SERVER"
TIMEOUT = 2 

def discover_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(TIMEOUT)
    server_ip = None

    try:
        sock.sendto(DISCOVER_MSG.encode(), ('<broadcast>', BROADCAST_PORT))
        data, addr = sock.recvfrom(1024)
        if data.decode().startswith("SERVER_HERE:"):
            server_ip = addr[0]
    except Exception as e:
        print(f"UDP Broadcast error: {e}")
    finally:
        sock.close()

    return f"http://{server_ip}:5000" if server_ip else "http://127.0.0.1:5000"

if opsi_server.get("opsi", "local server").lower() == "local server":
	SERVER_URL = discover_server()
else:
	SERVER_URL = "https://beverly-insight-tobago-betty.trycloudflare.com"
	
rata_kiri = Qt.AlignmentFlag.AlignLeft
rata_kanan = Qt.AlignmentFlag.AlignRight
rata_atas = Qt.AlignmentFlag.AlignTop
rata_bawah = Qt.AlignmentFlag.AlignBottom
expand = QSizePolicy.Policy.Expanding
fix = QSizePolicy.Policy.Fixed
bg, icon_size, font_size_normal, font_size_judul = "lightblue", (15, 15), 9, 10
app_name, version = "FiXy Point", "7.0.0"
bahasa_aplikasi = "bahasa indonesia"
warna_huruf = "black"
format_uang_app = ["Rp", "kiri", ".", ",", "2"]
format_waktu_app = "%d/%m/%Y %H:%M:%S"
use_decimal = True
style_jago = ParagraphStyle(name="jago", fontName="Helvetica-Bold", alignment=TA_LEFT)
style_biasa = ParagraphStyle(name="biasa", fontName="Helvetica", alignment=TA_LEFT)
style_judul = ParagraphStyle(name="namaToko", fontName="Helvetica-Bold", fontSize=12, textColor=colors.green, alignment=TA_LEFT)
style_header = ParagraphStyle(name="judul", fontName="Helvetica-bold", fontSize=12, textColor=colors.black, alignment=TA_CENTER, borderPadding=10, borderWidth=1, borderRadius=5, borderColor=colors.steelblue)

def get_format():
	global bahasa_aplikasi, format_uang_app, format_waktu_app
	data = getData("pengaturan_format")
	if not data:
		return
	d = data[0]
	bahasa_aplikasi = d["bahasa"] if d["bahasa"] else bahasa_aplikasi
	format_uang_app = json.loads(d["format_uang"]) if d["format_uang"] else format_uang_app
	format_waktu_app = d["format_waktu"] if d["format_waktu"] else format_waktu_app
		
def get_theme():
	global bg, warna_huruf, font_size_normal, font_size_judul, icon_size
	cursor.execute("SELECT * FROM pengaturan_tema")
	tm = cursor.fetchone()
	if not tm:
		return
	bg = tm["latar"] if tm["latar"] else bg
	warna_huruf = tm["warna_huruf"] if tm["warna_huruf"] else warna_huruf
	font_size_normal = tm["font_normal"] if tm["font_normal"] else font_size_normal
	font_size_judul = tm["font_judul"] if tm["font_judul"] else font_size_judul
	icon_size = (tm["ikon"], tm["ikon"]) if tm["ikon"] else icon_size
	
def get_decimal():
	global use_decimal
	if koneksi["connect"] == 1:
		try:
			des = requests.get(f"{SERVER_URL}/lihat_izin_desimal")
			des = des.json()
			status = des.get("approved", False)
		except Exception:
			status = False
	else:
		status = desimal.get("approved", False)
	use_decimal = status
		
def set_progress(window):
	layar = QApplication.primaryScreen()
	if not layar:
		return None
	else:
		geo = layar.availableGeometry()
		lebar_layar = geo.width()
		tinggi_layar = geo.height()

	tinggi = 30
	margin = 20
	lebar = lebar_layar - (margin * 2)

	progress = QProgressBar(window)
	progress.setGeometry(margin, tinggi_layar - tinggi - margin, lebar, tinggi)
	progress.setRange(0, 0)
	return progress
	
def set_spinner(window):
	layar = QApplication.primaryScreen()
	if not layar:
		return None

	geo = layar.availableGeometry()

	overlay = LoadingOverlay(window)
	overlay.resize(geo.width(), geo.height())
	overlay.show()
	overlay.raise_()

	return overlay

def upload_data(endpoint, data, pesan):
	psn = {}
	spinner = set_spinner(window)
	QApplication.processEvents()
	try:
		res = requests.post(f"{SERVER_URL}/{endpoint}", json=data, timeout=5)
		if res.status_code == 200:
			psn["status"] = "Berhasil"
			psn["pesan"] = pesan
		else:
			psn["status"] = "Gagal"
			psn["pesan"] = str(res.status_code)
	except Exception as e:
		psn["status"] = "Error"
		psn["pesan"] = str(e)
	spinner.deleteLater()
	QMB.information(None, tr(psn["status"]), psn["pesan"])

def getData(tabel):
	if koneksi["connect"] == 1:
		try:
			res = requests.get(f"{SERVER_URL}/lihat_data/{tabel}", timeout=5)
			if res.status_code == 200:
				return res.json()
			return []
		except Exception as e:
			return []
	else:
		cursor.execute(f"SELECT * FROM {tabel}")
		tbl = cursor.fetchall()
		return list(dict(row) for row in tbl)

def setData(func, data):
	spinner = set_spinner(window)
	try:
		res = requests.post(f"{SERVER_URL}/post_data/{func}", json=data)
		st = res.json()
		if res.status_code == 200:
			spinner.deleteLater()
			QMB.information(None, st["stat"], st["pesan"])
		else:
			spinner.deleteLater()
			QMB.warning(None, st["stat"], st["pesan"])
	except Exception as e:
		spinner.deleteLater()
		QMB.critical(None, "Error", str(e))
		
def setFile(func, file):
	spinner = set_spinner(window)
	if isinstance(file, dict):
		try:
			res = requests.post(f"{SERVER_URL}/post_file/{func}", files=file)
			st = res.json()
			if res.status_code == 200:
				spinner.deleteLater()
				QMB.information(None, st["stat"], st["pesan"])
			else:
				spinner.deleteLater()
				QMB.warning(None, st["stat"], st["pesan"])
		except Exception as e:
			spinner.deleteLater()
			QMB.critical(None, "Error", str(e))
	else:
		QMB.information(None, tr("Gagal"), tr("Format salah"))
		
def cek_kekuatan_koneksi(timeout=5):
    import time as tm
    try:
        start = tm.time()
        response = requests.get(SERVER_URL, timeout=timeout)
        latency = (tm.time() - start) * 1000
        if latency < 100:
            status = "Sinyal Kuat"
            kekuatan = 100
        elif latency < 300:
            status = "Sinyal Sedang"
            kekuatan = 70
        elif latency < 1000:
            status = "Sinyal Lemah"
            kekuatan = 40
        else:
            status = "Sinyal Sangat Lemah"
            kekuatan = 10
            
        return {
            "url": SERVER_URL,
            "latency_ms": round(latency, 2),
            "status": status,
            "kekuatan": kekuatan,
            "http_status": response.status_code
        }
    except requests.exceptions.Timeout:
        return {"url": SERVER_URL, "status": "Timeout - Sinyal Putus", "kekuatan": 0}
    except requests.exceptions.ConnectionError:
        return {"url": SERVER_URL, "status": "Tidak Terhubung", "kekuatan": 0}
    except Exception as e:
        return {"url": SERVER_URL, "status": f"Error: {str(e)}", "kekuatan": 0}
			
def askyesno(header, footer):
	if QMB.question(None, header, footer, QMB.Yes | QMB.No) == QMB.Yes:
		return True
	else:
		return False
		
def munculkan(widget):
	if animasi["yes"] == 1:
		effect = QGraphicsOpacityEffect(widget)
		widget.setGraphicsEffect(effect)
		anim = QPropertyAnimation(effect, b"opacity")
		anim.setDuration(300)
		anim.setStartValue(0)
		anim.setEndValue(1)
		widget.show()
		anim.start()
		widget.anim = anim
	else:
		widget.show()
	
def nama_operator():
	cursor.execute("SELECT nama FROM operator")
	operator = cursor.fetchone()
	return operator[0] if operator else ""
	
def komputer():
	cursor.execute("SELECT id_device FROM device")
	id = cursor.fetchone()
	return id[0] if id else ""	

def choose_save_path(nama_file, filter_type="All Files (*)"):
    file_path, _ = QFileDialog.getSaveFileName(None, "Simpan sebagai", nama_file, filter_type)
    if not file_path:
        return None
    tulis("Path yang diberikan: " + str(file_path))
    return file_path
    
def choose_save_path_pdf(nama_file):
    if not nama_file.lower().endswith(".pdf"):
        nama_file += ".pdf"
    file_path, _ = QFileDialog.getSaveFileName(None, "Simpan sebagai", nama_file, "PDF Files (*.pdf)")
    if not file_path:
        return None
    return file_path
	
def choose_folder():
	folder = QFileDialog.getExistingDirectory(None, "Pilih folder")
	return folder
		
def pretty_money(n):
	format = format_uang_app
	if use_decimal:
		try:
			teks = f"{n:,.{format[-1]}f}".replace(".", ",").split(",")
			money = format[2].join(teks[:-1]) + format[3] + teks[-1]
			if format[1].lower() == "kiri":
				format_money = format[0] + money
			else:
				format_money = money + format[0]
			return format_money
		except:
			return str(n)
	else:
		try:
			return f"{format[0]}{int(n):,}".replace(",", format[2])
		except:
			return str(n)
			
def replace_money(n):
	try:
		return float(n.replace(format_uang_app[0], "").replace(format_uang_app[2], "").replace(format_uang_app[3], "."))
	except:
		return str(n)

def mp(teks):
	return Paragraph(teks, style_biasa)
	
def qr_maker(teks, fill="black", back="white"):
	if not teks:
		QMB.warning(None, tr("Gagal"), tr("Teks kosong"))
		return
	qr_teks = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
	qr_teks.add_data(teks)
	qr_teks.make(fit=True)
	img = qr_teks.make_image(fill_color=fill, back_color=back)
	return img
	
def entry_maker(parent, teks):
	ent = {}
	for i, p in teks:
		lbl = label(tr(i.replace("_"," ").lower().capitalize()), font_weight=500, padding=3)
		en = entry(tr(p), font_size_normal)
		ent[i] = en
		parent.addWidget(lbl)
		parent.addWidget(en, alignment=rata_atas)
	return ent

def get_lokal_file_paths(folder):
	paths = []
	for p in os.listdir(folder):
		path = os.path.join(folder, p)
		if os.path.isfile(path):
			paths.append(path)
		elif os.path.isdir(path):
			if os.path.basename(path) != "Folder backup":
				paths.extend(get_lokal_file_paths(path))
	return paths
	
def get_server_file_paths():
	try:
		res = requests.get(f"{SERVER_URL}/get_all_paths")
		if res.status_code == 200:
			return res.json()
		else:
			QMB.critical(None, "", str(res.status_code))
	except Exception as e:
		QMB.critical(None, "", str(e))

def ambil_info_backup():
	folders = []
	for p in os.listdir(folder_backup):
		path = os.path.join(folder_backup, p)
		if os.path.isdir(path):
			folders.append(path)
	return folders
	
def ambil_path_file_backup(fol):
	info = os.path.join(fol, "Info.json")
	def get_file(ff):
		files = []
		for p in os.listdir(ff):
			path = os.path.join(ff, p)
			if os.path.isfile(path):
				files.append(path)
			elif os.path.isdir(path):
				files.extend(get_file(path))
		return files
	files = get_file(fol)
	with open(info, "r") as f:
		info_backup = json.load(f)
	if info in files:
		files.remove(info)	
	return {
		"waktu": info_backup.get("waktu", ""),
		"path files": files,
		"path original": info_backup.get("original path", [])
	}
	
def tulis(teks):
	path = "/storage/emulated/0/proyekku/error.txt"
	with open(path, "w", encoding="utf-8") as f:
		f.write(teks)
		
def show_pictures(pict, label, size):
	try:
		if isinstance(pict, str):
			pixmap = QPixmap(pict)
		elif isinstance(pict, (bytes, bytearray)):
			pixmap = QPixmap()
			pixmap.loadFromData(pict)
		else:
			label.setText(tr("Gambar tidak tersedia"))
			return
		
		if pixmap.isNull():
			label.setText(tr("Gagal memuat gambar"))
			return
			
		pix = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		label.setPixmap(pix)
		
	except Exception as e:
		label.setText(str(e))
								
def now_str():
	return datetime.now().strftime(format_waktu_app)
	
def setShortcut(short, func):
	shortcut = QShortcut(QKeySequence(short), window)
	shortcut.activated.connect(func)
	return shortcut
	
def safe_run(func, *args, **kwargs):
	try:
		return func(*args, **kwargs)
	except Exception:
		tulis(str(traceback.format_exc()))
		QMB.critical(None, "Error", traceback.format_exc())
	
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
							
def take_all_cache():
	cs = getData("customer")
	if cs:
		customer.clear()
		customer.extend(cs)		
	produk = getData("produk")
	if produk:
		produk_data.clear()
		produk_data.extend(produk)
	dataA = getData("tingkat_a")
	if dataA:
		A.clear()
		A.extend(dataA)
	dataB = getData("tingkat_b")
	if dataB:
		B.clear()
		B.extend(dataB)
	diskon = getData("produk_diskon")
	if diskon:
		diskon_data.clear()
		diskon_data.extend(diskon)
	profil = getData("profil")
	if profil:
		profil_data.clear()
		profil_data.extend(profil)
	pajak = getData("pajak")
	if pajak:
		pjk.clear()
		pjk.extend(pajak)

	simpan_semua(file_customer, customer)
	simpan_semua(file_produk_data, produk_data)
	simpan_semua(file_A, A)
	simpan_semua(file_B, B)
	simpan_semua(file_diskon_data, diskon_data)
	simpan_semua(file_profil_data, profil_data)
	simpan_semua(file_pajak, pjk)

def tr(kata):
	return translator(kata, bahasa_aplikasi)
	
def server_alive(timeout=1):
	try:
		r = requests.get(SERVER_URL, timeout=timeout)
		return True
	except Exception:
		return False
		
def take_data(tabel, model):
	idx = tabel.currentIndex()
	if not idx.isValid():
		return []
	mod = idx.model()
	row = idx.row()
	data = []
	for col in range(mod.columnCount()):
		index = mod.index(row, col)
		value = mod.data(index)
		data.append("" if value is None else str(value))
	return data
	
owner_v = {}
def take_owner_validation():
	data = getData("validasi_owner")
	if not data:
		owner_v["status"] = 0
		return
	stts = data[0]
	owner_v["status"] = stts["status"]
			
def validasi_owner_first():
	if owner_v:
		status = True if owner_v["status"] == 1 else False
		return status
	else:
		return False
		
def validasi_pemilik():
	if validasi_owner_first():
		data_user = getData("user")
		wdi, ok = input_string(tr("Password dibutuhkan"), tr("Masukkan kata sandi owner!"))
		if ok:
			wd = wdi.strip()
			cocok = next((p for p in data_user if pks.verify(wd, p["password"])), None)
			if cocok:
				if cocok["status"].lower() == "owner":
					pass
				else:
					QMB.warning(None, tr("Kata sandi salah"), tr("Silahkan masukkan kata sandi owner!"))
					return False
			else:
				QMB.warning(None, tr("Kata sandi salah"), tr("Kata sandi yang Anda masukkan tidak terdaftar dalam database!"))
				return False
			return True
	else:
		return True
		
def zebra_style(tabel, data, warna_ganjil = colors.aliceblue, warna_genap = colors.mintcream):
	style = [
		("BOX", (0,0), (-1,-1), 0.5, colors.black),
		("FONTNAME", (0,0), (-1, 0), "Helvetica-Bold"),
		("FONTSIZE", (0,0), (-1,0), 10),
		("BACKGROUND", (0,0), (-1,0), colors.lightgreen),
		("FONTNAME", (0,-4), (-1,-1), "Helvetica-Bold"),
		("BOX", (0,-4), (-1,-1), 0.5, colors.grey),
		("FONTNAME", (1,-1), (1,-1), "Helvetica"),
		("SPAN", (0,-1), (-3,-1))
	]
	for i in range(1, len(data)):
		warna = warna_genap if i%2 == 0 else warna_ganjil
		style.append(("BACKGROUND", (0,i), (-1,i), warna))
	tabel.setStyle(TableStyle(style))
	return tabel
		
def resource_path(filename):
	try:
		base_path = sys._MEIPASS
	except AttributeError:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, filename)
	
def set_margin(wd, nilai):
	wd.setContentsMargins(nilai, nilai, nilai, nilai)
	wd.setSpacing(nilai)
	
def set_expanding(frame, h, v):
	frame.setSizePolicy(h, v)
	
def give_scroll(frame, scrollH=True):
	scroll = QScrollArea()
	scroll.setStyleSheet("""
		QScrollArea {
			background-color: transparent;
			border: none;
		}""")
	scroll.setWidgetResizable(True)
	scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
	if scrollH:
		scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
	else:
		scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
	scroll.setWidget(frame)
	return scroll
	
def make_main_frame():
	path_wallpaper = os.path.join(folder_foto_profil, "Wallpaperforrightframeinmyappveryimportantandmostpowerfull.png")
	if not os.path.exists(path_wallpaper):
		path_wallpaper = resource_path("Pictures/wall_default.png")
		
	left, right, kal = QFrame(), QFrame(), QFrame()
	kal.setFixedWidth(180)
	kal.setObjectName("kal")
	kal.setStyleSheet(f"""
		QFrame#kal {{
			background-color: transparent;
			border: 0px solid black;
			border-radius: 2px;
		}}""")
		
	right.setObjectName("f3")
	right.setStyleSheet(f"""
		QFrame#f3 {{
			background-color: transparent;
		}}""")
	left.setObjectName("left")
	left.setStyleSheet(f"""
		QFrame#left {{
			background-color: transparent;
			margin: 2px;
			border-radius: 2px;
			border: 0.5px solid rgba(0,0,0,0.2);
		}}""")
	left.setFixedWidth(130)
	right_layout = QVBoxLayout(right)
	right_layout.setAlignment(rata_atas)
	right_layout.setContentsMargins(0,0,0,0)
	right_layout.setSpacing(0)
	
	for x in [left, right, kal]:
		window_layout.addWidget(x)
	return left, right_layout, QVBoxLayout(kal, alignment=rata_atas), kal
	
def left_layout_setting():
	left_layout = QVBoxLayout(left)
	left_layout.setAlignment(rata_atas)
	return left_layout

def summon_left():
	global state_left, lock_button
	if lock_button:
		return
	if not state_left:
		state_left = True
		munculkan(left)
	else:
		state_left = False
		left.hide()
	
def set_right_frames():
	f1 = QFrame()
	f2 = QFrame()
	f3 = QFrame()
	f2.setObjectName("frame2")
	f1.setStyleSheet(f"""
		QFrame {{
			background-color: {bg};
			margin-top: 5px;
			border: none;
			border-radius: 2px;
		}}""")
	f2.setStyleSheet(f"""
		QFrame#frame2 {{
			background-color: rgba(0,120,100,0.06);
			border: 1px solid rgba(0,0,0,0.1);
			border-radius: 2px;
		}}""")
		
	f3.setStyleSheet("""
		QFrame {
			background-color: transparent;
		}""")
	for x in [f1, f2]:
		set_expanding(x, expand, fix)
	set_expanding(f3, expand, expand)
	scroll = give_scroll(f3)
	for x in [f1, f2, scroll]:
		right_layout.addWidget(x)
	return f1, f2, f3
	
def set_layout_for_right_frame():
	layout1, layout2, layout3 = QHBoxLayout(f1), QHBoxLayout(f2, alignment=rata_kiri), QVBoxLayout(f3, alignment=rata_atas)
	layout1.setSpacing(1)
	set_margin(layout2, 3)
	set_margin(layout3, 3)
	return layout1, layout2, layout3

def set_f1_widgets():
	wd = {
		"left": QPushButton("\u2630"),
		"judul": QLabel(),
		"koneksi": QPushButton(),
		"kal": QPushButton()
	}
	wd["left"].clicked.connect(summon_left)
	wd["kal"].clicked.connect(open_kalkulator)
	wd["kal"].setIcon(QIcon(resource_path("Pictures/kalkulator.png")))
	wd["kal"].setIconSize(QSize(icon_size[0], icon_size[1]))
	
	for p in ["left", "kal", "judul"]:
		wd[p].setStyleSheet(f"""
			QPushButton {{
				font-size: {font_size_judul + 2}px;
				padding: 5px;
				border: none;
				color: {warna_huruf};
				background-color: transparent;
				font-weight: 800;
			}}
			QPushButton:pressed {{
				background-color: black;
				color: white;
			}}
			QLabel {{
				font-weight: 800;
				color: {warna_huruf};
				font-size: {font_size_normal}px;
			}}""")
	f1_layout.addWidget(wd["left"], alignment=rata_kiri)
	set_expanding(wd["judul"], expand, fix)
	for p in ["judul", "koneksi", "kal"]:
		f1_layout.addWidget(wd[p])
	return wd["judul"], wd["koneksi"]
			
def konfigurasi_koneksi():
	if koneksi["connect"] == 1:
		if server_alive():
			warna = "green"
			teks_koneksi = "Online"
			picture_koneksi = resource_path("Pictures/online_mode.png")
		else:
			warna = "red"
			teks_koneksi = tr("Server tidak aktif")
			picture_koneksi = resource_path("Pictures/offline_mode.png")
	else:
		warna = "yellow"
		teks_koneksi = "Offline"
		picture_koneksi = resource_path("Pictures/@.png")

	lbl_koneksi.setText(teks_koneksi)
	lbl_koneksi.setIcon(QIcon(picture_koneksi))
	lbl_koneksi.setIconSize(QSize(10,10))
	lbl_koneksi.setStyleSheet(style_label_koneksi(font_size_normal, warna))
	
def set_left_widgets():
	lbl_app = QPushButton(app_name+"\n"+"Version:"+" "+version)
	lbl_app.setIcon(QIcon("Pictures/f-pos.png"))
	lbl_app.setIconSize(QSize(20,20))
	lbl_app.setStyleSheet(f"""
		QPushButton {{
			font-size: {font_size_normal}px;
			background-color: {bg};
			color: {warna_huruf};
			padding: 10px;
			border: none;
			border-radius: 2px;
		}}""")
	left_layout.addWidget(lbl_app, alignment=rata_atas)
	
	list_left_button = [
		("Beranda", "Pictures/dashboard080102.png", lambda: dashboard_aplikasi.setup()),
		("Pemilik", "Pictures/owner080102.png", master),
		("Transaksi", "Pictures/transaksi080102.png", transaksi),
		("Laporan", "Pictures/laporan080102.png", lambda: safe_run(laporan_aplikasi.setup)),
		("Lainnya", "Pictures/lainnya080102.png", lainnya),
		("Tentang", "Pictures/tentang_app.png", tentang)
	]	
	for (teks, path, command) in list_left_button:
		btn = QPushButton(teks)
		btn.setStyleSheet(f"""
			QPushButton {{
				padding: 5px;
				border: none;
				background-color: transparent;
				font-size: {font_size_normal}px;
			}}
			QPushButton:hover {{
				border: 1px solid {bg};
				border-radius: 2px;
				background-color: rgba(0,100,35,0.08);
			}}""")
		btn.setIcon(QIcon(resource_path(path)))
		btn.setIconSize(QSize(icon_size[0], icon_size[1]))
		btn.clicked.connect(command)
		left_layout.addWidget(btn, alignment=rata_kiri)
		
	btn_out = label_photo(tr("Keluar"), resource_path("Pictures/keluar.png"), icon_size)
	btn_out.setStyleSheet(style_button(bg, font_size_normal))
	btn_out.clicked.connect(keluar)
	fr = QFrame()
	fr_layout = QVBoxLayout(fr)
	set_expanding(fr, expand, expand)
	fr_layout.setAlignment(rata_bawah)
	fr_layout.addWidget(btn_out, alignment=rata_bawah)
	left_layout.addWidget(fr)
	
foto_profil = {}
def simpan_foto_profil_sementara():
    global foto_profil
    if koneksi["connect"] == 1:
        try:
            res = requests.get(f"{SERVER_URL}/download_foto_profil")
            if res.status_code == 200:
                img_data = BytesIO(res.content)
                pil_img = Image.open(img_data).resize((250, 250), Image.LANCZOS)
                buffer = BytesIO()
                pil_img.save(buffer, format="PNG")
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())
            else:
                pixmap = QPixmap(resource_path("Pictures/store.png"))
        except Exception:
            pixmap = QPixmap(resource_path("Pictures/store.png"))
    else:
        path = os.path.join(folder_foto_profil, "foto profil.png")
        if not os.path.exists(path):
            pixmap = QPixmap(resource_path("Pictures/store.png"))
        else:
            pixmap = QPixmap(path).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    foto_profil["foto"] = pixmap

def pengaturan_shift():
	if not va("atur shift"):
		QMB.warning(None, "", tr("Anda tidak diizinkan"))
		return
		
	def make_main_frames():
		clear_widgets(f3)
		atas, atas_layout = frame(QVBoxLayout, bg="transparent")
		bawah, bawah_layout = frame(QHBoxLayout, bg="transparent")
		bawah_layout.setAlignment(rata_kiri)
		s = give_scroll(atas, scrollH=False)
		for p in [s, bawah]:
			f3_layout.addWidget(p)
		return atas, bawah, atas_layout, bawah_layout
	
	def set_bawah():
		buttons = [
			("Daftar shift", pengaturan_shift),
			("Tambah shift", tambah_shift),
			("Hapus seluruh shift", hapus_seluruh_shift)
		]
		for teks, command in buttons:
			btn = button(tr(teks), font_size_normal, bg)
			btn.clicked.connect(lambda *args, cm=command: safe_run(cm))
			bawah_layout.addWidget(btn, alignment=rata_kiri)
	
	def tambah_anggota(id, tabel, model):
		user = getData("user")
		dt = next((p for p in shift if p["id_shift"] == id), None)
		list_id_inisial = []
		member = []
		if dt:
			member = json.loads(dt["anggota"])
			list_id_inisial = list({p["inisial_code"] for p in member})
			
		clear_widgets(atas)
		jdl = label(tr("PILIH ANGGOTA"), font_size=font_size_judul, font_weight=800)
		atas_layout.addWidget(jdl)
		teks = [p["nama"] + " - " + p["inisial_code"] for p in user if p["inisial_code"] not in list_id_inisial]
		
		ceklist = {}
		for p in teks:
			cek = checkbutton(p, font_size_normal)
			ceklist[p] = cek
			atas_layout.addWidget(cek)
		
		def tambahkan():
			terpilih = [teks for teks, cek in ceklist.items() if cek.isChecked()]
			if not terpilih:
				QMB.information(None, tr("Kosong"), tr("Pilih minimal 1 anggota"))
				return
			list_bedah = []
			for p in terpilih:
				teks = p.split(" - ")
				list_bedah.append({
					"nama": teks[0],
					"inisial_code": teks[1]
				})
			if askyesno(tr("Konfirmasi"), tr("Simpan sekarang") + "?"):
				if koneksi["connect"] == 1:
					upload_data("tambah_anggota_shift", {"data": list_bedah + member, "shift": id}, f"{len(terpilih)} {tr('telah ditambahkan')}!")
				else:
					cursor.execute("UPDATE shift SET anggota = ? WHERE id_shift = ?", (json.dumps(list_bedah + member), id))
					conn.commit()
					QMB.information(None, tr("Berhasil"), f"{tr('Anggota')} {id} {tr('telah diperbarui')}")
				pengaturan_shift()
			
				
		btn = button(tr("Tambahkan"), font_size_normal, bg)
		btn.clicked.connect(tambahkan)
		atas_layout.addWidget(btn)
		
	def hapus_anggota(id, tabel, model):
		data = take_data(tabel, model)
		if not data:
			return
		nama, inisial_code = data[0], data[1]
		if askyesno(tr("Konfirmasi"), f"{tr('Hapus')} {nama} {tr('dari')} {id}?"):
			if koneksi["connect"] == 1:
				data = {
					"inisial_code": inisial_code,
					"id": id
				}
				setData("hapus_anggota_shift", data)
			else:
				cursor.execute("SELECT anggota FROM shift WHERE id_shift = ?",(id,))
				member = cursor.fetchone()
				if not member:
					QMB.warning(None, tr("Gagal"), tr("Anggota tidak ditemukan"))
					return
				anggota = json.loads(member["anggota"])
				new = [p for p in anggota if p["inisial_code"].lower() != inisial_code.lower()]
				cursor.execute("UPDATE shift SET anggota = ? WHERE id_shift = ?",(json.dumps(new), id))
				conn.commit()
				QMB.information(None, tr("Berhasil"), f"{nama} {tr('telah dihapus dari')} {id}")
			pengaturan_shift()
			
	def hapus_shift_ini(id, tabel, model):
		if askyesno(tr("Konfirmasi"), f"{tr('Anda ingin menghapus shift')} {id}?"):
			if koneksi["connect"] == 1:
				data = {"id": id}
				setData("hapus_shift_tertentu", data)
			else:
				cursor.execute("DELETE FROM shift WHERE id_shift = ?",(id,))
				conn.commit()
				QMB.information(None, tr("Berhasil"), f"Shift {id} {tr('telah dihapus')}")
			pengaturan_shift()
				
	def set_atas():
		clear_widgets(atas)
		if not shift:
			atas_layout.addWidget(red_label(tr("Tidak ada data shift")))
			return
		for p in shift:
			frr, layout = frame(QHBoxLayout, bg="transparent")
			kiri, kiri_layout = frame(QGridLayout, bg="rgba(0,100,120,0.06)")
			tabel, model = table_maker(["Nama", "Inisial code"])
			info = [
				("Nama", p["nama_shift"]),
				("ID shift", p["id_shift"]),
				("Waktu mulai", p["waktu_mulai"]),
				("Waktu selesai", p["waktu_selesai"])
			]
			for i, (teks, value) in enumerate(info):
				if i == 0:
					label_teks = label(tr(teks), font_size=font_size_judul, color="darkgreen", font_weight=800, padding=3)
					titik_dua = label(":", font_size=font_size_judul, color="darkgreen", font_weight=800, padding=3)
					label_value = label(value, font_size=font_size_judul, color="darkgreen", font_weight=800, padding=3)
				else:
					label_teks = label(teks, font_weight=600)
					titik_dua = label(":", font_weight=600)
					label_value = label(value, font_weight=600)
				kiri_layout.addWidget(label_teks, i, 0)
				kiri_layout.addWidget(titik_dua, i, 1)
				kiri_layout.addWidget(label_value, i, 2)
				
			btns = [
				("Tambah anggota", tambah_anggota),
				("Hapus anggota", hapus_anggota),
				("Hapus shift", hapus_shift_ini)
			]
			anggota = json.loads(p["anggota"])
			for person in anggota:
				model.appendRow([
					QStandardItem(person["nama"]),
					QStandardItem(person["inisial_code"])
				])
				
			for i, (teks, command) in enumerate(btns, start=4):
				btn = button(tr(teks), font_size_normal, bg)
				btn.clicked.connect(lambda *args, id=p["id_shift"], comm=command, tbl=tabel, mdl=model: safe_run(comm, id, tbl, mdl))
				kiri_layout.addWidget(btn, i, 0, 1, 3)
					
			for a in [kiri, tabel]:
				layout.addWidget(a)
			atas_layout.addWidget(frr)
			
	def tambah_shift():
		clear_widgets(atas)
		n = entry(tr("Nama shift..."), font_size_normal)
		atas_layout.addWidget(n)
		waktu = ["Waktu mulai", "Waktu selesai"]
		jdl = {}
		for teks in waktu:
			lbl = label(teks, font_size=font_size_judul, font_weight=700, color="green")
			tm = buat_input_waktu()
			jdl[teks.lower()] = tm
			for k in [lbl, tm]:
				atas_layout.addWidget(k)
				
		def simpan_shift_baru():
			nama = n.text().strip()
			mula = jdl["waktu mulai"].time().toString("HH.mm")
			selesai = jdl["waktu selesai"].time().toString("HH.mm")

			if askyesno(tr("Konfirmasi"), tr("Apakah data sudah benar")):
				if koneksi["connect"] == 1:
					data = {
						"nama": nama,
						"anggota": [],
						"mulai": mula,
						"selesai": selesai
					}
					upload_data("tambah_shift", data, f"{nama} {tr('telah dibuat')}!")
				else:
					cursor.execute("INSERT INTO shift (id_shift, nama_shift, anggota, waktu_mulai, waktu_selesai) VALUES (?, ?, ?, ?, ?)", (datetime.now().strftime("%f"), nama, json.dumps([]), mula, selesai))
					conn.commit()
					QMB.information(None, tr("Berhasil"), f"{nama} {tr('telah dibuat')}!")
				pengaturan_shift()
		btn_save = button(tr("Simpan"), font_size_normal, bg)
		btn_save.clicked.connect(lambda: safe_run(simpan_shift_baru))
		atas_layout.addWidget(btn_save)
				
	def hapus_seluruh_shift():
		if askyesno(tr("Konfirmasi"), tr("Anda yakin ingin menghapus seluruh shift") + "?"):
			if koneksi["connect"] == 1:
				setData("hapus_seluruh_shift", {"s":1})
			else:
				cursor.execute("DELETE FROM shift")
				conn.commit()
				QMB.information(None, tr("Berhasil"), tr("Seluruh data shift telah dihapus"))
			pengaturan_shift()
			
	shift = getData("shift")	
	atas, bawah, atas_layout, bawah_layout = make_main_frames()
	set_atas()
	set_bawah()

def move_data(id, entries, table):
	d = {key: value.text().strip() for key, value in entries.items()}
	d["id"] = id
	if askyesno(tr("Konfirmasi"), f"{tr('Data sudah siap')}. Update {table} {tr('sekarang')}?"):	
		if koneksi["connect"] == 1:
			setData("edit_" + table, d)
		else:
			if table == "customer":
				cursor.execute("UPDATE customer SET nama = ?, alamat = ?, kontak = ?, email = ? WHERE id = ?", (d.get("nama",""), d.get("alamat",""), d.get("kontak",""), d.get("email",""), id))
			else:
				cursor.execute("""
					UPDATE supplier SET
					nama = ?, alamat = ?, kontak = ?, email = ?,
					bidang = ?, medsos = ? WHERE id = ?""",
					d.get("nama",""), d.get("alamat",""),d.get("kontak",""),d.get("email",""),d.get("bidang",""),d.get("medsos",""),id
				)
			conn.commit()
			QMB.information(None, tr("Berhasil"), f"Update {table} {d.get('nama','')} {tr('telah berhasil')}")
						
def edit_customer(id, frame, layout):
	clear_widgets(frame)
	list_for_entry = [
		("nama", tr("Nama baru") + "..."),
		("alamat", tr("Alamat baru") + "..."),
		("kontak", tr("Telp/WA baru") + "..."),
		("email", tr("Email baru") + "...")
	]
	customer = getData("customer")
	cs = next((p for p in customer if p["id"] == id), None)
	entries = entry_maker(layout, list_for_entry)
	for key, value in entries.items():
		value.setText(cs[key] if cs[key] else "-")
	btn_simpan = button(tr("Simpan"), font_size_normal, bg)
	btn_simpan.clicked.connect(lambda: safe_run(move_data, id, entries, "customer"))
	layout.addWidget(btn_simpan, alignment=rata_atas)	

def hapus_customer(id, frame, layout):
	if askyesno(tr("Konfirmasi"), tr("Hapus customer sekarang") + "?"):
		if koneksi["connect"] == 1:
			setData("hapus_customer", {"id": id})
		else:
			cursor.execute("DELETE FROM customer WHERE id = ?",(id,))
			conn.commit()
			QMB.information(None, tr("Berhasil"), tr("Customer telah dihapus"))
		customer_menu()
		
def edit_supplier(id, frame, layout):
	clear_widgets(frame)
	list_for_entry = [
		("nama", tr("Nama baru") + "..."),
		("alamat", tr("Alamat baru") + "..."),
		("kontak", tr("Telp/WA baru") + "..."),
		("email", tr("Email baru") + "..."),
		("bidang", tr("Bidang baru") + "..."),
		("medsos", tr("Media sosial baru") + "...")
	]
	entries = entry_maker(layout, list_for_entry)
	supplier = getData("supplier")
	cs = next((p for p in supplier if p["id"] == id), None)
	for key, value in entries.items():
		value.setText(cs[key] if cs[key] else "-")
	btn_simpan = button(tr("Simpan"), font_size_normal, bg)
	btn_simpan.clicked.connect(lambda: safe_run(move_data, id, entries, "supplier"))
	layout.addWidget(btn_simpan, alignment=rata_atas)	
	
def hapus_supplier(id, frame, layout):
	if askyesno(tr("Konfirmasi"), tr("Hapus supplier sekarang") + "?"):
		if koneksi["connect"] == 1:
			setData("hapus_supplier", {"id": id})
		else:
			cursor.execute("DELETE FROM supplier WHERE id = ?", (id,))
			conn.commit()
			QMB.information(None, tr("Berhasil"), tr("Supplier telah dihapus"))
		supplier_menu()
	
def layout_for_customer_supplier(jdl):
	lbl_judul.setText(jdl)
	clear_widgets(f3)
	def prepare_frames():
		cari = entry(tr("Masukkan nama atau nomor telepon") + "...", font_size_normal)
		atas, atas_layout = frame(QGridLayout, padding=5, rata=rata_kiri)
		bawah, bawah_layout = frame(QHBoxLayout, rata=rata_kiri)
		atas_scroll = give_scroll(atas)
		atas_scroll.setMinimumHeight(250)
		for p in [cari, atas_scroll, bawah]:
			f3_layout.addWidget(p, alignment=rata_atas)
		return cari, atas, atas_layout, bawah, bawah_layout
	
	def set_buttons():
		btn_tambah = button(tr("Tambah"), font_size_normal, bg)
		btn_clear = button(tr("Hapus seluruh data"), font_size_normal, bg)
		for btn in [btn_tambah, btn_clear]:
			bawah_layout.addWidget(btn, alignment=rata_kiri)
			
		return btn_tambah, btn_clear
		
	cari, atas, atas_layout, bawah, bawah_layout = prepare_frames()
	tambah, hapus_semua = set_buttons()
	return cari, atas, atas_layout, tambah, hapus_semua

def show_data_customer_supplier(main, fff, data=[], col=1, mode="customer", teks=""):
	if not data:
		warning = red_label(tr("Tidak ada data"))
		main.addWidget(warning)
		return
	clear_widgets(fff)
		
	for idx, item in enumerate(data):
		if teks.lower() in item["nama"].lower(): #or teks.lower() in item["id_user"].lower():
			frame_utama, layout_utama = frame(QVBoxLayout, bg="rgba(0,100,120,0.06)", rata=rata_atas)
			nama = label(
				item["nama"],
				font_size=font_size_judul,
				color="green",
				font_weight=700,
				padding=10,
				margin=5,
				border="1px solid green",
				border_radius=2
			)
			fr, layout = frame(QGridLayout, bg="transparent", rata=rata_atas)
			for i, (key, value) in enumerate(item.items()):
				if key.lower() not in ["nama", "password", "id"]:
					teks_key = key.replace("_", " ").capitalize()
					label_key = label(teks_key)
					label_titik = label(":")
					label_value = label(str(value))
					layout.addWidget(label_key, i, 0)
					layout.addWidget(label_titik, i, 1)
					layout.addWidget(label_value, i, 2)
			
			buttons = [
				("Edit", edit_customer if mode == "customer" else edit_supplier),
				("Hapus", hapus_customer if mode == "customer" else hapus_supplier)
			]
			for i, (txt, command) in enumerate(buttons, start=len(item.items())):
				tombol = button(tr(txt), font_size_normal, bg)
				tombol.clicked.connect(lambda *args, cm=command, frm=frame_utama, lay=layout_utama, id=item["id"]: safe_run(cm, id, frm, lay))
				layout.addWidget(tombol, i, 0, 1, 3)
				
			for widget in [nama, fr]:
				layout_utama.addWidget(widget)
			main.addWidget(frame_utama, idx//col, idx%col)

def tambah_supplier_customer(fr, layout, mode):
	if mode == "supplier":
		list_entry = [
			("nama", tr("Nama") + "..."),
			("alamat", tr("Alamat") + "..."),
			("kontak", tr("Telp/WA") + "..."),
			("email", tr("Email") + "..."),
			("bidang", tr("Bidang") + "..."),
			("medsos", tr("Media sosial") + "...")
		]
	else:
		list_entry = [
			("nama", "Nama"),
			("alamat", "Alamat(opsional)"),
			("kontak", "Nomor telepon/WhatsApp"),
			("email", "Email(opsional)"),
			("password", "Password"),
			("konfirmasi password", "Konfirmasi password")
		]
	
	def simpan_cs_sp():
		d = {key: value.text().strip() for key, value in entries.items()}
		if askyesno(tr("Konfirmasi"), f"{tr('Tambahkan')} {d.get('nama','')} {tr('ke daftar')} {mode}?"):
			if koneksi["connect"] == 1:
				setData("tambah_" + mode, d)
				command = customer_menu() if mode == "customer" else supplier_menu
				command()
				
			else:
				if mode == "customer":
					if d.get("password","") != d.get("konfirmasi password",""):
						QMB.warning(None, tr("Gagal"), tr("Password dan konfirmasi password harus sama"))
						return
					if len(d.get("password","")) < 6:
						QMB.warning(None, tr("Gagal"), tr("Password harus minimal 6 karakter"))
						return
					cursor.execute("SELECT * FROM customer WHERE kontak = ? OR email = ?", (d.get("kontak",""),d.get("email","")))
					exist = cursor.fetchone()
					if exist:
						QMB.warning(None, tr("Gagal"), tr("Customer telah terdaftar. Silahkan login"))
						return
					
					id_user = "User-" + str(uuid.uuid4())[:10]
					password = pks.hash(d.get("password",""))
					cursor.execute("""
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
					conn.commit()
					QMB.information(
						None,
						tr("Berhasil"),
						f"{d.get('nama','')} {tr('telah ditambahkan ke dalam daftar customer')}"
					)
					customer_menu()
				else:
					if not all([
						d.get("nama",""),
						d.get("alamat",""),
						d.get("kontak","")
					]):
						QMB.information(None, tr("Gagal"), tr("Nama, alamat, dan nomor telepon harus diisi"))
						return
					cursor.execute("INSERT INTO supplier (nama, alamat, kontak, email, bidang, medsos) VALUES (?, ?, ?, ?, ?, ?)",
						(
							d.get("nama",""),
							d.get("alamat",""),
							d.get("kontak",""),
							d.get("email",""),
							d.get("bidang",""),
							d.get("medsos","")
						)
					)
					conn.commit()
					QMB.information(
						None,
						tr("Berhasil"),
						f"{d.get('nama','')} {tr('telah ditambahkan ke dalam daftar supplier')}"
					)
					supplier_menu()
							
	clear_widgets(fr)
	frame_input, layout_input = frame(QVBoxLayout, bg="transparent", rata=rata_atas)
	layout.addWidget(frame_input, 0, 0)
	entries = entry_maker(layout_input, list_entry)
	btn_simpan = button(tr("Simpan"), font_size_normal, bg)
	btn_simpan.clicked.connect(lambda: safe_run(simpan_cs_sp))
	layout_input.addWidget(btn_simpan)
	
def hapus_supplier_customer(mode):
	if askyesno(
		tr("Konfirmasi"),
		f"{tr('Hapus seluruh data')} {mode}?"
	):
		if koneksi["connect"] == 1:
			setData("hapus_seluruh", {"mode": mode})
		else:
			cursor.execute(f"DELETE FROM {mode}")
			conn.commit()
			QMB.information(
				None,
				tr("Berhasil"),
				tr("Seluruh data") + " " + mode + " " + tr("telah dihapus")
			)
		com = supplier_menu if mode == "supplier" else customer_menu
		com()
	
def supplier_menu():
	data = getData("supplier")
	cari, atas, atas_layout, tambah, hapus_semua = layout_for_customer_supplier(tr("DAFTAR SUPPLIER"))
	tambah.clicked.connect(lambda: safe_run(tambah_supplier_customer, atas, atas_layout, "supplier"))
	hapus_semua.clicked.connect(lambda: safe_run(hapus_supplier_customer, "supplier"))
	safe_run(show_data_customer_supplier, atas_layout, atas, data=data, col=3, mode="supplier")
	cari.textChanged.connect(lambda: safe_run(show_data_customer_supplier, atas_layout, atas, data=data, mode="supplier", col=3, teks=cari.text().strip())) 
			
def customer_menu():
	data = getData("customer")
	cari, atas, atas_layout, tambah, hapus_semua = layout_for_customer_supplier(tr("DAFTAR CUSTOMER"))
	tambah.clicked.connect(lambda: safe_run(tambah_supplier_customer, atas, atas_layout, "customer"))
	hapus_semua.clicked.connect(lambda: safe_run(hapus_supplier_customer, "customer"))
	safe_run(show_data_customer_supplier, atas_layout, atas, data=data, col=3)
	cari.textChanged.connect(lambda: safe_run(show_data_customer_supplier, atas_layout, atas, data=data, col=3, teks=cari.text().strip())) 
				
def master():
	if not va("pemilik"):
		QMB.critical(None, "", tr("Anda tidak diizinkan"))
		return
	for x in [f3, f2]:
		clear_widgets(x)
	
	def profil_func():
		if not va("profil"):
			QMB.critical(None, "", tr("Anda tidak diizinkan"))
			return	
		global foto_profil
		clear_widgets(f3)
		fr1 = QFrame()
		fr1_layout = QHBoxLayout(fr1)
		fr1left, fr1right = QFrame(), QFrame()
		fr1left_layout, fr1right_layout = QVBoxLayout(fr1left), QGridLayout(fr1right)
		fr2 = QFrame()
		fr2_layout = QHBoxLayout(fr2)
		
		label_foto = QLabel()
		label_foto.setPixmap(foto_profil["foto"])
		label_foto.setFixedSize(250, 250)
		label_foto.setScaledContents(True)
		label_foto.setAlignment(Qt.AlignCenter)
		fr1left_layout.addWidget(label_foto)
		
		btn_ganti = label_photo(tr("Ganti foto profil"), resource_path("Pictures/edit.png"), icon_size)
		btn_hapus = label_photo(tr("Hapus foto"), resource_path("Pictures/hehehe.png"), icon_size)
		
		profil_data = getData("profil")
		if not profil_data:
			fr1right_layout.addWidget(red_label(tr("Belum ada profil yang dibuat")), 0, 1)
		
		nama = next((p["nama"] for p in profil_data), "")
		label_nama = label_photo(nama, resource_path("Pictures/shop.png"), (30,30))
		label_nama.setStyleSheet(f"""
			QPushButton {{
				background-color: transparent;
				font-size: 15px;
				border: 0px solid transparent;
				color: green;
				font-weight: bold;
			}}
		""")
		fr1right_layout.addWidget(label_nama, 0, 0)
		
		btn_edit = label_photo(tr("Edit profil"), resource_path("Pictures/hahaha.png"), icon_size)
		btn_hapus_profil = label_photo(tr("Hapus profil"), resource_path("Pictures/hehehe.png"), icon_size)
		for p in [label_foto, label_nama]:
			munculkan(p)
		info = [
			("Pictures/alamat.png", "Alamat", next((p["alamat"] for p in profil_data), "")),
			("Pictures/telepon.png", "Telp / WA", next((p["kontak"] for p in profil_data), "")),
			("Pictures/email.png", "Email", next((p["email"] for p in profil_data), "")),
			("Pictures/medsos.png", "Website", next((p["website"] for p in profil_data), "")),
			("Pictures/jenis_usaha.png", "Jenis usaha", next((p["jenis"] for p in profil_data), ""))
		]
		for i, (a, b, c) in enumerate(info, start=1):
			lbl1 = label_photo(b, resource_path(a), (20,20))
			lbl2 = label_khusus(":")
			lbl3 = label_khusus(c)
			lbl1.setStyleSheet(style_button_fleksibel())
			fr1right_layout.addWidget(lbl1, i, 0, alignment=Qt.AlignLeft)
			fr1right_layout.addWidget(lbl2, i, 1, alignment=Qt.AlignLeft)
			fr1right_layout.addWidget(lbl3, i, 2, alignment=Qt.AlignLeft)
			for p in [lbl1, lbl2, lbl3]:
				munculkan(p)
			
		fr3 = QFrame()
		fr3.setStyleSheet(style_frame_putih("transparent"))
		
		fr3_layout = QGridLayout(fr3)
		keuangan = getData("keuangan")
		
		saldo, masuk, untung, keluar = 0, 0, 0, 0
		for x in keuangan:
			saldo += x["saldo"] + x["keuntungan"] - x["total_pengeluaran"]
			masuk += x["pemasukan"]
			untung += x["keuntungan"]
			keluar += x["total_pengeluaran"]
			break
		btn1 = QPushButton(f"{tr('Saldo bersih')}: {pretty_money(saldo)}")
		btn2 = QPushButton(f"{tr('Pemasukan')}: {pretty_money(masuk)}")
		btn3 = QPushButton(f"{tr('Pengeluaran')}: {pretty_money(keluar)}")
		btn4 = QPushButton(f"{tr('Keuntungan')}: {pretty_money(untung)}")
		btn5 = button(tr("Tambah saldo"), font_size_normal, bg)
		btn6 = button(tr("Reset saldo"), font_size_normal, bg)
		
		for x in [btn1, btn2, btn3, btn4]:
			x.setStyleSheet(f"""
				QPushButton {{
					font-size: {font_size_judul}px;
					font-weight: bold;
					border: 1px solid transparent;
					padding: 5px;
					border-radius: 2px;
				}}
				QPushButton:hover {{
					color: {bg};
					background-color: transparent;
					border: 1px solid {bg};
					border-radius: 2px;
				}}
				QPushButton:pressed {{
					color: {bg};
					background-color: transparent;
					border: 1px solid {bg};
					border-radius: 2px;
				}}
			""")
		fr3_layout.addWidget(btn1, 0, 0)
		fr3_layout.addWidget(btn2, 0, 1)
		fr3_layout.addWidget(btn3, 1, 0)
		fr3_layout.addWidget(btn4, 1, 1)
		fr3_layout.addWidget(btn5, 0, 2)
		fr3_layout.addWidget(btn6, 1, 2)
		for p in [btn1, btn2, btn3, btn4, btn5, btn6]:
			munculkan(p)
		
		for x in [fr1left, fr1right]:
			fr1_layout.addWidget(x)
		for x in [fr1, fr2, fr3]:
			f3_layout.addWidget(x)
		for x in [btn_ganti, btn_hapus, btn_edit, btn_hapus_profil]:
			x.setStyleSheet(style_button(bg, font_size_normal))
			fr2_layout.addWidget(x, alignment=Qt.AlignmentFlag.AlignTop)
			munculkan(x)
		
		def ganti_foto_profil():
			if not va("ganti foto profil"):
				QMB.critical(None, "", tr("Anda tidak diizinkan"))
				return
			file, _ = QFileDialog.getOpenFileName()
			if not file:
				return
			photo = Image.open(file)
			with open(file, "rb") as f:
				files = {"file": f}
				if koneksi["connect"] == 1:
					try:
						res = requests.post(f"{SERVER_URL}/upload_foto_profil", files=files)
						if res.status_code == 200:
							simpan_foto_profil_sementara()
							QMB.information(None, tr("Berhasil"), tr("Update foto profil berhasil"))
							profil_func()
						else:
							QMB.warning(None, tr("Gagal"), f"{res.status_code}")
					except Exception as e:
						QMB.critical(None, "Error", f"{e}")
						return
				else:
					name = "foto profil.png"
					file_path = os.path.join(folder_foto_profil, name)
					photo.save(file_path)
					QMB.information(None, tr("Berhasil"), tr("Update foto profil berhasil"))
					profil_func()
		
		def hapus_foto_profil():
			if not va("hapus foto profil"):
				QMB.critical(None, "", tr("Anda tidak diizinkan"))
				return
			global foto_profil
			if askyesno(tr("Konfirmasi"), tr("Anda yakin akan menghapus foto profil?")):
				foto_profil = {}
				if koneksi["connect"] == 1:
					upload_data("hapus_foto_profil", {}, tr("Foto profil telah dihapus"))	
				else:
					path = os.path.join(folder_foto_profil, "foto profil.png")
					if os.path.exists(path):
						os.remove(path)
					else:
						QMB.warning(None, tr("Kosong"), tr("Tidak ada foto profil"))
						return
					QMB.information(None, tr("Berhasil"), tr("Foto profil telah dihapus"))
				simpan_foto_profil_sementara()
				profil_func()
		
		def edit_profil():
			if not va("edit profil"):
				QMB.critical(None, "", tr("Anda tidak diizinkan"))
				return
			clear_widgets(f3)
			fr = QFrame()
			fr_layout = QHBoxLayout(fr)
			kiri, kanan = QFrame(), QFrame()
			kirilayout, kananlayout = QVBoxLayout(kiri), QVBoxLayout(kanan)
			for x in [kirilayout, kananlayout]:
				x.setAlignment(Qt.AlignmentFlag.AlignTop)
				
			list_entry = [
				("Masukkan nama", next((p["nama"] for p in profil_data), "")),
				("Masukkan alamat", next((p["alamat"] for p in profil_data), "")),
				("Masukkan Telp/WA", next((p["kontak"] for p in profil_data), "")),
				("Masukkan email", next((p["email"] for p in profil_data), "")),
				("Masukkan website", next((p["website"] for p in profil_data), "")),
				("Masukkan jenis usaha", next((p["jenis"] for p in profil_data), ""))
			]
			result = {}
			for i, (p, q) in enumerate(list_entry):
				teks = p.split()
				key = " ".join(teks[1:])
				label = QLabel(key.upper())
				label.setStyleSheet(f"""
					QLabel {{
						font-size: {font_size_judul}px;
						font-weight: bold;
					}}
				""")
				ent = entry(p, font_size_normal)
				ent.setText(q)
				result[key] = ent
				if i < 3:
					kirilayout.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop)
					kirilayout.addWidget(ent, alignment=Qt.AlignmentFlag.AlignTop)
				else:
					kananlayout.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop)
					kananlayout.addWidget(ent, alignment=Qt.AlignmentFlag.AlignTop)
			
			def simpan_profil():
				data = {key: value.text().strip() for key, value in result.items()}
				n = data["nama"]
				a = data["alamat"]
				k = data["Telp/WA"]
				e = data["email"]
				w = data["website"]
				j = data["jenis usaha"]
				if not all([n, a, k, e, w, j]):
					QMB.critical(None, tr("Gagal"), tr("Data tidak lengkap"))
					return #tidak berfungsi karena seluruh data diisi. keadaan sesuai harapan
				if koneksi["connect"] == 1: #kita lupakan dulu bagian koneski = 1 alias offline
					data = {
						"nama": n,
						"alamat": a,
						"kontak": k,
						"email": e,
						"website": w,
						"jenis": j
					}
					upload_data("tambah_profil", data, tr("Profil berhasil diperbarui!"))
				else: #fokus disini
					cursor.execute("DELETE FROM profil")
					cursor.execute("INSERT INTO profil (nama, alamat, kontak, email, website, jenis) VALUES (?, ?, ?, ?, ?, ?)", (n, a, k, e, w, j))
					conn.commit()
					QMB.information(None, tr("Berhasil"), tr("Profil telah diperbarui"))
					profil_func()
					
			btn_save = button(tr("Simpan"), font_size_normal, bg)
			btn_save.clicked.connect(lambda: safe_run(simpan_profil))		
			for x in [fr, btn_save]:
				f3_layout.addWidget(x)
			for x in [kiri, kanan]:
				fr_layout.addWidget(x)
		
		def hapus_profil():
			if not va("hapus profil"):
				QMB.critical(None, "", tr("Anda tidak diizinkan"))
				return
			if askyesno(tr("Konfirmasi"), tr("Apa Anda yakin ingin menghapus profil toko kita?")):
				if koneksi["connect"] == 1:
					upload_data("hapus_profil", None, tr("Profil telah dihapus!"))
				else:
					cursor.execute("DELETE FROM profil")
					conn.commit()
					QMB.information(None, tr("Berhasil"), tr("Profil telah dihapus!"))
				profil_func()
		 
		def tambah_saldo():
			if not va("tambah keuangan"):
				QMB.critical(None, "", tr("Anda tidak diizinkan"))
				return
			jd, yes = input_int(tr("Saldo"), tr("Masukkan jumlah saldo Anda"))
			if yes:
				if askyesno(tr("Konfirmasi"), f"{tr('Anda akan menambahkan saldo sebanyak')} {pretty_money(jd)} {tr('kedalam saldo kas')}!"):
					if koneksi["connect"] == 1:
						data = {"uang": jd}
						upload_data("tambah_saldo", data, f"{tr('Saldo senilai')} {pretty_money(jd)} {tr('telah ditambahkan')}")
					else:
						cursor.execute("SELECT saldo FROM keuangan")
						data = cursor.fetchone()
						saldo_terbaru = data["saldo"] + int(jd)
						cursor.execute("UPDATE keuangan SET saldo = ? WHERE id = ?", (saldo_terbaru, 1))
						conn.commit()
						QMB.information(None, tr("Berhasil"), f"{tr('Saldo saat ini senilai')} {pretty_money(saldo_terbaru)}")
					profil_func()
		
		def reset_keuangan():
			if not va("reset keuangan"):
				QMB.critical(None, "", tr("Anda tidak diizinkan"))
				return
			if askyesno(tr("Konfirmasi"), tr("Anda akan menghapus seluruh laporan keuangan Anda!")):
				if koneksi["connect"] == 1:
					upload_data("reset_keuangan", {}, tr("Keuangan telah direset!"))
				else:
					cursor.execute("UPDATE keuangan SET pemasukan = ?, total_pengeluaran = ?, keuntungan = ?, saldo = ? WHERE id = ?", (0, 0, 0, 0, 1))
					conn.commit()
				profil_func()
	   					
		btn_ganti.clicked.connect(ganti_foto_profil)
		btn_hapus.clicked.connect(hapus_foto_profil)
		btn_edit.clicked.connect(edit_profil)
		btn_hapus_profil.clicked.connect(hapus_profil)
		btn5.clicked.connect(tambah_saldo)
		btn6.clicked.connect(reset_keuangan)
		
	def daftar_produk_lama(): #dijadwalkan
		if not va("produk"):
			QMB.critical(None, "", tr("Anda tidak diizinkan"))
			return
		ff = format_uang_app
		lbl_judul.setText(tr("DAFTAR PRODUK"))
		for x in [f2, f3]:
			clear_widgets(x)
		
		spinner = set_spinner(window)
		QApplication.processEvents()
		produk_data = getData("produk")
		frame_atas = QFrame()
		frame_bawah = QFrame()
		
		frame_atas_layout = QVBoxLayout(frame_atas)
		frame_bawah_layout = QHBoxLayout(frame_bawah)
		frame_bawah_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		frame_bawah.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
		
		header_tabel = ["Id", "Barcode", "Nama", "Jumlah", "Harga modal", "Harga jual"]
		tabel, model = table_maker(header_tabel)

		def take_data():
			try:
				idx = tabel.currentIndex()
				mod = idx.model()
				row = idx.row()
				data = [mod.item(row, col).text() for col in range(mod.columnCount())]
				return data
			except Exception:
				return []
				
		def detail_produk():
			if not va("detail produk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			data = take_data()
			if not data:
				QMB.critical(None, tr("Tidak ada data"), tr("Silahkan pilih data dari tabel terlebih dahulu"))
				return
			id = data[0]
			d = next((p for p in produk_data if p["id_produk"] == id), None)
			info = [
				("Barcode", d["barcode"], "Nama", d["nama"]),
				("Kategori", d["kategori"], "Supplier", d["supplier"]),
				("Kadaluarsa", d["kadaluarsa"], "Jumlah", str(d["jumlah"])),
				("Satuan beli", d["satuan_beli"], "Satuan jual", d["satuan_jual"]),
				("Harga beli", pretty_money(d["harga_beli"]), "Harga jual", pretty_money(d["harga_jual"])),
				("Harga modal", pretty_money(d["harga_modal"]), "Isi satuan", str(d["isi_satuan"])),
				("Poin member", str(d["poin"]), "", "")
			]
			
			clear_widgets(frame_atas)
			fr = QFrame()
			fr.setStyleSheet(style_frame(bg))
			fr_lay = QGridLayout(fr)
			for i, (a, b, c, d) in enumerate(info):
				lbla, lblb, lblc, lbld, lble, lblf, lblg = QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel()
				for x in [lbla, lblb, lblc, lbld, lble, lblf, lblg]:
					x.setStyleSheet(style_label(font_size_normal))
				for x in [lblb, lblf]:
					x.setText(":")
				lbld.setText(" | ")
				lbla.setText(a)
				lblc.setText(b)
				lble.setText(c)
				lblg.setText(d)
				fr_lay.addWidget(lbla, i, 0)
				fr_lay.addWidget(lblb, i, 1)
				fr_lay.addWidget(lblc, i, 2)
				fr_lay.addWidget(lbld, i, 3)
				fr_lay.addWidget(lble, i, 4)
				fr_lay.addWidget(lblf, i, 5)
				fr_lay.addWidget(lblg, i, 6)
			frame_atas_layout.addWidget(fr)
		
		def tambah_stok():
			if not va("tambah stok"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			index = tabel.currentIndex()
			if not index.isValid():
				QMB.critical(None, tr("Tidak ada data"), tr("Silahkan pilih data dari tabel terlebih dahulu"))
				return				
			row = index.row()
			column = 3
			row_fokus = model.index(row, column)
			tabel.setCurrentIndex(row_fokus)
			tabel.edit(row_fokus)
			
		def simpan_stok():
			data = take_data()
			try:
				x = int(data[3])
			except ValueError:
				QMB.critical(None, tr("Gagal"), tr("Masukkan angka dengan benar"))
				return
			d = next((p for p in produk_data if p["id_produk"] == data[0]), None)
			total_stok = int(d['jumlah']) + x
			if total_stok > d["jumlah_tertinggi"]:
				stok_tertinggi = total_stok
			else:
				stok_tertinggi = d["jumlah_tertinggi"]
				
			datriw = {
				"waktu": now_str(),
				"aksi": "Tambah stok",
				"nama": d["nama"],
				"jumlah": x,
				"barcode": d["barcode"],
				"stok_terbaru": int(d["jumlah"]) + x,
				"operator": nama_operator(),
				"sumber": komputer()
			}
			if koneksi["connect"] == 1:
				data = {
					"nama": d["nama"],
					"barcode": d["barcode"],
					"tambahan": x,
					"jumlah_tertinggi": stok_tertinggi
				}
				upload_data("tambah_stok", {"data_tambah": data, "riwayat": datriw}, f"Stok {d['nama']} saat ini adalah {d['jumlah'] + x}")
				daftar_produk()
			else:
				cursor.execute("UPDATE produk SET jumlah = ?, jumlah_tertinggi = ? WHERE id = ?", (total_stok, stok_tertinggi, d["id"]))				
				cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, stok_terbaru, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (now_str(), "Tambah stok", d["nama"], x, d["barcode"], total_stok, nama_operator(), komputer()))
				conn.commit()
				QMB.information(None, tr("Berhasil"), f"Stok {d['nama']} saat ini adalah {d['jumlah']}")
				daftar_produk()
							
		def tampilkan_produk(teks=""):
			model.removeRows(0, model.rowCount())
			for p in produk_data:
				nama = p["nama"]
				if teks.lower() in nama.lower():
					item = [
						QStandardItem(p["id_produk"]),
						QStandardItem(p["barcode"]),
						QStandardItem(nama),
						QStandardItem(format_unit(p["jumlah"], p["satuan_jual"])),
						QStandardItem(pretty_money(p["harga_modal"])),
						QStandardItem(pretty_money(p["harga_jual"]))
					]
					model.appendRow(item)
					QApplication.processEvents()
		
		def hapus_produk():
			if not va("hapus produk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			data = take_data()
			if not data:
				QMB.critical(None, tr("Tidak ada data"), tr("Silahkan pilih data dari tabel terlebih dahulu"))
				return
				
			d = next((p for p in produk_data if p["id_produk"] == data[0]), None)
			if askyesno(tr("Konfirmasi"), f"{tr('Anda yakin ingin menghapus produk')} {d['nama']}?"):
				data = {
					"waktu": now_str(),
					"aksi": "Hapus produk",
					"nama": d["nama"],
					"id": d["id"],
					"jumlah": d["jumlah"],
					"barcode": d["barcode"],
					"operator": nama_operator(),
					"sumber": komputer()
				}
							
				if koneksi["connect"] == 1:
					upload_data("hapus_produk", data, tr("Produk telah berhasil dihapus"))
					
				else:
					cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Hapus produk", d["nama"], d["jumlah"], d["barcode"], nama_operator(), komputer()))
					cursor.execute("DELETE FROM produk WHERE id = ?", (d["id"], ))			
					conn.commit()
					QMB.information(None, tr("Berhasil"), tr("Produk telah berhasil dihapus"))
				daftar_produk()
					
		def edit_produk(): #dijadwalkan
			if not va("edit produk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			data = take_data()
			if not data:
				QMB.critical(None, tr("Tidak ada data"), tr("Silahkan pilih data dari tabel terlebih dahulu"))
				return
			d = next((p for p in produk_data if p["id_produk"] == data[0]), None)
			fields = [
				("barcode", str),
				("nama", str),
				("kadaluarsa", str),
				("jumlah", str),
				("harga_beli", pretty_money),
				("harga_jual", pretty_money),
				("harga_modal", pretty_money),
				("isi_satuan", str),
				("stok_minimum", str),
				("poin", str),
				("catatan", str)
			]
			clear_widgets(frame_atas)
			
			fr = QFrame()
			fr_layout = QGridLayout(fr)
			fr1, fr2, fr3, fr4 = QFrame(), QFrame(), QFrame(), QFrame()
			
			fr_layout.addWidget(fr1, 0, 0)
			fr_layout.addWidget(fr2, 0, 1)
			fr_layout.addWidget(fr3, 1, 0)
			fr_layout.addWidget(fr4, 1, 1)
			fr1_layout, fr2_layout, fr3_layout, fr4_layout = QVBoxLayout(fr1), QVBoxLayout(fr2), QVBoxLayout(fr3), QVBoxLayout(fr4)
			btn_save = button(tr("Simpan"), font_size_normal, bg)
			btn_generate = button("Generate barcode", font_size_normal, bg)
			btn_katalog = button(tr("Gambar katalog"), font_size_normal, bg)
			
			eee, fff, ggg, hhh = QFrame(), QFrame(), QFrame(), QFrame()
			eee.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
			eeelay, ffflay, ggglay, hhhlay = QHBoxLayout(eee), QVBoxLayout(fff), QVBoxLayout(ggg), QVBoxLayout(hhh)
			for x in [eeelay, ffflay, ggglay, hhhlay]:
				x.setAlignment(Qt.AlignmentFlag.AlignTop)
				
			def open_umum():
				for i, x in enumerate([fff, ggg, hhh]):
					x.setVisible(False if i != 0 else True)
						
			def open_diskon():
				for i, x in enumerate([fff, ggg, hhh]):
					x.setVisible(False if i != 1 else True)
			
			def open_tingkat():
				for i, x in enumerate([fff, ggg, hhh]):
					x.setVisible(False if i != 2 else True)
				
			command = [open_umum, open_diskon, open_tingkat]
			btn_umum = button(tr("Utama"), font_size_normal, bg)
			btn_diskon = button(tr("Diskon"), font_size_normal, bg)
			btn_tingkat = button(tr("Tingkat"), font_size_normal, bg)
			for i, x in enumerate([btn_umum, btn_diskon, btn_tingkat]):
				eeelay.addWidget(x)
				x.clicked.connect(command[i])
			
			for i, x in enumerate([eee, fff, ggg, hhh]):
				x.setVisible(True if i in [0,1] else False)
				
			entries = {}
			for i, (key, format) in enumerate(fields):
				lbl = QLabel(key.replace("_", " ").upper())
				lbl.setStyleSheet(style_label_bold(font_size_normal))
				ent = entry("", font_size_normal)
				ent.setText(format(d[key]))
				entries[key] = ent
				
				if i < 6:
					fr1_layout.addWidget(lbl)
					fr1_layout.addWidget(ent)
				else:
					fr2_layout.addWidget(lbl)
					fr2_layout.addWidget(ent)
			
			list_kategori = list({p["kategori"] for p in produk_data})
			list_supplier = list({p["supplier"] for p in produk_data})
			list_satuan_beli = list({p["satuan_beli"] for p in produk_data})
			list_satuan_jual = list({p["satuan_jual"] for p in produk_data})
			fields_combo = [
				("kategori", list_kategori),
				("supplier", list_supplier),
				("satuan_beli", list_satuan_beli),
				("satuan_jual", list_satuan_jual)
			]
			combo_dick = {}
			for i, (key, list_idk) in enumerate(fields_combo):
				lbl = QLabel(key.replace("_", " ").upper())
				lbl.setStyleSheet(style_label_bold(font_size_normal))
				cmb = combobox(font_size_normal, list_idk)
				cmb.setCurrentText(str(d[key]))					
				ent = entry(key.replace("_", " ") + " baru", font_size_normal)
				combo_dick[key] = [cmb, ent]
				fr3_layout.addWidget(lbl)
				fr3_layout.addWidget(cmb)
				fr4_layout.addWidget(ent)
			
			def get_data_combo():
				return {key: r[-1].text().strip() if r[-1].text().strip() != "" else r[0].currentText() for key, r in combo_dick.items()}
								
			def get_data_entry():
				data = {}
				for key, widget in entries.items():
					teks = widget.text().strip()
					if teks.startswith(ff[0]) or teks.endswith(ff[0]):
						teks = teks.replace(ff[0], "").replace(ff[2], "").replace(ff[3], ".")
					data[key] = teks
				return data
				
			def edit_foto_katalog():
				clear_widgets(frame_atas)
				file_path, _= QFileDialog.getOpenFileName()
				if not file_path:
					return
				lbl_prev = QLabel()
				lbl_prev.setFixedSize(500,500)
				lbl_prev.setScaledContents(True)
				btn_save = button(tr("Simpan"), font_size_normal, bg)
				px = QPixmap(file_path)
				lbl_prev.setPixmap(px)
				
				def save():
					if koneksi["connect"] == 1:
						try:
							with open(file_path, "rb") as f:
								files = {"foto": (file_path.split("/")[-1], f, "image/jpeg")}
								data = {"nama": d["nama"]}
								res = requests.post(f"{SERVER_URL}/upload_foto_katalog", files=files, data=data)
								if res.status_code == 200:
									QMB.information(None, tr("Berhasil"), tr("Foto telah diperbarui"))
								else:
									QMB.warning(None, tr("Gagal"), "Gagal upload_foto")
						except Exception as e:
							QMB.critical(None, "", str(e))
					else:
						img = Image.open(file_path).convert("RGB")
						img = img.resize((150, 150), Image.LANCZOS)
						filename = f"{d['nama']}.jpeg"
						path = os.path.join(folder_katalog, filename)
						img.save(path, "jpeg", quality=90, optimize=True)
						QMB.information(None, tr("Berhasil"), tr("Foto telah diperbarui"))				
				btn_save.clicked.connect(save)
				for x in [lbl_prev, btn_save]:
					frame_atas_layout.addWidget(x)
				
			def generate_barcode():
				if askyesno(tr("Konfirmasi"), f"{tr('Generate barcode produk')} {d['nama']}?"):
					nama = d["nama"].split()
					teks_for_generate = nama[0] + "_" + d["id_produk"]
					clear_widgets(frame_atas)
					
					def generate_now():
						brc = barcode.get("code128", entBrc.text().strip(), writer=ImageWriter())
						buffer = BytesIO()
						brc.write(buffer)
						buffer.seek(0)
						pixmap = QPixmap()
						pixmap.loadFromData(buffer.read())
						lbl_preview.setPixmap(pixmap)
						return brc, buffer
					
					def simpan_barcode():
						new = entBrc.text().strip()
						id = d["id_produk"]
						if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
							if koneksi["connect"] == 1:
								doc, buffer = generate_now()
								buffer.seek(0)
								data = {"barcode": new, "id": id}
								files = {"file": (d["nama"] + ".png", buffer, "image/png")}
								path = choose_save_path(d["nama"] + ".png")
								doc.save(path)
								
								try:
									res = requests.post(f"{SERVER_URL}/ganti_barcode", files=files, data=data)
									if res.status_code == 200:
										QMB.information(None, tr("Berhasil"), f"{tr('Barcode produk')} {d['nama']} {tr('telah berhasil diperbarui')}")
									else:
										QMB.warning(None, tr("Gagal"), str(res.status_code))
								except Exception as e:
									QMB.critical(None, "Error", str(e))
							else:
								cursor.execute("UPDATE produk SET barcode = ? WHERE id_produk = ?", (new, d["id_produk"]))
								conn.commit()
								file_name = d["nama"] + ".png"
								folder = choose_folder()
								path = os.path.join(folder, file_name)
								brc, _ = generate_now()
								brc.save(path)
								QMB.information(None, tr("Berhasil"), f"{tr('Barcode produk')} {d['nama']} {tr('telah berhasil diperbarui')}")
								edit_produk()
													
					btn_kembali = button(tr("Kembali"), font_size_normal, "lightgreen")
					lbl_preview = QLabel()
					entBrc = entry(tr("Karakter yang akan dibuat..."), font_size_normal)
					save = button(tr("Simpan"), font_size_normal, bg)
					for x in [btn_kembali, lbl_preview, entBrc, save]:
						frame_atas_layout.addWidget(x)
					entBrc.setText(teks_for_generate)
					entBrc.textChanged.connect(generate_now)
					btn_kembali.clicked.connect(edit_produk)
					save.clicked.connect(simpan_barcode)
					generate_now()
						
			def simpan():
				e = get_data_entry()
				c = get_data_combo()
				b = copy.deepcopy(dict(d))
				try:
					jumlah = int(e.get("jumlah", 0))
					harga_beli = float(e.get("harga_beli", 0))
					isi_satuan = int(e.get("isi_satuan", 0))
				except ValueError:
					QMB.critical(None, tr("Gagal"), tr("Masukkan angka dengan benar"))
					return
				stok_tertinggi = jumlah if jumlah > b["jumlah_tertinggi"] else b["jumlah_tertinggi"]
				harga_modal = float(harga_beli / isi_satuan)
				choosen_produk = []
				choosen_produk[:] = [p for p in produk_data if p["id"] != d["id"]]
				for p in choosen_produk:
					if p["nama"].lower() == e.get("nama", "").lower() or p["barcode"] == e.get("barcode", ""):
						QMB.critical(None, "Duplikasi produk", "Terdeteksi duplikasi produk")
						return
				if askyesno(tr("Konfirmasi"), f"{tr('Apakah data produk')} {e.get('nama', '')} {tr('sudah benar')}?"):
					if koneksi["connect"] == 1:
						data = {
							"nama_lama": b["nama"],
							"barcode_lama": b["barcode"],
							"id": b["id"],
							"barcode": e.get("barcode", ""),
							"nama": e.get("nama", ""),
							"catatan": e.get("catatan", ""),
							"kategori": c.get("kategori", ""),
							"kadaluarsa": e.get("kadaluarsa", ""),
							"satuan_beli": c.get("satuan_beli", ""),
							"satuan_jual": c.get("satuan_jual", ""),
							"isi_satuan": isi_satuan,
							"harga_beli": harga_beli,
							"harga_jual": float(e.get("harga_jual", 0)),
							"jumlah": jumlah,
							"stok_minimum": int(e.get("stok_minimum", 0)),
							"supplier": c.get("supplier", ""),
							"jumlah_tertinggi": stok_tertinggi,
							"poin": int(e.get("poin", 0))
						}
						datriw = {
							"waktu": now_str(),
							"aksi": "Edit produk",
							"nama_lama": b["nama"],
							"nama": e.get("nama", ""),
							"jumlah_lama": b["jumlah"],
							"jumlah": jumlah,
							"modal_lama": b["harga_modal"],
							"harga_modal": float(e.get("harga_modal", 0)),
							"jual_lama": b["harga_jual"],
							"harga_jual": float(e.get("harga_jual", 0)),
							"catatan_lama": b["catatan"],
							"catatan": e.get("catatan", ""),
							"barcode": e.get("barcode", ""),
							"operator": nama_operator(),
							"sumber": komputer()
						}
						kemasan = {
							"data": data,
							"riwayat": datriw
						}
						upload_data("edit_produk", kemasan, f"Data {d['nama']} telah diperbarui!")
					else:
						cursor.execute("UPDATE produk SET barcode = ?, nama = ?, kategori = ?, catatan = ?, kadaluarsa = ?, satuan_beli = ?, satuan_jual = ?, isi_satuan = ?, supplier = ?, harga_beli = ?, harga_modal = ?, harga_jual = ?, jumlah = ?, jumlah_tertinggi = ?, stok_minimum = ?, poin = ? WHERE id = ?", (e.get("barcode", ""), e.get("nama", ""), c.get("kategori", ""), e.get("catatan", ""), e.get("kadaluarsa", ""), c.get("satuan_beli", ""), c.get("satuan_jual", ""), e.get("isi_satuan", 0), c.get("supplier", ""), e.get("harga_beli", 0), e.get("harga_modal", 0), e.get("harga_jual", 0), jumlah, stok_tertinggi, e.get("stok_minimum", 0), e.get("poin", 0), b["id"]))		
						cursor.execute("INSERT INTO riwayat (waktu, aksi, nama_lama, nama, jumlah_lama, jumlah, modal_lama, harga_modal, jual_lama, harga_jual, catatan_lama, catatan, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (now_str(), "Edit produk", b["nama"], e.get("nama", ""), b["jumlah"], e.get("jumlah", 0), b["harga_modal"], e.get("harga_modal", 0), b["harga_jual"], e.get("harga_jual", 0), b["catatan"], e.get("catatan", ""), e.get("barcode", ""), nama_operator(), komputer()))
						conn.commit()
						QMB.information(None, tr("Berhasil"), f"Data {d[2]} telah diperbarui!")
					daftar_produk()
			
			label_judul = QLabel(tr("Menu pengaturan diskon"))
			label_judul.setStyleSheet(style_label_bold(font_size_normal))
			entPersen = entry(tr("Masukkan persentase diskon"), font_size_normal)
			entMin = entry(tr("Masukkan minimum pembelian"), font_size_normal)
			btn_save2 = button(tr("Simpan"), font_size_normal, bg)
			
			def simpan_diskon(): #dijadwalkan
				data_lain = get_data_entry()
				barcode = data_lain.get("barcode", "")
				nama = data_lain.get("nama", "")
				try:
					persen = int(entPersen.text().strip())
					min_qty = int(entMin.text().strip())
					harga_jual = float(data_lain.get("harga_jual", 0).strip().replace(format_uang_app[0], "").replace(format_uang_app[2], "").replace(format_uang_app[3], "."))
				except ValueError:
					QMB.warning(None, tr("Gagal"), tr("Masukkan angka dengan benar"))
					return
				
				datriw = {
					"waktu": now_str(),
					"aksi": "Tambah produk diskon",
					"nama": nama,
					"barcode": barcode,
					"jumlah": 1,
					"operator": nama_operator(),
					"sumber": komputer()
				}
				if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
					if koneksi["connect"] == 1:
						data = {
							"nama": nama,
							"barcode": barcode,
							"harga_jual": harga_jual,
							"persen": persen,
							"min": min_qty
						}
						kemasan = {
							"data": data,
							"riwayat": datriw
						}
						upload_data("tambah_produk_diskon", kemasan, f"{d['nama']} telah ditambahkan ke produk diskon")
					else:
						cursor.execute("SELECT * FROM produk_diskon WHERE barcode = ? OR nama = ?", (barcode, nama))
						disk = cursor.fetchone()
						if disk:
							cursor.execute("UPDATE produk_diskon SET persen = ?, min = ? WHERE id = ?", (persen, min_qty, disk["id"]))
						else:
							cursor.execute("INSERT INTO produk_diskon (barcode, nama, harga_jual, persen, min) VALUES (?, ?, ?, ?, ?)", (barcode, nama, harga_jual, persen, min_qty))
						cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, barcode, jumlah, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Tambah produk diskon", nama, barcode, 1, nama_operator(), komputer()))
						conn.commit()			
						QMB.information(None, tr("Berhasil"), f"{d['nama']} {tr('telah ditambahkan ke produk diskon')}")
			
			btn_save2.clicked.connect(simpan_diskon)
			
			for x in [label_judul, entPersen, entMin, btn_save2]:
				ggglay.addWidget(x)		
			for x in [fr1_layout, fr2_layout, fr3_layout, fr4_layout]:
				x.setAlignment(Qt.AlignmentFlag.AlignTop)
			for x in [fr, btn_save, btn_generate, btn_katalog]:
				ffflay.addWidget(x)
			for x in [eee, fff, ggg, hhh]:
				frame_atas_layout.addWidget(x)
			btn_save.clicked.connect(simpan)
			btn_generate.clicked.connect(generate_barcode)
			btn_katalog.clicked.connect(edit_foto_katalog)
		
		def tambah_produk_baru():
			if not va("tambah produk baru"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			margin_data = getData("margin")
			list_entry = ["barcode", "nama", "harga beli", "isi satuan", "harga jual", "jumlah", "minimum stok", "catatan"]
			list_kategori = list({p["kategori"] for p in produk_data})
			list_supplier = list({p["supplier"] for p in produk_data})
			list_satuan_beli = list({p["satuan_beli"] for p in produk_data})
			list_satuan_jual = list({p["satuan_jual"] for p in produk_data})
			fields_combo = [
				("kategori", list_kategori),
				("supplier", list_supplier),
				("satuan_beli", list_satuan_beli),
				("satuan_jual", list_satuan_jual)
			]
			clear_widgets(frame_atas)
			top, atas, bawah = QFrame(), QFrame(), QFrame()
			atas_layout, bawah_layout = QHBoxLayout(atas), QHBoxLayout(bawah)
			atas_kiri, atas_kanan, bawah_kiri, bawah_kanan = QFrame(), QFrame(), QFrame(), QFrame()
			atas_kiri_layout, bawah_kiri_layout, atas_kanan_layout, bawah_kanan_layout = QVBoxLayout(atas_kiri), QVBoxLayout(bawah_kiri), QVBoxLayout(atas_kanan), QVBoxLayout(bawah_kanan)
			for x in [top, atas, bawah]:
				frame_atas_layout.addWidget(x)
			for i, x in enumerate([atas_kiri, atas_kanan, bawah_kiri, bawah_kanan]):
				atas_layout.addWidget(x) if i in [0, 1] else bawah_layout.addWidget(x)
			top_layout = QVBoxLayout(top)
			lbl_rec = QLabel()
			lbl_rec.setStyleSheet(style_label_bold(font_size_normal))
			top_layout.addWidget(lbl_rec)
			
			def hitung_harga_jual(e):
				data = get_data_entry()
				dt = get_data_combo()
				sb = dt.get("satuan_beli", "")
				sj = dt.get("satuan_jual", "")
				ktgr = dt.get("kategori", "")
				try:
					i = int(data.get("isi satuan", 0))
					hb = float(data.get("harga beli", 0))
				except ValueError:
					return
				merg = next((float(p["margin"]) for p in margin_data if p["kategori"].lower() == ktgr.lower()), 0.5)
				hm = hb / i
				hj = hm + (hm * merg)
				hjp = hb + (hb * merg)				
				lbl_rec.setText(f"Harga modal: {pretty_money(hm)}\n" + f"Harga jual per-{sj}: {pretty_money(hj)}\nHarga jual per-{sb}: {pretty_money(hjp)}")
			
			entries = {}
			for i, x in enumerate(list_entry):
				lbl = QLabel(x.upper())
				lbl.setStyleSheet(style_label_bold(font_size_normal))
				ent = entry("Masukkan " + x, font_size_normal)
				if i < 4:
					atas_kiri_layout.addWidget(lbl)
					atas_kiri_layout.addWidget(ent)
				else:
					atas_kanan_layout.addWidget(lbl)
					atas_kanan_layout.addWidget(ent)
				entries[x] = ent
				if i in [2, 4]:
					ent.textChanged.connect(lambda *args, e=ent: format_rupiah(e))
				if i in [2, 3]:
					ent.textChanged.connect(lambda *args, e=ent: hitung_harga_jual(e))
			combos = {}
			for i, (x, y) in enumerate(fields_combo):
				cmb = combobox(font_size_normal, y)
				ent = entry("Masukkan " + x.replace("_", " ") + " baru", font_size_normal)
				bawah_kiri_layout.addWidget(cmb)
				bawah_kanan_layout.addWidget(ent)
				combos[x] = [cmb, ent]
			
			l = QLabel("Tanggal kadaluarsa")
			l.setStyleSheet(style_label_bold(font_size_normal))
			tgl = make_date()
			btn_save = button(tr("Simpan"), font_size_normal, bg)
			
			def get_data_entry():
				data = {}
				for key, widget in entries.items():
					teks = widget.text().strip()
					if teks.startswith(ff[0]) or teks.endswith(ff[0]):
						teks = teks.replace(ff[0], "").replace(ff[2], "").replace(ff[3], ".")
					data[key] = teks
				return data
			
			def get_data_combo():
				data = {}
				for key, value in combos.items():
					cmb, ent = value[0].currentText(), value[1].text().strip()
					data[key] = ent if ent != "" else cmb
				return data
			
			def simpan():
				ent = get_data_entry()
				cmb = get_data_combo()
				barc = ent.get("barcode", "")
				name = ent.get("nama", "")
				note = ent.get("catatan", "")
				cls = cmb.get("kategori", "")
				expired = datetime.strptime(tgl.text().strip(), "%d/%m/%y").strftime("%m/%d/%y")
				sat_beli = cmb.get("satuan_beli", "")
				sat_jual = cmb.get("satuan_jual", "")
				try:
					isi_sat = int(ent.get("isi satuan", 0))
					hj = float(ent.get("harga jual", 0))
					hb = float(ent.get("harga beli", 0))
					stok = int(ent.get("jumlah", 0))
					ms = int(ent.get("minimum stok", 0))
				except ValueError:
					QMB.critical(None, tr("Gagal"), tr("Masukkan angka dengan benar"))
					return
				sup = cmb.get("supplier", "")
				modal_price = hb / isi_sat
				
				if not all([name, cls, expired, sat_beli, sat_jual, hj]):
					QMB.warning(None, tr("Gagal"), tr("Beberapa data harus diisi"))
					return
				same = False
				for p in produk_data:
					if p["nama"].lower() == name.lower() or p["barcode"] == barc:
						QMB.warning(None, tr("Duplikat"), "Terdeteksi duplikasi produk!")
						same = True
						break
				if not same:
					data = {
						"barcode": barc,
						"nama": name,
						"kategori": cls,
						"kadaluarsa": expired,
						"satuan_beli": sat_beli,
						"satuan_jual": sat_jual,
						"isi_satuan": isi_sat,
						"supplier": sup,
						"harga_beli": hb,
						"harga_modal": float(modal_price),
						"harga_jual": hj,
						"jumlah": stok,
						"jumlah_tertinggi": stok,
						"stok_minimum": ms,
						"operator": nama_operator(),
						"sumber": komputer()
					}
					if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
						if koneksi["connect"] == 1:
							upload_data("tambah_produk", data, f"Produk baru {name} telah ditambahkan!")
								
						else:
							id = datetime.now().strftime("%f")
							
							cursor.execute("""INSERT INTO produk (id_produk, barcode, nama, kategori, catatan, kadaluarsa, satuan_beli, satuan_jual, isi_satuan, supplier, harga_beli, harga_modal, harga_jual, jumlah, jumlah_tertinggi, stok_minimum, poin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (id, barc, name, cls, note, expired, sat_beli, sat_jual, isi_sat, sup, hb, modal_price, hj, stok, stok, ms, 0))
							cursor.execute("""INSERT INTO riwayat (waktu, aksi, nama, barcode, jumlah, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)""", (now_str(), "Tambah produk", name, barc, stok, nama_operator(), komputer()))
							
							cursor.execute("SELECT * FROM margin WHERE kategori = ?", (cls, ))
							mrg = cursor.fetchone()
							if not mrg:
								cursor.execute("""INSERT INTO margin (kategori, margin) VALUES (?, ?)""", (cls, 0.5))
								
							cursor.execute("SELECT * FROM supplier WHERE nama = ?", (sup, ))
							supl = cursor.fetchone()
							if not supl:
								cursor.execute("""INSERT INTO supplier (nama) VALUES (?)""", (sup, ))
							conn.commit()				
							QMB.information(None, tr("Berhasil"), f"Produk baru {name} telah ditambahkan!")
						tambah_produk()
			
			for x in [l, tgl, btn_save]:
				frame_atas_layout.addWidget(x)
			for x in [atas_kiri, atas_kanan, bawah_kiri, bawah_kanan]:
				x.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
			btn_save.clicked.connect(simpan)
						
		btn_detail = label_photo("Detail", resource_path("Pictures/detail.png"), icon_size)
		btn_tambah = label_photo("Tambah stok", resource_path("Pictures/add.png"), icon_size)
		btn_edit = label_photo("Edit", resource_path("Pictures/edit.png"), icon_size)
		btn_hapus = label_photo("Hapus", resource_path("Pictures/hehehe.png"), icon_size)
		btn_tingkat = label_photo("Multi harga", resource_path("Pictures/add_price.png"), icon_size)
		
		btn_kembali = button_photo(tr("Kembali"), resource_path("Pictures/kembali.png"), icon_size, master)
		btn_refresh = button_photo("Refresh", resource_path("Pictures/refresh.png"), icon_size, daftar_produk)
		btn_produk_baru = button_photo(tr("Produk baru"), resource_path("Pictures/produk_baru.png"), icon_size, tambah_produk_baru)
		frame_cari = QFrame()
		frame_cari_layout = QVBoxLayout(frame_cari)
		entry_cari_produk = entry("Masukkan nama produk...", font_size_normal)
		fr_vawah = QFrame()
		fr_vawah_layout = QHBoxLayout(fr_vawah)
		
		btn_menu = button("Menu", font_size_normal, bg)
		btn_info = button("Info", font_size_normal, bg)
		btn_katalog = button(tr("Katalog"), font_size_normal, bg)
		btn_exp = button(tr("Kadaluarsa"), font_size_normal, bg)
		
		def menu_lain():
			clear_widgets(f3)
			fr = QFrame()
			fr_layout = QHBoxLayout(fr)
			left, right = QFrame(), QFrame()
			left_layout, right_layout = QVBoxLayout(left), QVBoxLayout(right)			
			for x in [left, right]:
				fr_layout.addWidget(x)
			for x in [left_layout, right_layout]:
				x.setAlignment(Qt.AlignmentFlag.AlignTop)
			f3_layout.addWidget(fr)
			left.setFixedWidth(200)
			left.setStyleSheet(style_frame_putih("transparent"))
			
			def pengaturan_margin():
				if not va("pengaturan margin"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
				clear_widgets(right)
				margin_data = getData("margin")
				produk_data = getData("produk")
				
				tabel, model = table_maker(["Id", "Kategori", "Margin", "Jumlah produk"])
				for p in margin_data:
					kategori = p["kategori"]
					jumlah_produk = 0
					for k in produk_data:
						if k["kategori"].lower() == kategori.lower():
							jumlah_produk += 1
					item = [
						QStandardItem(str(p["id"])),
						QStandardItem(kategori),
						QStandardItem(format_persen(p["margin"] * 100)),
						QStandardItem(str(jumlah_produk))
					]
					model.appendRow(item)
				
				def take_row():
					try:
						idx = tabel.currentIndex()
						mod = idx.model()
						row = idx.row()
						data = [mod.item(row, col).text() for col in range(mod.columnCount())]
						return data
					except Exception:
						return []
					
				def tambah_margin():
					nonlocal state_tambah
					state_tambah = True
					add_new_row(4, tabel, model)

				def simpan_tambah():
					nonlocal state_tambah
					if not state_tambah:
						return	
					data = take_row()
					if not data:
						return
					kategori = data[1]
					try:
						margin = int(data[2])
					except ValueError as e:
						QMB.critical(None, "", str(e))
						return
					margin_data = getData("margin")
					for p in margin_data:
						if p["kategori"].lower() == kategori.lower():
							QMB.warning(None, tr("Sudah ada"), tr("Sepertinya kategori tersebut sudah ada.\nSilahkan lakukan edit margin untuk update!"))
							return
					else:
						if koneksi["connect"] == 1:
							data = {
								"kategori": kategori,
								"margin": margin
							}
							upload_data("tambah_margin", data, tr(f"{kategori} {margin} % telah ditambahkan!"))
						else:
							cursor.execute("SELECT * FROM margin WHERE kategori = ?", (kategori, ))
							mrgn = cursor.fetchone()
							if not mrgn:
								cursor.execute("INSERT INTO margin (kategori, margin) VALUES (?, ?)", (kategori, margin / 100))
								conn.commit()
							QMB.information(None, tr("Berhasil"), tr(f"{kategori} {margin} % telah ditambahkan!"))
						state_tambah = False
						pengaturan_margin()
		
				def produk_kategori():
					clear_widgets(right)
					data = take_row()
					if not data:
						QMB.critical(None, tr("Tidak ada data"), tr("Silahkan pilih data dari tabel terlebih dahulu"))
						return
					kategori = data[1].strip().lower()
					header = ["ID PRODUK", "NAMA", "KATEGORI", "JUMLAH", "HARGA JUAL"]
					tab, mod = table_maker(header)
					for p in produk_data:
						if p["kategori"].lower() == kategori:
							data = [
								QStandardItem(p["id_produk"]),
								QStandardItem(p["nama"]),
								QStandardItem(p["kategori"]),
								QStandardItem(format_unit(p["jumlah"], p["satuan_jual"])),
								QStandardItem(pretty_money(p["harga_jual"]))
							]
							mod.appendRow(data)
					right_layout.addWidget(tab)
				
				def edit_margin():
					nonlocal state_tambah
					state_tambah = False
					if state_tambah:
						return
					data = take_row()
					if not data:
						QMB.critical(None, tr("Tidak ada data"), tr("Silahkan pilih data dari tabel terlebih dahulu"))
						return
					kategori = data[1]
					try:
						persen = float(data[2].replace("%", ""))
						id = int(data[0])
					except ValueError as e:
						QMB.critical(None, "", str(e))
						return
					if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
						if koneksi["connect"] == 1:
							data = {
								"kategori": kategori,
								"margin": persen / 100,
								"id": id
							}
							riwayat_dict = {
								"waktu": now_str(),
								"aksi": "Edit margin",
								"nama": kategori,
								"jumlah": persen / 100,
								"barcode": "",
								"operator": nama_operator(),
								"sumber": komputer()
							}
							upload_data("edit_margin", {"data": data, "riwayat": riwayat_dict}, f"{tr('Margin')} {kategori} {tr('telah diubah')}")	
						else:
							cursor.execute("UPDATE margin SET kategori = ?, margin = ? WHERE id = ?", (kategori, persen / 100, id))
							conn.commit()							
							QMB.information(None, tr("Berhasil"), f"{tr('Margin')} {kategori} {tr('telah diubah')}")
						pengaturan_margin()
				
				def simpan_transistor():
					simpan_tambah() if state_tambah else edit_margin()
				
				state_tambah = False			
				btn_tambah = label_photo(tr("Tambah"), resource_path("Pictures/add.png"), icon_size)
				btn_produk = label_photo(tr("Seluruh produk"), resource_path("Pictures/other_menu.png"), icon_size)
				btn_simpan = label_photo(tr("Simpan"), resource_path("Pictures/ddd.png"), icon_size)
				btn_tambah.clicked.connect(tambah_margin)
				btn_produk.clicked.connect(produk_kategori)
				btn_simpan.clicked.connect(simpan_transistor)
				
				fr_bawah = QFrame()
				fr_atas = QFrame()
				fr_atas_layout = QVBoxLayout(fr_atas)
				fr_bawah_layout = QHBoxLayout(fr_bawah)
				fr_atas_layout.addWidget(tabel)
				for x in [fr_atas, fr_bawah]:
					right_layout.addWidget(x)
				for x in [btn_tambah, btn_produk, btn_simpan]:
					fr_bawah_layout.addWidget(x)
					x.setStyleSheet(style_button("transparent", font_size_normal))
							
			def daftar_stok():
				if not va("daftar stok"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
				clear_widgets(right)
				tabel, model = table_maker(["ID", "NAMA", "STATUS", "STOK", "MODAL", "NILAI STOK"])
				fr_bawah = QFrame()
				fr_bawah_layout = QHBoxLayout(fr_bawah)
				
				for p in produk_data:
					status = "Cukup" if p["jumlah"] > p["stok_minimum"] else "Kurang" if 0 < p["jumlah"] <= p["stok_minimum"] else "Habis"
					model.appendRow([
						QStandardItem(p["id_produk"]),
						QStandardItem(p["nama"]),
						QStandardItem(status),
						QStandardItem(format_unit(p["jumlah"], p["satuan_jual"])),
						QStandardItem(pretty_money(p["harga_modal"])),
						QStandardItem(pretty_money(p["harga_jual"] * p["jumlah"]))
					])
					
				for x in [tabel, fr_bawah]:
					right_layout.addWidget(x)
				btn_stokk = label_photo(tr("Tambah stok"), resource_path("Pictures/add.png"), icon_size)
				btn_stokk.setStyleSheet(style_button("transparent", font_size_normal))
				btn_stokk.clicked.connect(daftar_produk)
				fr_bawah_layout.addWidget(btn_stokk)
			
			def daftar_produk_diskon():
				if not va("produk diskon"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
				diskon_data = getData("produk_diskon")
				
				clear_widgets(right)
				tabel, model = table_maker(["BARCODE", "NAMA", "HARGA JUAL", "DISKON", "MINIMUM PEMBELIAN"])
				for x in diskon_data:
					model.appendRow([
						QStandardItem(x["barcode"]),
						QStandardItem(x["nama"]),
						QStandardItem(pretty_money(x["harga_jual"])),
						QStandardItem(format_persen(x["persen"])),
						QStandardItem(format_unit(x["min"], "pcs"))
					])
				
				def hapus_produk_diskon():
					data = tabel.currentIndex()
					mod = data.model()
					row = data.row()
					dt = [mod.item(row, col).text() for col in range(mod.columnCount())]
					barcode = dt[0]
					nama = dt[1]
					if not dt:
						return
					if askyesno(tr("Konfirmasi"), f"{tr('Apakah Anda yakin akan menghapus')} {nama} {tr('dari daftar produk diskon')}?"):
						if koneksi["connect"] == 1:
							data = {
								"barcode": barcode,
								"nama": nama
							}
							upload_data("hapus_produk_diskon", data, f"{tr('Produk')} {nama} {tr('telah dihapus')}!")
						else:
							cursor.execute("DELETE FROM produk_diskon WHERE nama = ? OR barcode = ?", (nama, barcode))
							conn.commit()
							QMB.information(tr("Berhasil"), f"{tr('Produk')} {nama} {tr('telah dihapus')}")
						daftar_produk_diskon()
					
				right_layout.addWidget(tabel)
				fr = QFrame()
				fr_layout = QHBoxLayout(fr)
				btn_hapus = label_photo(tr("Hapus"), resource_path("Pictures/hehehe.png"), icon_size)
				btn_hapus.setStyleSheet(style_button("transparent", font_size_normal))
				btn_hapus.clicked.connect(hapus_produk_diskon)
				
				right_layout.addWidget(fr)
				fr_layout.addWidget(btn_hapus)
			
			def daftar_tingkat():
				if not va("produk tingkat"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
				def top_widget():
					def make_button(simbol):
						btn = QPushButton(simbol)
						btn.setStyleSheet(f"""
							QPushButton {{
								background-color: transparent;
								border: 1px solid {bg};
								font-size: {font_size_normal}px;
								font-weight: bold;
								border-radius: 2px;
								color: black;
								padding: 5px;
							}}
							QPushButton:pressed {{
								background-color: black;
								color: white;
							}}
						""")
						return btn
								
					return {
						"prev": make_button("«"),
						"judul": button("", font_size_normal, bg),
						"next": make_button("»")
					}
				
				def set_top_widget():
					for i, p in enumerate(list(top_w.values())):
						if i in [0, 2]:
							p.setMaximumWidth(50)
						atas_layout.addWidget(p)
				
				def show_now(off, judul):
					top_w["judul"].setText(judul)
					data = getData(off)
					model.removeRows(0, model.rowCount())
					for p in data:
						model.appendRow([
							QStandardItem(p["id_produk"]),
							QStandardItem(p["barcode"]),
							QStandardItem(p["nama"]),
							QStandardItem(str(p["min_beli"])),
							QStandardItem(pretty_money(p["harga_jual"])),
							QStandardItem(pretty_money(p["harga_modal"]))
						])
					
				def show_tingkat_a():
					show_now("tingkat_a", "DATA TINGKAT A")
				
				def show_tingkat_b():
					show_now("tingkat_b", "DATA TINGKAT B")
				
				def set_command():
					top_w["prev"].clicked.connect(show_tingkat_a)
					top_w["next"].clicked.connect(show_tingkat_b)
					
				def set_layout():
					clear_widgets(right)
					atas, tengah, bawah = QFrame(), QFrame(), QFrame()
					for x in [atas, tengah, bawah]:
						right_layout.addWidget(x)
					return QHBoxLayout(atas), tengah, QHBoxLayout(bawah)
					
				atas_layout, tengah, bawah_layout = set_layout()
				top_w = top_widget()
				set_top_widget()
				set_command()
				tengah_layout = QVBoxLayout(tengah)
				tabel, model = table_maker(["ID", "BARCODE", "NAMA", "MINIMUM", "HARGA JUAL", "HARGA MODAL"])
				tengah_layout.addWidget(tabel)
				show_tingkat_a()
	
			def ekspor_impor():
				if not va("ekspor dan impor"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
				cursor.execute("SELECT * FROM produk")
				data = cursor.fetchall()
				if server_alive():
					pr = requests.get(f"{SERVER_URL}/lihat_data/produk")
					produk = pr.json()
				else:
					if askyesno(tr("Gagal"), tr("Anda belum terhubung ke server. Hubungkan sekarang?")):
						koneksi["connect"] = 1
						simpan_semua(file_koneksi, koneksi)
						konfigurasi_koneksi()
					
				def set_layout():
					clear_widgets(right)
					atas, tengah, bawah = QFrame(), QFrame(), QFrame()
					atas.setStyleSheet(style_frame_putih("transparent"))
					for x in [atas, tengah, bawah]:
						right_layout.addWidget(x)
					return QHBoxLayout(atas), tengah, bawah
				
				def atas_widget():
					eks = label_photo(tr("Ekspor"), resource_path("Pictures/ex.png"), icon_size)
					imp = label_photo(tr("Impor"), resource_path("Pictures/in.png"), icon_size)
					list_command = [menu_ekspor, menu_impor]
					for i, x in enumerate([eks, imp]):
						x.setStyleSheet(style_button(bg, font_size_normal))
						x.clicked.connect(list_command[i])
						
					return {
						"ekspor": eks,
						"impor": imp
					}
				
				def set_atas_layout():
					for p in list(atas_widget().values()):
						atas_layout.addWidget(p)
				
				def menu_ekspor():
					def ekspor_data_sekarang(command, data_sama, data_tidak_sama):
						data = {
							"command": command,
							"sama": [dict(row) for row in data_sama],
							"tidak_sama": [dict(row) for row in data_tidak_sama]
						}
						def eksp_now():
							if server_alive():
								upload_data("ekspor_produk_terpilih", data, tr("Data produk dalam server berhasil diperbarui"))
							else:
								if askyesno(tr("Gagal"), tr("Sepertinya koneksi server bermasalah. Silahkan periksa server dan ulangi proses")):
									eksp_now()
								else:
									return
						eksp_now()
												
					def decision_layout(label):
						clear_widgets(bawah)
						lbl = QLabel(label)
						lbl.setStyleSheet(style_label_bold(font_size_normal))
						frame = QFrame()
						frame_layout = QHBoxLayout(frame)
						btn_overwrite = button(tr("Timpa produk lama"), font_size_normal, bg)
						btn_merge = button(tr("Gabungkan stok"), font_size_normal, bg)
						btn_skip = button(tr("Lewati"), font_size_normal, bg)
						for x in [btn_overwrite, btn_merge, btn_skip]:
							frame_layout.addWidget(x)
						for x in [lbl, frame]:
							bawah_layout.addWidget(x)
						return btn_overwrite, btn_merge, btn_skip
							
					def set_button():
						clear_widgets(tengah)
						list_btn = [
							("semua", ekspor_semua), 
							("Per kategori", ekspor_kategori),
							("Per produk", ekspor_per_produk)
						]
						for a, b in list_btn:
							bt = button(tr(a), font_size_normal, "transparent")
							bt.clicked.connect(b)
							tengah_layout.addWidget(bt)
					
					def ekspor_semua():
						if not data:
							QMB.warning(None, tr("Gagal"), tr("Data kosong. Ekspor data produk dibatalkan"))
							return
						if askyesno(tr("Konfirmasi"), tr("Ekspor semua data produk ke server?")):
							if koneksi["connect"] == 1:
								list_kirim = []
								for x in data:
									list_kirim.append((x["id_produk"], x["barcode"], x["nama"], x["kategori"], x["catatan"], x["kadaluarsa"], x["satuan_beli"], x["satuan_jual"], x["isi_satuan"], x["supplier"], x["harga_beli"], x["harga_modal"], x["harga_jual"], x["jumlah"], x["jumlah_tertinggi"], x["stok_minimum"], x["poin"]))
									
								upload_data("ekspor_produk", list_kirim, tr("Data produk telah diekspor ke server!"))
							else:
								if askyesno("Offline", tr("Sepertinya Anda belum terhubung ke server!\n\nHubungkan sekarang?")):
									koneksi["connect"] = 1
									simpan_semua(file_koneksi, koneksi)
									ekspor_semua()
					
					def ekspor_kategori():
						clear_widgets(bawah)
						list_kategori = list({p["kategori"] for p in data})
						frame = QFrame()
						frame.setStyleSheet(style_frame_putih("transparent"))
						frame_layout = QGridLayout(frame)
						cmb_select_all = checkbutton(tr("Pilih semua"), font_size_normal)
						btn_ekspor = button(tr("Ekspor"), font_size_normal, bg)
						for x in [frame, cmb_select_all, btn_ekspor]:
							bawah_layout.addWidget(x)
						
						dict_combobox = {}
						list_combobox = []
						for i, p in enumerate(list_kategori):
							baris = i // 3
							kolom = i % 3
							cmb = checkbutton(p, font_size_normal)
							dict_combobox[p] = cmb
							list_combobox.append(cmb)
							frame_layout.addWidget(cmb, baris, kolom)
						
						def select_all():
							if cmb_select_all.isChecked():
								for p in list_combobox:
									p.setChecked(True)
							else:
								for p in list_combobox:
									p.setChecked(False)
						
						def ekspor_now():
							terpilih = [ktgr for ktgr, v in dict_combobox.items() if v.isChecked()]
							list_kirim = [p for p in data if p["kategori"] in terpilih]
							data_sama, data_tidak_sama = [], []
							for p in list_kirim:
								for q in produk:
									if q["id_produk"] == p["id_produk"]:
										data_sama.append(p)
										break
								else:
									data_tidak_sama.append(p)
							if data_sama:
								timpa, merge, skip = decision_layout(f"Terdapat {len(data_sama)} data produk yang sama dalam database server")
								list_command = ["overwrite", "merge", "skip"]
								for i, x in enumerate([timpa, merge, skip]):
									x.clicked.connect(lambda checked=False, p=list_command[i]: ekspor_data_sekarang(p, data_sama, data_tidak_sama))
							else:
								ekspor_data_sekarang("lanjutkan", data_sama, data_tidak_sama)
				
						cmb_select_all.toggled.connect(select_all)
						btn_ekspor.clicked.connect(ekspor_now)
					
					def ekspor_per_produk():
						clear_widgets(bawah)
						list_produk = list({p["nama"] for p in data})
						
						frame = QFrame()
						frame.setStyleSheet(style_frame_putih("transparent"))
						frame_layout = QGridLayout(frame)
						cmb_select_all = checkbutton(tr("Pilih semua"), font_size_normal)
						btn_ekspor = button(tr("Ekspor"), font_size_normal, bg)
						for x in [frame, cmb_select_all, btn_ekspor]:
							bawah_layout.addWidget(x)
							
						dict_combobox = {}
						list_combobox = []
						for i, p in enumerate(list_produk):
							baris = i // 3
							kolom = i % 3
							cmb = checkbutton(p, font_size_normal)
							dict_combobox[p] = cmb
							list_combobox.append(cmb)
							frame_layout.addWidget(cmb, baris, kolom)
						
						def select_all():
							if cmb_select_all.isChecked():
								for p in list_combobox:
									p.setChecked(True)
							else:
								for p in list_combobox:
									p.setChecked(False)
						
						def ekspor_now():
							terpilih = [nama for nama, v in dict_combobox.items() if v.isChecked()]
							list_kirim = [p for p in data if p["nama"] in terpilih]
							data_sama, data_tidak_sama = [], []
							for p in list_kirim:
								for q in produk:
									if q["id_produk"] == p["id_produk"]:
										data_sama.append(p)
										break
								else:
									data_tidak_sama.append(p)
							if data_sama:
								timpa, merge, skip = decision_layout(f"Terdapat {len(data_sama)} data produk yang sama dalam database server")
								list_command = ["overwrite", "merge", "skip"]
								for i, x in enumerate([timpa, merge, skip]):
									x.clicked.connect(lambda checked=False, p=list_command[i]: ekspor_data_sekarang(p, data_sama, data_tidak_sama))
							else:
								ekspor_data_sekarang("lanjutkan", data_sama, data_tidak_sama)
		
						cmb_select_all.toggled.connect(select_all)
						btn_ekspor.clicked.connect(ekspor_now)
														
					set_button()	
				
				def menu_impor():
					if not server_alive():
						QMB.warning(None, "Offline", tr("Terjadi masalah koneksi ke server"))
						return
					d = requests.get(f"{SERVER_URL}/lihat_produk")
					data = d.json()
					
					def insert_produk(p, j):
						data = (
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
							values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
							
					def execute_data(command, data_sama, data_tidak_sama):
						if command == "overwrite":
							for p in data_sama:
								id_produk = p["id_produk"]
								cursor.execute("DELETE FROM produk WHERE id_produk = ?", (id_produk, ))
								insert_produk(p, p["jumlah"])
							for p in data_tidak_sama:
								insert_produk(p, p["jumlah"])
						elif command == "merge":
							for p in data_sama:
								jumlah = p["jumlah"]
								cursor.execute("SELECT jumlah FROM produk WHERE id_produk = ?", (p["id_produk"], ))
								jml = cursor.fetchone()
								jumlah_baru = jumlah + jml["jumlah"]
								cursor.execute("DELETE FROM produk WHERE id_produk = ?", (p["id_produk"], ))
								insert_produk(p, jumlah_baru)
							for p in data_tidak_sama:
								insert_produk(p, p["jumlah"])
						else:
							for p in data_tidak_sama:
								insert_produk(p, p["jumlah"])
						conn.commit()
						QMB.information(None, tr("Berhasil"), tr("Data produk telah diperbarui"))
								
					def set_button():
						clear_widgets(tengah)
						list_btn = [
							("Semua", impor_semua),
							("Per kategori", impor_perkategori),
							("Per produk", impor_perproduk)
						]
						for a, b in list_btn:
							btn = button(tr(a), font_size_normal, "transparent")
							btn.clicked.connect(b)
							tengah_layout.addWidget(btn)
					
					def impor_semua():
						if not data:
							QMB.warning(None, tr("Gagal"), tr("Data kosong. Impor data dibatalkan"))
							return
						if askyesno(tr("Konfirmasi"), tr("Anda akan memindahkan seluruh produk dari server ke database lokal. Data lama akan dihapus")):
							list_impor = []
							for x in data:
								list_impor.append((x["id_produk"], x["barcode"], x["nama"], x["kategori"], x["catatan"], x["kadaluarsa"], x["satuan_beli"], x["satuan_jual"], x["isi_satuan"], x["supplier"], x["harga_beli"], x["harga_modal"], x["harga_jual"], x["jumlah"], x["jumlah_tertinggi"], x["stok_minimum"], x["poin"]))
							cursor.execute("DELETE FROM produk")
							cursor.executemany("INSERT INTO produk (id_produk, barcode, nama, kategori, catatan, kadaluarsa, satuan_beli, satuan_jual, isi_satuan, supplier, harga_beli, harga_modal, harga_jual, jumlah, jumlah_tertinggi, stok_minimum, poin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", list_impor)
							conn.commit()
							QMB.information(None, tr("Berhasil"), tr("Data telah berhasil dipindahkan ke database lokal"))
					
					def impor_perkategori():
						data_kategori = list({p["kategori"] for p in data})
						clear_widgets(bawah)
						frame = QFrame()
						frame.setStyleSheet(style_frame_putih("transparent"))
						frame_layout = QGridLayout(frame)
						cek_all = checkbutton(tr("Pilih semua"), font_size_normal)
						btn_impor = button(tr("Impor"), font_size_normal, bg)
						for x in [frame, cek_all, btn_impor]:
							bawah_layout.addWidget(x)
						list_kategori, dict_kategori = [], {}
						for i, p in enumerate(data_kategori):
							baris = i // 3
							kolom = i % 3
							cek = checkbutton(p, font_size_normal)
							dict_kategori[p] = cek
							list_kategori.append(cek)
							frame_layout.addWidget(cek, baris, kolom)
						
						def cek_semua():
							if cek_all.isChecked():
								for p in list_kategori:
									p.setChecked(True)
							else:
								for p in list_kategori:
									p.setChecked(False)
									
						def impor_now():
							terpilih = [kategori for kategori, cek in dict_kategori.items() if cek.isChecked()]
							data_impor = [p for p in data if p["kategori"] in terpilih]
						
							cursor.execute("SELECT * FROM produk")
							produk = cursor.fetchall()
							data_sama = []
							data_tidak_sama = []
							for d in data_impor:
								id_produk = d["id_produk"]
								for p in produk:
									if p["id_produk"] == id_produk:
										data_sama.append(d)
										break
								else:
									data_tidak_sama.append(d)
							if data_sama:
								clear_widgets(bawah)
								label = QLabel(f"Terdapat {len(data_sama)} data produk yang sudah ada dalam database lokal")
								frame_tombol = QFrame()
								tombol_layout = QHBoxLayout(frame_tombol)
								btn_overwrite = button(tr("Timpa produk lama"), font_size_normal, bg)
								btn_merge = button(tr("Gabungkan stok"), font_size_normal, bg)
								btn_skip = button(tr("Lewati"), font_size_normal, bg)
								list_command = ["overwrite", "merge", "skip"]
								for i, x in enumerate([btn_overwrite, btn_merge, btn_skip]):
									x.clicked.connect(lambda checked=False, x=list_command[i]: execute_data(x, data_sama, data_tidak_sama))
									tombol_layout.addWidget(x)
								for x in [label, frame_tombol]:
									bawah_layout.addWidget(x)
							else:
								for p in data_tidak_sama:
									insert_produk(p, p["jumlah"])
								conn.commit()
								QMB.information(None, tr("Berhasil"), tr("Data produk berhasil diperbarui"))
								
						cek_all.toggled.connect(cek_semua)
						btn_impor.clicked.connect(impor_now)
					
					def impor_perproduk():
						data_produk = list({p["nama"] for p in data})
						clear_widgets(bawah)
						fr = QFrame()
						fr.setStyleSheet(style_frame_putih("transparent"))
						fr_layout = QGridLayout(fr)
						btn_impor = button(tr("Impor"), font_size_normal, bg)
						pilih = checkbutton(tr("Pilih semua"), font_size_normal)
						for x in [fr, pilih, btn_impor]:
							bawah_layout.addWidget(x)
						dict_cek = {}
						list_cek = []
						for i, p in enumerate(data_produk):
							baris = i // 3
							kolom = i % 3
							cek = checkbutton(p, font_size_normal)
							dict_cek[p] = cek
							list_cek.append(cek)
							fr_layout.addWidget(cek, baris, kolom)
						
						def pilih_semua():
							if pilih.isChecked():
								for x in list_cek:
									x.setChecked(True)
							else:
								for x in list_cek:
									x.setChecked(False)
						
						def impor_now():
							terpilih = [nama for nama, v in dict_cek.items() if v.isChecked()]
							if not terpilih:
								QMB.warning(None, tr("Gagal"), tr("Pilih setidaknya satu data"))
								return
							data_impor = [p for p in data if p["nama"] in terpilih]
							cursor.execute("SELECT * FROM produk")
							produk = cursor.fetchall()
							data_sama, data_tidak_sama = [], []
							for p in data_impor:
								id_produk = p["id_produk"]
								for q in produk:
									if q["id_produk"] == id_produk:
										data_sama.append(p)
										break
								else:
									data_tidak_sama.append(p)
							
							if data_sama:
								clear_widgets(bawah)
								label = QLabel(f"Terdapat {len(data_sama)} data produk yang sudah ada dalam database lokal")
								frame_tombol = QFrame()
								tombol_layout = QHBoxLayout(frame_tombol)
								btn_overwrite = button(tr("Timpa produk lama"), font_size_normal, bg)
								btn_merge = button(tr("Gabungkan stok"), font_size_normal, bg)
								btn_skip = button(tr("Lewati"), font_size_normal, bg)
								list_command = ["overwrite", "merge", "skip"]
								for i, x in enumerate([btn_overwrite, btn_merge, btn_skip]):
									x.clicked.connect(lambda checked=False, x=list_command[i]: execute_data(x, data_sama, data_tidak_sama))
									tombol_layout.addWidget(x)
								for x in [label, frame_tombol]:
									bawah_layout.addWidget(x)
							else:
								for p in data_tidak_sama:
									insert_produk(p, p["jumlah"])
								conn.commit()
								QMB.information(None, tr("Berhasil"), tr("Data produk berhasil diperbarui"))
								
								
						pilih.toggled.connect(pilih_semua)
						btn_impor.clicked.connect(impor_now)
										
					set_button()
							
				atas_layout, tengah, bawah = set_layout()
				tengah_layout, bawah_layout = QHBoxLayout(tengah), QVBoxLayout(bawah)
				
				set_atas_layout()
				
			def menu_hapus():
				if not va("hapus produk lanjutan"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
				def tampilkan_data(data):
					clear_widgets(frame)
					fr = QFrame()
					fr.setStyleSheet(style_frame_putih("transparent"))
					llayout = QGridLayout(fr)
					sa = checkbutton(tr("Pilih semua"), font_size_normal)
					btn = button(tr("Hapus"), font_size_normal, bg)
					list_cek, dict_cek = [], {}
					for i, p in enumerate(data):
						baris, kolom = i // 3, i % 3
						cek = checkbutton(p, font_size_normal)
						list_cek.append(cek)
						dict_cek[p] = cek
						llayout.addWidget(cek, baris, kolom)
					for x in [fr, sa, btn]:
						layout.addWidget(x)
					return list_cek, dict_cek, sa, btn
					
				def select(cek, data):
					if cek.isChecked():
						for p in data:
							p.setChecked(True)
					else:
						for p in data:
							p.setChecked(False)
							
				def eksekusi(data):
					if askyesno(tr("Konfirmasi"), f"{tr('Terdapat')} {len(data)} {tr('data produk terpilih. Hapus sekarang?')}"):
						if koneksi["connect"] == 1:
							upload_data("hapus_data_produk", [dict(row) for row in data], tr("Data produk terpilih telah dihapus"))
						else:
							for p in data:
								id_produk = p["id_produk"]
								cursor.execute("DELETE FROM produk WHERE id_produk = ?", (id_produk, ))
							conn.commit()
							QMB.information(None, tr("Berhasil"), tr("Data produk terpilih telah dihapus"))
							
				def set_layout():
					atas, bawah = QFrame(), QFrame()
					clear_widgets(right)
					list_button = [
						("Hapus per kategori", hapus_per_kategori),
						("Hapus per produk", hapus_per_produk),
						("Hapus produk kosong", hapus_produk_kosong),
						("Hapus semua", hapus_semua_produk)
					]
					al = QHBoxLayout(atas)
					for a, b in list_button:
						btn = button(tr(a), font_size_normal, bg)
						btn.clicked.connect(b)
						al.addWidget(btn)
					for x in [atas, bawah]:
						right_layout.addWidget(x)
					return bawah
				
				def hapus_per_kategori():
					list_cek, dict_cek, sa, btn = tampilkan_data(list({p["kategori"] for p in produk_data}))					
					def hapus():
						terpilih = [kategori for kategori, v in dict_cek.items() if v.isChecked()]
						list_hapus = [p for p in produk_data if p["kategori"] in terpilih]
						eksekusi(list_hapus)
						hapus_per_kategori()

					sa.toggled.connect(lambda: select(sa, list_cek))
					btn.clicked.connect(hapus)
					
				def hapus_per_produk():
					list_cek, dict_cek, sa, btn = tampilkan_data(list({f"{p['id_produk']} - {p['nama']}" for p in produk_data}))					
					def hapus():
						terpilih = [namaxid for namaxid, v in dict_cek.items() if v.isChecked()]
						list_id_produk = []
						for p in terpilih:
							teks = p.replace(" ", "").split("-")
							list_id_produk.append(teks[0])
						list_hapus = [p for p in produk_data if p["id_produk"] in list_id_produk]
						eksekusi(list_hapus)
						hapus_per_produk()
									
					sa.toggled.connect(lambda: select(sa, list_cek))
					btn.clicked.connect(hapus)
					
				def hapus_produk_kosong():
					list_cek, dict_cek, sa, btn = tampilkan_data(list({f"{p['id_produk']} - {p['nama']} - {format_unit(p['jumlah'], p['satuan_jual'])}" for p in produk_data if p["jumlah"] <= 0}))
					def hapus():
						terpilih = [teks for teks, v in dict_cek.items() if v.isChecked()]
						list_id_produk = []
						for p in terpilih:
							teks = p.replace(" ", "").split("-")
							list_id_produk.append(teks[0])
						list_hapus = [p for p in produk_data if p["id_produk"] in list_id_produk]
						eksekusi(list_hapus)
						hapus_produk_kosong()
		
					sa.toggled.connect(lambda: select(sa, list_cek))
					btn.clicked.connect(hapus)
					
				def hapus_semua_produk():
					eksekusi(produk_data)
					
				frame = set_layout()
				layout = QVBoxLayout(frame)
						
			btn_margin = label_photo(tr("Pengaturan margin"), resource_path("Pictures/setting.png"), icon_size)
			btn_stok = label_photo(tr("Daftar stok"), resource_path("Pictures/daftar.png"), icon_size)
			btn_diskon = label_photo(tr("Daftar produk diskon"), resource_path("Pictures/daftar.png"), icon_size)
			btn_tingkat = label_photo(tr("Daftar produk bertingkat"), resource_path("Pictures/daftar.png"), icon_size)
			btn_ekspor = label_photo(tr("Ekspor/impor produk"), resource_path("Pictures/export.png"), icon_size)
			btn_hapus = label_photo(tr("Hapus produk"), resource_path("Pictures/hehehe.png"), icon_size)
		
			for i, x in enumerate([btn_margin, btn_stok, btn_diskon, btn_tingkat, btn_ekspor, btn_hapus]):
				x.setStyleSheet(style_button("transparent", font_size_normal))
				left_layout.addWidget(x, alignment=Qt.AlignmentFlag.AlignLeft)
			btn_margin.clicked.connect(pengaturan_margin)
			btn_stok.clicked.connect(daftar_stok)
			btn_diskon.clicked.connect(daftar_produk_diskon)
			btn_tingkat.clicked.connect(daftar_tingkat)
			btn_ekspor.clicked.connect(lambda: safe_run(ekspor_impor))
			btn_hapus.clicked.connect(menu_hapus)
		
		def informasi_produk():
			if not va("info produk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			def get_data():
				riwayat = getData("riwayat_penjualan_campuran")
				max_jumlah = max(p["jumlah"] for p in produk_data)
				min_jumlah = min(p["jumlah"] for p in produk_data)
				riwayat_data = []
				for p in riwayat:
					riwayat_data.extend(json.loads(p["data_belanja"]))
					
				nama = [a["nama"] for a in riwayat_data]
				non_ada = [p["nama"] for p in produk_data if p["nama"] not in nama]
				return {
				    "Jumlah_seluruh_produk": format_unit(len(produk_data), "Unit"),
				    "Produk_stok_habis": format_unit(sum(1 for p in produk_data if p["jumlah"] <= 0), "Unit"),
				    "Produk_hampir_habis": format_unit(sum(1 for p in produk_data if 0 < p["jumlah"] <= p["stok_minimum"]), "Unit"),
				    "Produk_stok_cukup": format_unit(sum(1 for p in produk_data if p["jumlah"] >= p["stok_minimum"]), "Unit"),
				    "Total_modal_tersisa": pretty_money(sum(p["harga_modal"] * p["jumlah"] for p in produk_data)),
				    "Total_penjualan_tersisa": pretty_money(sum(p["harga_jual"] * p["jumlah"] for p in produk_data)),
				    "Total_jumlah_stok_tersisa": format_unit(sum(p['jumlah'] for p in produk_data), "Unit"),
				    "Total_perkiraan_keuntungan_tersisa": pretty_money(sum(p["harga_jual"] * p["jumlah"] for p in produk_data) - sum(p["harga_modal"] * p["jumlah"] for p in produk_data)),
				    "Produk_stok_terbanyak": format_unit(max_jumlah, "Unit") + " " + "-" + " " + ", ".join([p["nama"] for p in produk_data if p["jumlah"] == max_jumlah]),
				    "Produk_stok_paling_sedikit": format_unit(min_jumlah, "Unit") + " " + "-" + " " + ", ".join([p["nama"] for p in produk_data if p["jumlah"] == min_jumlah]),
				    "Rata_rata_jumlah_produk": format_unit(sum(p["jumlah"] for p in produk_data) // len(produk_data), "Unit"),
				    "Rata_rata_modal_produk": pretty_money(sum(p["harga_modal"] for p in produk_data) / len(produk_data)),
				    "Rata_rata_harga_jual_produk": pretty_money(sum(p["harga_jual"] for p in produk_data) / len(produk_data)),
				    "Rata_rata_potensi_keuntungan_per-produk": pretty_money((sum(p["harga_jual"] for p in produk_data) - sum(p["harga_modal"] for p in produk_data)) / len(produk_data)),
				    "Produk_terlaris": max(set(nama), key=nama.count) + " " + "terjual sebanyak" + " " + str(nama.count(max(set(nama), key=nama.count))) + " " + "kali",
				    "Produk_paling_lambat_terjual": min(set(nama), key=nama.count) + " " + "terjual sebanyak" + " " + str(nama.count(min(set(nama), key=nama.count))) + " " + "kali",
				    "Produk_belum_pernah_terjual": "\n• ".join(non_ada)
				}
			
			def set_layout():
				clear_widgets(f3)
				frame = QFrame()
				label = QLabel(tr("INFORMASI SEKILAS DATA PRODUK"))
				for p in [label, frame]:
					f3_layout.addWidget(p, alignment=rata_atas)
				return QGridLayout(frame)
			
			def set_data():
				data = get_data()
				for i, (a, b) in enumerate(data.items()):
					info = a.replace("_", " ").upper()
					value = b
					lbl1, lbl2, lbl3 = QLabel(info), QLabel(":"), QLabel(value)
					for c in [lbl1, lbl2]:
						c.setStyleSheet(style_label_bold(font_size_normal))
					lbl3.setStyleSheet(f"""
						QLabel {{
							font-size: {font_size_normal}px;
						}}
					""")
					layout.addWidget(lbl1, i, 0, alignment=rata_atas)
					layout.addWidget(lbl2, i, 1, alignment=rata_atas)
					layout.addWidget(lbl3, i, 2, alignment=rata_kiri)
					
			layout = set_layout()
			set_data()
		
		def katalog_produk():
			if not va("katalog produk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			def get_picture():
				try:
					res = requests.get(f"{SERVER_URL}/ambil_gambar_katalog")
					if res.status_code == 200:
						return BytesIO(res.content)
					else:
						return None
				except Exception:
					return None
			
			def set_layout():
				clear_widgets(f3)
				frame = QFrame()
				label = QLabel(tr("KATALOG PRODUK"))
				label.setAlignment(Qt.AlignCenter)
				label.setStyleSheet(style_label_bold(font_size_judul))
				for x in [label, frame]:
					f3_layout.addWidget(x)
				return QGridLayout(frame)
			
			def set_katalog():
				zip = get_picture()
				if zip:
					with zipfile.ZipFile(zip, "r") as z:
						daftar_foto = z.namelist()
						for i, nama_file in enumerate(daftar_foto):
							baris, kolom = i // 3, i % 3
							data_gambar = z.read(nama_file)
							pix = QPixmap()
							pix.loadFromData(data_gambar)
							pix = pix.scaled(200,200,Qt.KeepAspectRatio,Qt.SmoothTransformation)
							frame = QFrame()
							layout_frame = QVBoxLayout(frame)
							lbl_gambar = QLabel()
							lbl_gambar.setPixmap(pix)
							lbl_gambar.setAlignment(Qt.AlignCenter)
							lbl_nama = QLabel(nama_file)
							lbl_nama.setStyleSheet(style_label_bold(font_size_normal))
							lbl_nama.setAlignment(Qt.AlignCenter)
							for x in [lbl_gambar, lbl_nama]:
								layout_frame.addWidget(x)
							layout.addWidget(frame, baris, kolom)							
			layout = set_layout()
			set_katalog()
		
		def data_kadaluarsa():
			if not va("info kadaluarsa"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			def set_layout():
				clear_widgets(f3)
				lbl_judul.setText(tr("LAPORAN DATA PRODUK KADALUARSA"))
				tabel, model = table_maker(["ID PRODUK", "NAMA", "KADALUARSA DALAM", "TANGGAL KADALUARSA"])
				f3_layout.addWidget(tabel)
				return tabel, model
				
			def get_data():
				for p in produk_data:
					try:
						exp = p["kadaluarsa"]
						time_expired = time_exp(exp)
						waktu_asli = datetime.strptime(exp, "%m/%d/%y").strftime("%A, %d %B %Y")
						model.appendRow([
							QStandardItem(p["id_produk"]),
							QStandardItem(p["nama"]),
							QStandardItem(time_expired),
							QStandardItem(waktu_asli)
						])
					except Exception:
						continue
				
			tabel, model = set_layout()
			get_data()
					
		btn_menu.clicked.connect(menu_lain)
		btn_info.clicked.connect(informasi_produk)
		btn_katalog.clicked.connect(katalog_produk)
		btn_exp.clicked.connect(lambda: safe_run(data_kadaluarsa))
		
		frame_atas_layout.addWidget(tabel)
		for x in [btn_menu, btn_info, btn_katalog, btn_exp]:
			fr_vawah_layout.addWidget(x)
		for x in [btn_kembali, btn_refresh, btn_produk_baru]:
			x.setStyleSheet(f2_btn(font_size_normal))
			f2_layout.addWidget(x, alignment=Qt.AlignmentFlag.AlignLeft)
		for x in [btn_detail, btn_tambah, btn_edit, btn_hapus, btn_tingkat]:
			x.setStyleSheet(style_button("transparent", font_size_normal))
			frame_bawah_layout.addWidget(x, alignment=Qt.AlignmentFlag.AlignLeft)
		for x in [frame_atas, frame_bawah]:
			f3_layout.addWidget(x)
		f2_layout.addWidget(frame_cari)
		for x in [entry_cari_produk, fr_vawah]:
			frame_cari_layout.addWidget(x)
		entry_cari_produk.setFocus()
		entry_cari_produk.textChanged.connect(lambda: tampilkan_produk(entry_cari_produk.text().strip()))
		QTimer.singleShot(0, tampilkan_produk)
		spinner.deleteLater()
		
		def produk_tingkat():
			if not va("multi price produk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			fm = format_uang_app
			data = take_data()
			if not data:
				QMB.critical(None, tr("Tidak ada data"), tr("Silahkan pilih data dari tabel terlebih dahulu"))
				return
			id = data[0]
			barcode = data[1]
			nama = data[2]
			hm = next((p["harga_modal"] for p in produk_data if p["id_produk"] == id), None)
			hj = next((p["harga_jual"] for p in produk_data if p["id_produk"] == id), None)
			list_path = ["Tingkat A", "Tingkat B"]
			str_path = combobox(font_size_normal, list_path)
			min_beli = entry(tr("Minimum pembelian produk"), font_size_normal)
			harga_jual = entry(tr("Harga jual tingkat"), font_size_normal)
			btn_save = button(tr("Simpan"), font_size_normal, bg)
			label_harga = QLabel()
			label_harga.setStyleSheet("""
				QLabel {
					background-color: transparent;
					font-size: {font_size_normal}px;
					color: green;
					font-weight: bold;
					padding: 10px;
					border: 1px solid black;
					border-radius: 2px;
				}
			""")
			def hitung_kembalian(x):
				try:
					beli = int(x.text().strip())
				except ValueError:
					return
				hehe = beli * hj
				label_harga.setText(f"HARGA JUAL ASLI = {pretty_money(hehe)}\n\nPertimbangkan harga jual dengan bijak...")
			
			def simpan():
				path = str_path.currentText()
				try:
					hj = float(harga_jual.text().strip().replace(format_uang_app[0], "").replace(format_uang_app[2], "").replace(format_uang_app[3], "."))
					mbb = int(min_beli.text().strip())
				except ValueError as e:
					QMB.warning(None, tr("Gagal"), tr("Masukkan angka dengan benar"))
					return
				save_in = path.lower().replace(" ", "_")
				harga_modal = hm * mbb
				if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
					if koneksi["connect"] == 1:
						data = {
							"id_produk": id,
							"barcode": barcode,
							"nama": nama,
							"harga_modal": harga_modal,
							"harga_jual": hj,
							"min_beli": mbb,
							"path": save_in
						}
						upload_data("tambah_tingkat_produk", data, f"Produk {id}-{nama}-{barcode} telah ditambahkan ke {path}")
					else:
						cursor.execute(f"SELECT * FROM {save_in} WHERE id_produk = ?", (id, ))
						pr = cursor.fetchone()
						if not pr:
							cursor.execute(f"INSERT INTO {save_in} (id_produk, barcode, nama, harga_modal, harga_jual, min_beli) VALUES (?, ?, ?, ?, ?, ?)", (id, barcode, nama, harga_modal, hj, mbb))
						else:
							QMB.warning(None, tr("Ditolak"), f"Produk {id} {nama} {barcode} sudah ada dalam {save_in}")
							return
						conn.commit()
						QMB.information(None, tr("Berhasil"), f"Produk {id}-{nama}-{barcode} telah ditambahkan ke {save_in}")
						
			harga_jual.textChanged.connect(lambda: format_rupiah(harga_jual))
			min_beli.textChanged.connect(lambda: hitung_kembalian(min_beli))
			btn_save.clicked.connect(simpan)
			
			clear_widgets(frame_atas)
			fr = QFrame()
			fr_layout = QHBoxLayout(fr)
			fr_layout.setContentsMargins(3,3,3,3)
			fr_layout.setSpacing(3)
			left, right = QFrame(), QFrame()
			left_layout, right_layout = QVBoxLayout(left), QVBoxLayout(right)
			for i, x in enumerate([str_path, min_beli, harga_jual, btn_save, label_harga]):
				left_layout.addWidget(x) if i == 4 else right_layout.addWidget(x)
				
			for x in [left, right]:
				x.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
				x.setStyleSheet(style_frame(bg))
				fr_layout.addWidget(x)
			frame_atas_layout.addWidget(fr)
						
		btn_detail.clicked.connect(detail_produk)
		btn_tambah.clicked.connect(tambah_stok)
		btn_edit.clicked.connect(edit_produk)
		btn_hapus.clicked.connect(hapus_produk)
		btn_tingkat.clicked.connect(produk_tingkat)
		model.itemChanged.connect(simpan_stok)
	
	def daftar_pengguna():
		if not va("pengguna"):
			QMB.critical(None, "", tr("Anda tidak diizinkan"))
			return
		
		def make_main_frame():
			clear_widgets(f3)
			fr_atas, atas = frame(QHBoxLayout, bg="transparent")
			fr_tengah, tengah = frame(QGridLayout, bg="transparent")
			scrolled_fr = give_scroll(fr_tengah, scrollH=False)
			scrolled_fr.setMinimumHeight(350)
			fr_midle, midle = frame(QHBoxLayout, bg="transparent", rata=rata_kiri)
			fr_bawah, bawah = frame(QHBoxLayout, bg="transparent")
			
			for p in [fr_atas, scrolled_fr, fr_midle, fr_bawah]:
				f3_layout.addWidget(p)
				munculkan(p)
			return atas, tengah, bawah, fr_tengah, fr_bawah, fr_midle, midle
		
		def set_atas():
			kiri, layout_kiri = frame(QGridLayout, bg="rgba(0,100,120,0.06)", margin=3, padding=5)
			tengah, tengah_layout = frame(QVBoxLayout, bg="rgba(0,100,120,0.06)", margin=3, padding=5)
			kanan, kanan_layout = frame(QVBoxLayout, bg="rgba(0,100,120,0.06)", margin=3, padding=5)
			
			cursor.execute("SELECT nama, status, inisial_code FROM operator")
			opr = cursor.fetchone()
			info = [
				("Nama", opr["nama"] if opr else ""),
				("Status", opr["status"] if opr else ""),
				("Inisial Code", opr["inisial_code"] if opr else "")
			]
			judul_operator = label(tr("OPERATOR SAAT INI"), color="green", font_weight=600, font_size=font_size_judul)
			layout_kiri.addWidget(judul_operator, 0, 0, 1, 3)
			for i, (a, b) in enumerate(info, start=1):
				al, l, bl = label(tr(a)), label(":"), label(b)
				layout_kiri.addWidget(al, i, 0)
				layout_kiri.addWidget(l, i, 1)
				layout_kiri.addWidget(bl, i, 2)
			
			cursor.execute("SELECT id_device FROM device")
			id = cursor.fetchone()
			
			def ubah_id():
				if not id:
					pass
				else:
					QMB.warning(None, tr("Gagal"), tr("Komputer ini sudah memiliki id"))
					return
				c = random.choice(["XyZ", "A2Cx", "HjW", "LmA7", "MmV"])
				t = datetime.now().strftime("%f")
				id_now = f"{c}_{t}"
				cursor.execute("INSERT INTO device (id_device) VALUES (?)", (id_now, ))
				conn.commit()
				QMB.information(None, tr("Berhasil"), f"{tr('Komputer ini didaftarkan pada')} {c}_{t}")
				daftar_pengguna()
				
			if not id:
				lbl_id = red_label(tr("Perangkat ini belum memiliki id"))
			else:
				lbl_id = label(f"{tr('ID PERANGKAT')}: {id['id_device']}", font_size=font_size_judul, color="green", font_weight=800, padding=5, border="1px solid black", border_radius=2)
			
			btn_ubah = label_photo(tr("Ganti"), resource_path("Pictures/pengaturan_lainnya.png"), icon_size)
			btn_ubah.setStyleSheet(style_button(bg, font_size_normal))
			btn_ubah.clicked.connect(ubah_id)
			
			validasi_owner = checkbutton(tr("Validasi pemilik"), font_size_normal)
			validasi_owner.setChecked(next((p["status"] for p in stts), 0))
			validasi_owner.toggled.connect(aktifkan_validasi_owner)
			
			cari_pengguna = entry(tr("Masukkan nama atau inisial code pengguna"), font_size_normal)
			
			for p in [lbl_id, btn_ubah]:
				tengah_layout.addWidget(p)
				
			for p in [validasi_owner, cari_pengguna]:
				kanan_layout.addWidget(p)
				
			for p in [kiri, tengah, kanan]:
				atas.addWidget(p)
			return validasi_owner, cari_pengguna
			
		def set_tengah(teks=""):
			clear_widgets(fr_tengah)
			if not user:
				tengah.addWidget(red_label(tr("Pengguna tidak tersedia")))
				return
			for i, p in enumerate(user):
				if teks.lower() in p["nama"].lower() or teks.lower() in p["inisial_code"].lower() or teks.lower() in p["status"].lower():
					fr, layout = frame(QVBoxLayout, bg="rgba(0,100,120,0.06)", margin=3, padding=5)
					nama = QPushButton(p["nama"].upper())
					nama.setStyleSheet(f"""
						QPushButton {{
							font-size: {font_size_judul}px;
							background-color: transparent;
							padding: 7px;
							border: 1px solid {bg};
							border-radius: 2px;
							font-weight: 700;
						}}
						QPushButton:hover {{
							color: darkgreen;
							border: 2px solid darkgreen;
							font-size: {font_size_judul+1}px;
						}}""")
					nama.clicked.connect(lambda *args, id=p["inisial_code"]: safe_run(release_qr, id))
					status = label(tr("Status") + ": " + p["status"])
					id_code = label("ID: " + p["inisial_code"])
					
					frm, lay = frame(QHBoxLayout, border="1px solid green")
					buttons = [
						("Edit", edit_data_user),
						("Hapus", hapus_pengguna),
						("Jadikan operator", jadikan_operator),
						("Lupa kata sandi", lupa_kata_sandi)
					]
					for btn, command in buttons:
						bt = button(tr(btn), font_size_normal, bg)
						bt.clicked.connect(lambda *args, id=p["inisial_code"], cm=command: safe_run(cm, id))
						lay.addWidget(bt)
						
					for a in [nama, status, id_code, frm]:
						layout.addWidget(a, alignment=rata_atas)
					tengah.addWidget(fr, i//2, i%2, alignment=rata_atas)
		
		def set_bawah():
			kiri, frk = frame(QVBoxLayout, bg="transparent")
			kanan, frn = frame(QVBoxLayout, bg="transparent")
			for p in [kiri, kanan]:
				bawah.addWidget(p)
			return frk, frn, kiri, kanan
			
		def set_midle():
			btn = [
				("Tambah pengguna", tambah_pengguna),
				("Lihat riwayat", lihat_riwayat),
				("Atur shift", pengaturan_shift)
			]
			for teks, command in btn:
				bt = button(tr(teks), font_size_normal, bg)
				bt.clicked.connect(lambda *args, cm=command: safe_run(cm))
				midle.addWidget(bt, alignment=rata_kiri)
		
		"""----Brain Function----"""
		
		def tambah_pengguna():
			clear_widgets(fr_kiri)
			list_entry = [
				("status", "Masukkan status baru"),
				("nama", "Masukkan nama"),
				("password", "Masukkan password"),
				("konfirmasi password", "Masukkan konfirmasi password"),
				("pertanyaan keamanan", "Masukkan pertanyaan keamanan"),
				("jawaban", "Masukkan jawaban")
			]
			cmb = combobox(font_size_normal, ["Owner", "Admin", "Kasir"])
			kiri.addWidget(cmb)
			entries = entry_maker(kiri, list_entry)
			konf = red_label("")
			btn_save = label_photo(tr("Simpan"), resource_path("Pictures/ddd.png"), icon_size)
			btn_save.setStyleSheet(style_button(bg, font_size_normal))
			
			def simpan_user():
				if not va("tambah pengguna baru"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
					
				d = {key: value.text().strip() for key, value in entries.items()}
				n = d.get("nama", "")
				s = d.get("status", "") if d.get("status", "") != "" else cmb.currentText()
				p = d.get("password", "")
				kp = d.get("konfirmasi password", "")
				q = d.get("pertanyaan keamanan", "")
				a = d.get("jawaban", "")
				if not user:
					if s.lower() != "owner":
						QMB.warning(None, tr("Gagal"), tr("Pendaftaran user pertama kali harus berstatus OWNER!"))
						return					
				if not all([n, s, p, kp]):
					konf.setText(tr("Beberapa data harus diisi!"))
					return
				if p != kp:
					konf.setText(tr("Password dan konfirmasi password tidak sama!"))
					return
					
				nama_bagi = n.split()
				name = n[0].split()
				inisial = name[0]
				inisial_code = f"{inisial}{datetime.now().strftime('%f')}"
				same = False
				for u in user:
					if u["nama"].lower() == n.lower():
						konf.setText(tr("User telah terdaftar"))
						same = True
						break
				if not same:
					pengguna = {
						"nama": n,
						"status": s,
						"inisial": inisial,
						"inisial_code": inisial_code,
						"password": pks.hash(p),
						"pertanyaan": q,
						"jawaban": pks.hash(a),
						"operator": nama_operator(),
						"sumber": komputer(),
						"pw": p
					}
					if koneksi["connect"] == 1:
						try:
							res = requests.post(f"{SERVER_URL}/tambah_user", json=pengguna)
							if res.status_code == 200:
								QMB.information(None, tr("Berhasil"), f"{tr('Pengguna baru')} {n} {tr('telah ditambahkan')}")
								pratinjau_qr(n, s, inisial_code)
							else:
								QMB.warning(None, tr("Gagal"), f"{tr('Terdapat masalah penambahan pengguna. Kode respon:')} {res.status_code}")
								return
						except Exception as e:
							QMB.critical(None, "Error", str(e))
							return
					else:
						cursor.execute("INSERT INTO user (nama, status, inisial, inisial_code, password, pertanyaan, jawaban) VALUES (?, ?, ?, ?, ?, ?, ?)", (n, s, inisial, inisial_code, pks.hash(p), q, pks.hash(a)))
						cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Tambah pengguna", n, 1, inisial_code, nama_operator(), komputer()))
						conn.commit()
						
						def choose_color():
							return random.choice(["darkblue", "black", "darkred", "purple"])
							
						teks = f"{inisial_code} {p}"
						img = qr_maker(teks, fill=choose_color())
						path = os.path.join(folder_foto_profil, f"{n} {inisial_code}.jpeg")
						img.save(path, "jpeg", quality=90, optimize=True)
						QMB.information(None, tr("Berhasil"), f"{tr('Pengguna baru')} {n} {tr('telah ditambahkan')}!")
						pratinjau_qr(n, s, inisial_code)			
			
			btn_save.clicked.connect(simpan_user)
			for p in [konf, btn_save]:
				kiri.addWidget(p)
			
		def lihat_riwayat():
			print()
		
		def hapus_pengguna(id):
			if not validasi_pemilik():
				return
			d = next((p for p in user if p["inisial_code"] == id), None)
			if askyesno(tr("Konfirmasi"), f"{tr('Hapus')} {d['nama']} {tr('sekarang')}?"):			
				if koneksi["connect"] == 1:
					upload_data("hapus_user", {"id": d["inisial_code"]}, f"{tr('Hapus user')} {d['nama']} {tr('berhasil')}")
				else:
					cursor.execute("DELETE FROM user WHERE inisial_code = ?", (d["inisial_code"], ))
					conn.commit()
					QMB.information(None, tr("Berhasil"), f"{d['nama']} {tr('telah dihapus')}")
				daftar_pengguna()
		
		def jadikan_operator(id):
			if not validasi_pemilik():
				return
			d = next((p for p in user if p["inisial_code"] == id), None)
			cursor.execute("DELETE FROM operator")		
			cursor.execute("INSERT INTO operator (nama, status, inisial_code) VALUES (?, ?, ?)", (d["nama"], d["status"], d["inisial_code"]))
			if koneksi["connect"] == 1:
				data = {
					"pengenal": d["inisial_code"],
					"waktu": now_str(),
					"device": komputer(),
					"tipe_login": "Lewat perantara owner",
					"poin_kesalahan": 0
				}
				upload_data("tambah_riwayat_login", data, f"{tr('Selamat datang kembali')} {d['nama']}")
			else:
				cursor.execute("INSERT INTO riwayat_login (id_pengenal, nama, inisial_code, waktu, device, login_menggunakan, kesalahan_login) VALUES (?, ?, ?, ?, ?, ?, ?)", (d["inisial_code"], d["nama"], d["inisial_code"], now_str(), komputer(), "Lewat perantara owner", 0))		
			conn.commit()
			QMB.information(None, tr("Berhasil"), f"{d['nama']} {tr('telah ditetapkan menjadi operator')}")
			daftar_pengguna()
						
		def lupa_kata_sandi(id):
			if not validasi_pemilik():
				return
			if askyesno(tr("Konfirmasi"), tr("Pergantian kata sandi wajib dilakukan owner!")):
				pw, yes = input_string(tr("Kata sandi"), tr("Masukkan kata sandi owner"))
				if yes:
					if not pw:
						return
					owner = any(p["status"].lower() == "owner" for p in user)
					if owner:
						for p in user:
							if pks.verify(pw, p["password"]):
								if p["status"].lower() == "owner":
									break
								else:
									QMB.warning(None, tr("Gagal"), tr("Anda tidak diizinkan"))
									return
						else:
							QMB.warning(None, tr("Gagal"), tr("Password salah"))
							return
					else:
						pass
					clear_widgets(fr_kiri)
					
					lbl_judul.setText(tr("Pergantian kata sandi"))
					list_ent = [
						("kata sandi baru", "Kata sandi baru..."),
						("konfirmasi kata sandi baru", "Konfirmasi kata sandi baru...")
					]
					entries = entry_maker(kiri, list_ent)
			
					def simpan():
						data = next((p for p in user if p["inisial_code"].lower() == id.lower()), None)
						d = {key: value.text().strip() for key, value in entries.items()}
						p = d.get("kata sandi baru", "")
						k = d.get("konfirmasi kata sandi baru", "")
						if not all ([p, k]):
							kon.setText(tr("Entry wajib diisi"))
							return
						if p != k:
							kon.setText(tr("Kata sandi dan konfirmasi kata sandi harus sama"))
							return
							
						if koneksi["connect"] == 1:
							d = {
								"nama": data["nama"],
								"inisial_code": data["inisial_code"],
								"pass": p
							}
							upload_data("lupa_password", d, f"{data['nama']} {tr('telah memperbarui kata sandinya')}!")
						else:
							cursor.execute("UPDATE user SET password = ? WHERE inisial_code = ?", (pks.hash(p), data["inisial_code"]))
							teks = data["inisial_code"] + " " + p
							img = qr_maker(teks)
							path = os.path.join(folder_foto_profil, f"{data['nama']} {data['inisial_code']}.jpeg")
							img.save(path, "jpeg", quality=90, optimize=True)
							QMB.information(None, tr("Berhasil"), f"{data['nama']} {tr('telah memperbarui kata sandinya')}!")
						daftar_pengguna()
						
					kon = red_label("")
					btn_simpan = label_photo(tr("Simpan"), resource_path("Pictures/ddd.png"), icon_size)
					btn_simpan.setStyleSheet(style_button(bg, font_size_normal))
					for x in [kon, btn_simpan]:
						kiri.addWidget(x)
					btn_simpan.clicked.connect(simpan)
					
		def edit_data_user(id):
			if not validasi_pemilik():
				return
			clear_widgets(fr_kiri)
			list_entry = [
				("nama", "Masukkan nama baru..."),
				("status", "Masukkan status baru..."),
				("pertanyaan baru", "Masukkan pertanyaan baru..."),
				("jawaban", "Masukkan jawaban...")
			]
			entries = entry_maker(kiri, list_entry)
		
			kon = red_label("")
			btn_simpan = label_photo(tr("Simpan"), resource_path("Pictures/ddd.png"), icon_size)
			btn_simpan.setStyleSheet(style_button(bg, font_size_normal))
			
			def simpan():
				d = {key: value.text().strip() for key, value in entries.items()}
				n = d.get("nama", "")
				s = d.get("status", "")
				q = d.get("pertanyaan baru", "")
				a = d.get("jawaban", "")
				
				if not all([n, s]):
					kon.setText("Nama dan status harus diisi!")
					return
				if askyesno(tr("Konfirmasi"), tr("Apakah data sudah benar?")):
					if koneksi["connect"] == 1:
						data_upload = {
							"nama": n,
							"status": s,
							"pertanyaan": q,
							"jawaban": pks.hash(a),
							"inisial_code": id
						}
						upload_data("edit_user", data_upload, f"{tr('Data')} {d['nama']} {tr('telah diperbarui')}!")
						
					else:
						cursor.execute("UPDATE user SET nama = ?, status = ?, pertanyaan = ?, jawaban = ? WHERE inisial_code = ?", (n, s, q, pks.hash(a), id))
						conn.commit()
						QMB.information(None, tr("Berhasil"), f"{tr('Data')} {d['nama']} {tr('telah diperbarui')}")
					daftar_pengguna()
			
			kiri.addWidget(kon)
			kiri.addWidget(btn_simpan)
			btn_simpan.clicked.connect(simpan)
			
		def aktifkan_validasi_owner():
			password, yes = input_string(tr("Masukkan password"), tr("Masukkan password owner"))
			if yes:
				if not user:
					pass
				for p in user:
					if pks.verify(password, p["password"]):
						if p["status"].lower() == "owner":
							break
						else:
							QMB.warning(None, tr("Tidak diizinkan"), tr("Anda tidak diizinkan!"))
							return
				else:
					QMB.critical(None, tr("Gagal"), tr("Password salah"))
					return
				status = validasi_owner.isChecked()
				if koneksi["connect"] == 1:
					data = {
						"status": status
					}
					try:
						res = requests.post(f"{SERVER_URL}/aktifkan_validasi_owner", json=data)
						if res.status_code == 200:
							daftar_pengguna()
						else:
							QMB.critical(None, tr("Gagal"), tr("Gagal aktifkan validasi owner!"))
					except Exception as e:
						QMB.critical(None, "", str(e))
				else:
					cursor.execute("SELECT * FROM validasi_owner")
					val = cursor.fetchone()
					if val:
						cursor.execute("UPDATE validasi_owner SET status = ? WHERE id = ?", (status, 1))
					else:
						cursor.execute("INSERT INTO validasi_owner (status) VALUES (?)", (status, ))
					conn.commit()
					daftar_pengguna()
					
		def pratinjau_qr(nama, status, id):
			clear_widgets(fr_kanan)
			data = {
				"nama": nama,
				"id": id
			}
			lbl_qr = label(tr("Tidak ada gambar"))
			image = None
			
			def take_image():
				nonlocal image
				if koneksi["connect"] == 1:
					try:
						res = requests.get(f"{SERVER_URL}/ambil_gambar_qr", params=data)
						if res.status_code != 200:
							return
					except Exception:
						return
					image = res.content
				else:
					path = os.path.join(folder_foto_profil, f"{nama} {id}.jpeg")
					if not os.path.exists(path):
						return
					image = path
			
			take_image()
			show_pictures(image, lbl_qr, 300)

			info_opr = [
				("NAMA", nama.upper()),
				("STATUS", status.upper()),
				("INISIAL CODE", id.upper())
			]
			teks, teks_layout = frame(QGridLayout, bg="rgba(0,100,120,0.06)")
			for i, (x,y) in enumerate(info_opr):
				lbl1 = label(x, font_size=font_size_judul, font_weight=600)
				lbl2 = label(":", font_size=font_size_judul, font_weight=600)
				lbl3 = label(y, font_size=font_size_judul, font_weight=600)

				teks_layout.addWidget(lbl1, i, 0)
				teks_layout.addWidget(lbl2, i, 1)
				teks_layout.addWidget(lbl3, i, 2)
				
			btn_save = button(tr("Simpan sebagai pdf"), font_size_normal, bg)
				
			def save_pdf():
				profil = getData("profil")
				if not profil:
					QMB.warning(None, tr("Gagal"), tr("Sepertinya Anda belum membuat profil. Qr code user disimpan dalam database!"))
					return 
				if askyesno(tr("Konfirmasi"), f"{tr('Simpan PDF Card')} {nama}?"):
					file_name = f"{nama} {id}.pdf"
					path = choose_save_path_pdf(file_name)
					doc = SimpleDocTemplate(
						path,
						pagesize=(85.6*mm, 53.98*mm),
						leftMargin=3*mm,
						rightMargin=3*mm,
						topMargin=3*mm,
						bottomMargin=3*mm
					)
			
					content = []
			
					profil = getData("profil")
					pro = profil[0]
			
					style_title = ParagraphStyle(name="Title", alignment=1, fontSize=10, leading=12)
					style_small = ParagraphStyle(name="Small", alignment=1, fontSize=7, leading=9)
					style_user = ParagraphStyle(name="User", alignment=1, fontSize=9, leading=11)
					
					if isinstance(image, (bytes, bytearray)):
						img = BytesIO(image)
					else:
						with open(image, "rb") as f:
							img = BytesIO(f.read())
					pict = RLImage(img, width=25*mm, height=25*mm)
					pict.hAlign = "CENTER"
			
					data = [
						[Paragraph(pro["nama"], style_title)],
						[Paragraph(f"{pro['alamat']}, {pro['kontak']}", style_small)],
						[pict],
						[Paragraph(f"{nama} | {status}", style_user)]
					]
			
					table = Table(data, colWidths=[79.6*mm])
			
					table.setStyle(TableStyle([
						("ALIGN", (0,0), (-1,-1), "CENTER"),
						("VALIGN", (0,0), (-1,-1), "MIDDLE"),
						("TOPPADDING", (0,0), (-1,-1), 2),
						("BOTTOMPADDING", (0,0), (-1,-1), 2),
					]))
			
					content.append(table)
					doc.build(content)
			
					QMB.information(None, tr("Berhasil"), f"{tr('Kartu')} {file_name} {tr('telah tersimpan dalam')} {path}")
					daftar_pengguna()
							
			for x in [teks, lbl_qr, btn_save]:
				kanan.addWidget(x)
			btn_save.clicked.connect(lambda: safe_run(save_pdf))
								
		def release_qr(id):
			info = next((p for p in user if p["inisial_code"].lower() == id.lower()), None)
			if info:
				pratinjau_qr(info["nama"], info["status"], id)
			
		"""----End brain functuin----"""
		
		stts = getData("validasi_owner")
		user = getData("user")		
		atas, tengah, bawah, fr_tengah, fr_bawah, fr_midle, midle = make_main_frame()
		kiri, kanan, fr_kiri, fr_kanan = set_bawah()
		validasi_owner, cari_pengguna = set_atas()
		set_tengah()
		set_midle()
		cari_pengguna.textChanged.connect(lambda: set_tengah(cari_pengguna.text().strip()))
		
	def tulis_struk():
		if not va("tulis struk"):
			QMB.critical(None, "", tr("Anda tidak diizinkan"))
			return
		def get_receipt():
			try:
				path = os.path.join(folder_struk, "struk_1.txt")
				with open(path, "r") as f:
					template = f.read()
			except Exception:
				template = ""
			kotak_teks.setPlainText(template)
			kotak_teks.setReadOnly(True)
		
		def open_edit():
			if not va("tulis ulang struk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			kotak_teks.setReadOnly(False)
			kotak_teks.setFocus()
		
		def simpan_struk():
			struk = kotak_teks.toPlainText().strip()
			if not struk:
				QMB.warning(None, tr("Gagal"), tr("Tulis template struk dengan format yang benar"))
				return
			nama, ok = input_string(tr("Nama struk"), tr("Masukkan nama struk"))
			if ok:
				if koneksi["connect"] == 1:
					data_struk = {
						"nama": nama,
						"struk": struk
					}
					upload_data("tulis_struk", data_struk, f"{tr('Struk')} {nama} {tr('telah ditambahkan')}!")
				else:
					file_path = os.path.join(folder_struk, f"{nama}.txt")
					with open(file_path, "w") as f:
						f.write(struk)
					QMB.information(None, tr("Berhasil"), f"{tr('Struk')} {nama} {tr('telah ditambahkan')}!")
				tulis_
				struk()	
		def minta():
			if not va("ambil struk"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			struk, ok = input_string(tr("Dapatkan struk"), tr("Tuliskan nama struk"))
			if not ok:
				return
			if koneksi["connect"] == 1:
				try:
					res = requests.get(f"{SERVER_URL}/ambil_struk/{struk}")
					if res.status_code == 200:
						file_path = os.path.join(folder_struk, "struk_1.txt")
						with open(file_path, "wb") as f:
							f.write(res.content)
					else:
						QMB.warning(None, tr("Gagal"), tr("Pengambilan gagal"))
				except Exception as e:
					QMB.critical(None, tr("Gagal"), str(e))
			else:
				path_open = os.path.join(folder_struk, struk + ".txt")
				if not os.path.exists(path_open):
					QMB.warning(None, tr("Tidak ditemukan"), f"{tr('Struk')} {struk} {tr('tidak ditemukan')}!")
					return
				with open(path_open, "rb") as f:
					receipt = f.read()
				with open(os.path.join(folder_struk, "struk_1.txt"), "wb") as f:
					f.write(receipt)
				QMB.information(None, tr("Berhasil"), f"{tr('Struk')} {struk} {tr('telah ditambahkan')}!")					
			get_receipt()
			
		def cek_qr():
			status_data = getData("status_qr")
			if not status_data:
				cek_opsi.setChecked(False)
			else:
				status = next((p["status"] for p in status_data), 0)
				cek_opsi.setChecked(True if status == 1 else False)
				opsi.setCurrentText(next((p["tipe"] for p in status_data), "Barcode"))
		
		def qr_upload():
			tipe = opsi.currentText()
			status = cek_opsi.isChecked()
			if not status:
				return
			if koneksi["connect"] == 1:
				upload_data("tambah_tipe_gambar_struk", {"tipe": tipe}, f"{tipe} {tr('akan dicetak dalam struk')}!")
			else:
				cursor.execute("DELETE FROM status_qr")
				cursor.execute("INSERT INTO status_qr (status, tipe) VALUES (?, ?)", (1, tipe))
				conn.commit()
				QMB.information(None, tr("Berhasil"), f"{tipe} {tr('akan dicetak dalam struk')}!")
		
		def pengaturan_nota():
			if not va("pengaturan nota"):
				QMB.warning(None, "", tr("Anda tidak diizinkan"))
				return
			def get_text():
				dict_data = {}
				for i, (a, b) in enumerate(list(widgets.items())):
					if i != 4:
						dict_data[a] = b.toPlainText().strip()
				return dict_data
					
			def setup_widget():
				return {
					"judul": box_maker(tr("Tuliskan judul nota")),
					"catatan": box_maker(tr("Tuliskan catatan")),
					"penerima": box_maker(tr("Tuliskan format penerima")),
					"penerbit": box_maker(tr("Tuliskan format penerbit")),
					"simpan": button(tr("Simpan"), font_size_normal, bg)
				}
			def simpan():
				d = get_text()
				j = d.get("judul", "")
				c = d.get("catatan", "")
				ima = d.get("penerima", "")
				bit = d.get("penerbit", "")
				if not all([j, c, ima, bit]):
					QMB.warning(None, tr("Gagal"), tr("Data harus diisi seluruhnya"))
					return
					
				if askyesno(tr("Konfirmasi"), tr("Apakah data sudah benar?")):
					if koneksi["connect"] == 1:
						data = {
							"judul": j,
							"catatan": c,
							"penerima": ima,
							"penerbit": bit
						}
						upload_data("tambah_pengaturan_nota", data, tr("Pengaturan berhasil disimpan"))
					else:
						cursor.execute("SELECT * FROM pengaturan_nota")
						d = cursor.fetchall()
						if not d:
							cursor.execute("INSERT INTO pengaturan_nota (judul, catatan, penerima, penerbit) VALUES (?, ?, ?, ?)", (j, c, ima, bit))
						else:
							cursor.execute("UPDATE pengaturan_nota SET judul = ?, catatan = ?, penerima = ?, penerbit = ? WHERE id = ?", (j, c, ima, bit, 1))
						conn.commit()
						QMB.information(None, tr("Berhasil"), tr("Pengaturan berhasil disimpan"))
					tulis_struk()
						
			def set_on_layout():
				clear_widgets(f3)
				nota = getData("pengaturan_nota")
				n = nota[0] if nota else None
				list_isi = [
					n["judul"] if n else "" if nota else "",
					n["catatan"] if n else "" if nota else "",
					n["penerima"] if n else "" if nota else "",
					n["penerbit"] if n else "" if nota else ""
				]
				for i, p in enumerate(list(widgets.values())):
					if i != 4:
						p.setPlainText(list_isi[i])
					f3_layout.addWidget(p)
				
			widgets = setup_widget()
			set_on_layout()
			widgets["simpan"].clicked.connect(simpan)
						
		clear_widgets(f3)
		kotak_teks = QTextEdit()
		kotak_teks.setPlaceholderText(tr("Ketik template struk disini..."))
		kotak_teks.setFontPointSize(font_size_normal)
		fr = QFrame()
		fr_layout = QHBoxLayout(fr)
		tulis_ulang = button(tr("Tulis ulang"), font_size_normal, bg)
		simpan = button(tr("Simpan"), font_size_normal, bg)
		dapatkan = button(tr("Dapatkan struk"), font_size_normal, bg)
		opsi = combobox(font_size_normal, ["Barcode", "QR code"])
		cek_opsi = checkbutton(tr("Dicetak"), font_size_normal)
		
		btn_lain = button(tr("Pengaturan format nota"), font_size_normal, bg)
		btn_lain.clicked.connect(pengaturan_nota)
		for x in [kotak_teks, fr]:
			f3_layout.addWidget(x)
		fr_layout.addWidget(opsi)
		fr_layout.addWidget(cek_opsi)
		for x in [tulis_ulang, simpan, dapatkan, btn_lain]:
			fr_layout.addWidget(x, alignment=rata_kanan)
		fr_layout.setAlignment(rata_kanan)
		get_receipt()
		cek_qr()
		tulis_ulang.clicked.connect(open_edit)
		simpan.clicked.connect(simpan_struk)
		dapatkan.clicked.connect(minta)
		cek_opsi.toggled.connect(qr_upload)
		
	def metode_pembayaran():
		if not va("media bayar"):
			QMB.critical(None, "", tr("Anda tidak diizinkan"))
			return
		
		def get_picture(n, b):
			pict = None
			if koneksi["connect"] == 1:
				name = b + n + ".jpeg"
				try:
					res = requests.get(f"{SERVER_URL}/lihat_gambar_rekening", params={"name": name}, timeout=5)
					if res.status_code != 200:
						return
				except Exception:
					return
				pict = res.content
			else:
				name = b + n + ".jpeg"
				pict = os.path.join(folder, name)
			return pict
				
		def prepare_layout():
			clear_widgets(f3)
			atas, bawah = QFrame(), QFrame()
			atas_layout, bawah_layout = QGridLayout(atas, alignment=rata_atas), QHBoxLayout(bawah, alignment=rata_kiri)
			for p in [atas, bawah]:
				f3_layout.addWidget(p)
			return atas_layout, bawah_layout
		
		def show_data():
			for i, p in enumerate(data):
				frame = QFrame()
				frame.setObjectName("frame")
				set_expanding(frame, fix, expand)
				frame.setStyleSheet("""
					QFrame#frame {
						background-color: transparent;
						border-bottom: 1px ridge rgba(0,0,0,0.1);
						border-radius: 2px;
					}""")
				layout = QVBoxLayout(frame)
				
				label_gambar = QLabel()
				gbr = get_picture(p["nama_pemilik"], p["bank"])
				show_pictures(gbr, label_gambar, 200)
				
				label_nama = QLabel(f"Nama pemilik: {p['nama_pemilik']}")
				label_bank = QLabel(f"Bank: {p['bank']}")
				label_norek = QLabel(f"Nomor rekening: {p['nomor_rekening']}")
				layout.addWidget(label_gambar)
				fr = QFrame()
				lay = QHBoxLayout(fr, alignment=rata_kiri)
				
				buttons = [
					("Edit", edit_pembayaran),
					("Hapus", hapus_pembayaran),
					("Reupload QR", reupload_qr)
				]
				for a, b in buttons:
					btn = button(tr(a), font_size_normal, bg)
					btn.clicked.connect(lambda *args, id=p["id"], func=b: safe_run(func, id))
					lay.addWidget(btn)
				
				for q in [label_nama, label_bank, label_norek, fr]:
					q.setStyleSheet(style_label_bold(font_size_normal))
					layout.addWidget(q)
				
				atas.addWidget(frame, i//3, i%3, alignment=rata_atas)
				
		def tambahkan():
			ent = [
				("bank", "Bank..."),
				("nama", "Nama pemilik..."),
				("norek", "Nomor rekening...")
			]
			def upload_gambar():
				nonlocal path
				file, _ = QFileDialog.getOpenFileName(filter="*.jpg *.jpeg *.png")
				if file:
					show_pictures(file, picture, 200)
					path = file
			
			def simpan_bayar():
				if not va("alat pembayaran"):
					QMB.warning(None, "", tr("Anda tidak diizinkan"))
					return
				b = entries["bank"].text().strip()
				n = entries["nama"].text().strip()
				norek = entries["norek"].text().strip()
				pict = path
				
				if not all([b, n, norek, pict]):
					QMB.critical(None, tr("Kurang"), tr("Data harus lengkap"))
					return
				
				if askyesno(tr("Konfirmasi"), tr("Upload rekening baru") + "?"):	
					if koneksi["connect"] == 1:
						data = {
							"bank": b,
							"nama": n,
							"norek": norek
						}
						json_file = ("data.json", json.dumps(data), "application/json")
						try:
							with open(pict, "rb") as f:
								img_file = (b + n + ".jpeg", f, "image/jpeg")
								files = {
									"data_json": json_file,
									"data_qr": img_file
								}
								res = requests.post(f"{SERVER_URL}/upload_pembayaran", files=files)
								if res.status_code == 200:
									QMB.information(None, tr("Berhasil"), tr("Upload data berhasil"))
								else:
									QMB.warning(None, tr("Gagal"), f"{tr('Gagal upload data')}: {res.status_code}")
						except Exception as e:
							QMB.critical(None, "", f"{e}")
						
					else:
						p = Image.open(pict).convert("RGB")
						file_name = b + n + ".jpeg"
						file_path = os.path.join(folder, file_name)
						p.save(file_path, "jpeg", quality=90, optimize=True)
						cursor.execute("INSERT INTO media_bayar (bank, nama_pemilik, nomor_rekening) VALUES (?, ?, ?)", (b, n, norek))
						conn.commit()
						QMB.information(None, tr("Berhasil"), f"{tr('Pembayaran dengan bank')} {b} {tr('atas nama')} {n} {tr('telah ditambahkan')}!")
					metode_pembayaran()
					
			path = None
			entries = entry_maker(kiri_layout, ent)
			button_save = button(tr("Simpan"), font_size_normal, bg)
			button_upload = button(tr("Upload foto QR Code"), font_size_normal, bg)
			button_upload.clicked.connect(upload_gambar)
			button_save.clicked.connect(simpan_bayar)
			for p in [button_upload, button_save]:
				kiri_layout.addWidget(p)
		
		def edit_pembayaran(id):
			clear_widgets(kiri)
			ent = [
				("bank", "Bank baru..."),
				("nama", "Nama pemilik baru..."),
				("norek", "Nomor rekening baru...")
			]
			entries = entry_maker(kiri_layout, ent)
			info = next((p for p in data if p["id"] == id), None)
			if info:
				entries["bank"].setText(info["bank"])
				entries["nama"].setText(info["nama_pemilik"])
				entries["norek"].setText(info["nomor_rekening"])
			
			def simpan_edit():
				bank = entries["bank"].text().strip()
				nama = entries["nama"].text().strip()
				norek = entries["norek"].text().strip()
				if not all([bank, nama, norek]):
					QMB.warning(None, tr("Gagal"), tr("Seluruh input harus diisi"))
					return
				if askyesno(tr("Konfirmasi"), f"{tr('Simpan perubahan rekening milik')} {info['nama_pemilik']}?"):
					if koneksi["connect"] == 1:
						data = {
							"nama": nama,
							"bank": bank,
							"norek": norek,
							"id": id
						}
						setData("edit_rekening", data)
					else:
						nama_lama = info["bank"] + info["nama_pemilik"] + ".jpeg"
						nama_baru = bank + nama + ".jpeg"
						os.rename(os.path.join(folder, nama_lama), os.path.join(folder, nama_baru))
						
						cursor.execute("UPDATE media_bayar SET nama_pemilik = ?, bank = ?, nomor_rekening = ? WHERE id = ?", (nama, bank, norek, id))
						conn.commit()
						QMB.information(None, tr("Berhasil"), tr("Data rekening milik") + " " + info["nama_pemilik"] + " telah diperbarui")
					metode_pembayaran()
				
			btn = button(tr("Simpan pembaruan"), font_size_normal, bg)
			btn.clicked.connect(simpan_edit)
			kiri_layout.addWidget(btn)
			
		def hapus_pembayaran(id):
			info = next((p for p in data if p["id"] == id), None)
			nama = info["bank"] + info["nama_pemilik"] + ".jpeg"
			
			if askyesno(tr("Konfirmasi"), tr("Apakah Anda yakin akan menghapus rekening") + " " + info["nama_pemilik"] + " " + tr("dari daftar") + "?"):
				if koneksi["connect"] == 1:
					dt = {
						"id": id,
						"nama": nama
					}
					setData("hapus_rekening", dt)
				else:
					os.remove(os.path.join(folder, nama))
					cursor.execute("DELETE FROM media_bayar WHERE id = ?", (id, ))
					conn.commit()
					QMB.information(None, tr("Berhasil"), tr("Rekening milik") + " " + nama.replace(".jpeg", "") + " " + tr("telah dihapus"))
				metode_pembayaran()
			
		def reupload_qr(id):
			file, _ = QFileDialog.getOpenFileName(filter="*.jpg *.jpeg *.png")
			if file:				
				def unggah():
					info = next((p for p in data if p["id"] == id), None)
					if askyesno(tr("Konfirmasi"), f"{tr('Upload gambar untuk')} {info['nama_pemilik']} - {info['bank']} {tr('Sekarang')}?"):
						if koneksi["connect"] == 1:
							try:
								with open(file, "rb") as f:
									img_file = (
										info["bank"] + info["nama_pemilik"] + ".jpeg",
										f,
										"image/jpeg"
									)
									setFile("reupload_qr", {"file": img_file})
							except Exception as e:
								QMB.critical(None, "Error", str(e))
						else:
							spin = set_spinner(window)
							file_name = info["bank"] + info["nama_pemilik"] + ".jpeg"
							path = os.path.join(folder, file_name)
							shutil.copy(file, path)
							spin.deleteLater()
							QMB.information(None, tr("Berhasil"), f"{tr('Gambar baru untuk rekening')} {info['bank']} - {info['nama_pemilik']} {tr('telah diperbarui')}")
						metode_pembayaran()
							
				clear_widgets(kiri)
				show_pictures(file, picture, 200)
				btn = button(tr("Unggah"), font_size_normal, bg)
				btn.clicked.connect(unggah)
				kiri_layout.addWidget(btn, alignment=rata_kanan)
			
		data = getData("media_bayar")		
		atas, bawah = prepare_layout()
		kiri, kanan = QFrame(), QFrame()
		kiri_layout, kanan_layout = QVBoxLayout(kiri, alignment=rata_kiri), QVBoxLayout(kanan, alignment=Qt.AlignCenter)
		for p in [kiri, kanan]:
			set_expanding(p, expand, fix)
			bawah.addWidget(p)
		picture = QLabel()
		kanan_layout.addWidget(picture)
		show_data()
		tambahkan()

	profil = button_photo(tr("Profil"), resource_path("Pictures/profil.png"), icon_size, profil_func)
	produk = button_photo(tr("Produk"), resource_path("Pictures/produk.png"), icon_size, lambda: safe_run(daftar_produk.setup))
	user = button_photo(tr("Pengguna"), resource_path("Pictures/tambah_customer.png"), icon_size, lambda: safe_run(daftar_pengguna))
	pelanggan = button_photo(tr("Pelanggan"), resource_path("Pictures/customer.png"), icon_size, customer_menu)
	supp = button_photo(tr("Penyedia"), resource_path("Pictures/supplier.png"), icon_size, supplier_menu)
	taxes = button_photo(tr("Pajak"), resource_path("Pictures/total.png"), icon_size, pajak_aplikasi.setup)
	media_bayar = button_photo(tr("Media bayar"), resource_path("Pictures/metode_bayar.png"), icon_size, metode_pembayaran)
	write_struk = button_photo(tr("Tulis struk"), resource_path("Pictures/edit_struk.png"), icon_size, tulis_struk)
	pengeluaran = button_photo(tr("Biaya"), resource_path("Pictures/pengeluaran.png"), icon_size, lambda: safe_run(pengeluaran_aplikasi.setup))
	pesan = button_photo(tr("Permintaan"), resource_path("Pictures/ddd.png"), icon_size, permintaan)
	for x in [profil, produk, user, pelanggan, supp, taxes, media_bayar, write_struk, pengeluaran, pesan]:
		x.setStyleSheet(f2_btn(font_size_normal))
		f2_layout.addWidget(x, alignment=Qt.AlignmentFlag.AlignLeft)
	profil_func()

def permintaan():
	if not va("permintaan"):
		QMB.warning(None, "", tr("Anda tidak diizinkan"))
		return
	def prepare_ui():
		clear_widgets(f3)
		fr = QFrame()
		f3_layout.addWidget(fr)
		return QGridLayout(fr)
	
	def hapus_permintaan(id):
		if not va("hapus permintaan"):
			QMB.warning(None, "", tr("Anda tidak diizinkan"))
			return
		if askyesno(tr("Konfirmasi"), tr("Hapus permintaan sekarang?")):
			if koneksi["connect"] == 1:
				upload_data("edit_permintaan", {"id": id, "status": "delete"}, tr("Data permintaan telah dihapus"))
			else:
				cursor.execute("DELETE FROM permintaan WHERE id = ?", (id, ))
				conn.commit()
				QMB.information(None, tr("Berhasil"), tr("Data permintaan telah dihapus"))
			permintaan()

	def approved(data, id, status, jenis, pemesan):
		if not va("setujui permintaan"):
			QMB.warning(None, "", tr("Anda tidak diizinkan"))
			return
		if status.lower() in ["approved", "diproses"]:
			QMB.warning(None, tr("Peringatan"), f"{data.get('nama', '')} {tr('telah disetujui')}")
		if jenis.lower() == "pesanan pembeli":
			safe_run(proses_permintaan_pesanan, data, id, pemesan)
		else:
			if askyesno(tr("Konfirmasi"), f"{tr('Anda akan menambahkan')} {data.get('nama', '')}"):
				if koneksi["connect"] == 1:
					upload_data("tambah_user", data, f"{data.get('nama', '')} {tr('telah ditambahkan')}")
					try:
						res = requests.post(f"{SERVER_URL}/edit_permintaan", json={"id": id, "status": "approved"})
						if res.status_code == 200:
							permintaan()
						else:
							QMB.warning(None, "", str(res.status_code))
					except Exception as e:
						QMB.critical(None, "", str(e))
						
				else:
					cursor.execute("INSERT INTO user (nama, status, inisial, inisial_code, password, pertanyaan, jawaban) VALUES (?, ?, ?, ?, ?, ?, ?)", (data.get("nama", ""), data.get("status", ""), data.get("inisial", ""), data.get("inisial_code", ""), data.get("password", ""), data.get("pertanyaan", ""), data.get("jawaban", "")))
					cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Tambah pengguna", data.get("nama", ""), 1, data.get("inisial_code", ""), data.get("operator", ""), data.get("sumber", "")))
	
					teks = f"{data.get('inisial_code', '')} {data.get('pw', '')}"
					qr_teks = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
					qr_teks.add_data(teks)
					qr_teks.make(fit=True)
						
					img = qr_teks.make_image(fill_color=choose_color(), back_color="white")
					path = os.path.join(folder_foto_profil, f"{data.get('nama', '')} {data.get('inisial_code', '')}.jpeg")
					img.save(path, "jpeg", quality=90, optimize=True)
					cursor.execute("UPDATE permintaan SET status = ? WHERE id = ?", ("approved", id))
					conn.commit()
					QMB.information(None, tr("Berhasil"), f"{tr('Pengguna baru')} {data.get('nama', '')} {tr('telah ditambahkan')}!")
						
	def open_data(id):
		d = next((p for p in data if p["id"] == id), None)
		dt = json.loads(d["data"])
		jenis = d["jenis"]
		
		def prepare_frames():
			wd = {
				"judul": QPushButton(d["status"].upper()),
				"atas": QFrame(),
				"tengah": QFrame(),
				"bawah": QFrame()
			}
			wd["judul"].setStyleSheet(f"""
				QPushButton {{
					background-color: transparent;
					font-size: {font_size_judul + 3}px;
					font-weight: bold;
					font-family: Arial;
					border: none;
					border-radius: 2px;
					padding: 10px;
				}}""")
			for p in ["atas", "bawah"]:
				wd[p].setStyleSheet(style_frame(bg))
			clear_widgets(f3)
			for p in list(wd.values()):
				f3_layout.addWidget(p)
			return QGridLayout(wd["atas"], alignment=rata_kiri), QGridLayout(wd["tengah"]), QHBoxLayout(wd["bawah"], alignment=rata_kanan)
		
		def set_atas_wd():
			info = [
				("Waktu", d["waktu"]),
				("Jenis", d["jenis"])
			]
			for i, (a, b) in enumerate(info):
				aa, bb, cc = QLabel(tr(a)), QLabel(":"), QLabel(b.capitalize())
				for p in [aa, bb, cc]:
					p.setStyleSheet(style_label_bold(font_size_normal))
				atas.addWidget(aa, i, 0)
				atas.addWidget(bb, i, 1)
				atas.addWidget(cc, i, 2)
		
		def set_tengah_wd():
			if d["jenis"].lower() == "pesanan pembeli":
				copydata = dt.copy()
				copydata.pop("belanjaan", None)
				for i, (key, value) in enumerate(list(copydata.items())):	
					aa, bb, cc = QLabel(tr(key.replace("_", " ").capitalize())), QLabel(":"), QLabel(str(value))
					for p in [aa, bb, cc]:
						p.setStyleSheet(style_label(font_size_normal))
					tengah.addWidget(aa, i, 0, alignment=rata_kiri)
					tengah.addWidget(bb, i, 1, alignment=rata_kiri)
					tengah.addWidget(cc, i, 2, alignment=rata_kiri)
		
			elif d["jenis"].lower() == "pendaftaran pengguna baru":
				for i, (key, value) in enumerate(list(dt.items())):
					aa, bb, cc = QLabel(tr(key.replace("_", " ").capitalize())), QLabel(":"), QLabel(str(value))
					for p in [aa, bb, cc]:
						p.setStyleSheet(style_label(font_size_normal))
					tengah.addWidget(aa, i, 0, alignment=rata_kiri)
					tengah.addWidget(bb, i, 1, alignment=rata_kiri)
					tengah.addWidget(cc, i, 2, alignment=rata_kiri)
		
		def set_bawah_wd():
			btn = {
				"agree": button(tr("Setujui"), font_size_normal, "lightgreen"),
				"delete": button(tr("Hapus"), font_size_normal, "red"),
				"cancel": button(tr("Batal"), font_size_normal, "yellow")
			}
			btn["cancel"].clicked.connect(permintaan)
			btn["delete"].clicked.connect(lambda: safe_run(hapus_permintaan, id))
			btn["agree"].clicked.connect(lambda: safe_run(approved, dt, id, d["status"], jenis, d["oleh"]))
			for p in list(btn.values()):
				bawah.addWidget(p, alignment=rata_kanan)
									
		atas, tengah, bawah = prepare_frames()
		safe_run(set_atas_wd)
		safe_run(set_tengah_wd)
		safe_run(set_bawah_wd)
				
	def show_data():
		for i, p in enumerate(sorted(data, key=lambda x: parse_date(x["waktu"]), reverse=True)):
			huruf = "800" if p["status"].lower() in ["pending", "ditangguhkan"] else "normal"
			warna = "green" if p["status"].lower() in ["pending", "ditangguhkan"] else "black"
			btn = label_photo(p["jenis"] + "\n" + p["waktu"], resource_path("Pictures/letter.png"), (50,50))
			btn.setStyleSheet(f"""
				QPushButton {{
					background-color: transparent;
					font-size: {font_size_normal}px;
					border: none;
					border-radius: 2px;
					font-weight: {huruf};
					padding: 10px;
					color: {warna};
				}}
				QPushButton:hover {{
					border: 1px solid {bg};
					font-weight: normal;
				}}""")
			btn.clicked.connect(lambda *args, x=p["id"]: safe_run(open_data, x))
			layout.addWidget(btn, i//2, i%2, alignment=rata_kiri)
			
	layout = prepare_ui()
	data = getData("permintaan")
	if not data:
		QMB.information(None, tr("Kosong"), tr("Permintaan data tidak tersedia"))
		return
	show_data()
				
def format_rupiah(entry_uang):
	fr = format_uang_app
	e = entry_uang.text().strip()
	if len(e) == 1:
		if e.isdigit():
			t = float(e)
			teks = f"{t:,.{fr[-1]}f}".replace(".", ",").split(",")
			teks_uang = fr[2].join(teks[:-1]) + fr[3] + teks[-1]
	else:
		p = e.replace(fr[0], "").replace(fr[2], "").replace(fr[3], ".")
		t = float(p)
		teks = f"{t:,.{fr[-1]}f}".replace(".", ",").split(",")
		teks_uang = fr[2].join(teks[:-1]) + fr[3] + teks[-1]
	input_uang = fr[0] + teks_uang if fr[1].lower() == "kiri" else teks_uang + fr[0]
	entry_uang.setText(input_uang)
	def apply():
		des = input_uang.find(fr[-2])
		if des == -1:
			des = len(teks_uang)
		entry_uang.setCursorPosition(des)
	QTimer.singleShot(0, apply)

keranjang = []
penyimpanan_sementara = []
penyimpanan_undo = []
penyimpanan_redo = []
shortcuts = []

undo_count, redo_count = 0, 0
cursor.execute("SELECT inisial_code FROM operator")
idi = cursor.fetchone()
id = idi["inisial_code"] if idi else "F00"
nomor_transaksi = id[:3] + "_" + datetime.now().strftime("%f")

def render_keranjang_khusus(keranjang_list):
	isi = ""
	for item in keranjang_list:
		total_item = item.get("subtotal_jual", 0)
		isi += f"{item['nama']}\n{item['qty']} x {pretty_money(item['harga_jual'])} = {pretty_money(total_item)}\n"
	return isi.strip()

def cetak_struk(data, no_trans):
	global profil_data
	if askyesno("Cetak struk", "Ingin cetak struk?"):
		try:
			folder = "Struk penjualan"
			os.makedirs(folder, exist_ok=True)
			
			with open(os.path.join(folder_struk, "struk_1.txt"), "r", encoding="utf-8") as f:
				template = f.read()
			struk_final = template.format(**data)
			
			berhasil_cetak = False
			if printer:
				for p in printer:
					tipe = p.get("tipe", "").lower()
					if tipe == "usb port":
						try:
							idven = p.get("id_vendor", "")
							idprod = p.get("id_produk", "")
							if idven and idprod:
								printer_usb = Usb(idven, idprod)
								printer_usb.text(struk_final)
								cetak_qr = getData("status_qr")
								tipe_kode = cetak_qr[0]["tipe"].lower() if cetak_qr else "qr code"
								status = cetak_qr[0]["status"] if cetak_qr else 0
								
								if status == 1:
									if tipe_kode == "qr code":
										qr_teks = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=7, border=4)
										qr_teks.add_data(no_trans)
										qr_teks.make(fit=True)
										img = qr_teks.make_image(fill_color="black", back_color="white")
									else:
										img = barcode.get("code128", no_trans, writer=ImageWriter())
									printer_usb.image(img)
								printer_usb.cut()
								berhasil_cetak = True
								QMB.information(None, "Transaksi berhasil", "Transaksi sukses. Terima kasih telah berbelanja!")
								break
						except Exception as e:
							QMB.critical(None, "Error", str(e))
							continue
					
			if not berhasil_cetak:
				file_struk = os.path.join(folder, f"STRUK-{no_trans}.txt")
				with open(file_struk, "w", encoding="utf-8") as f:
					f.write(struk_final)
				QMB.information(None, tr("Berhasil"), "Printer tidak tersedia/error. Struk digital telah disimpan!")

		except Exception as e:
			QMB.critical(None, tr("Gagal"), f"Gagal cetak struk {e}")		
	else:
		QMB.information(None, tr("Berhasil"), "Transaksi berhasil. Terima kasih telah berbelanja!")

def proses_permintaan_pesanan(data, id, pemesan):
	def cek_status_pesanan(id):
		try:
			res = requests.get(f"{SERVER_URL}/lihat_data/permintaan")
			minta = res.json()
			status = next((p["status"] for p in minta if p["id"] == id), "")
			if status.lower() in ["sedang diantar", "selesai"]:
				return False, f"Pesanan {status}"
			else:
				return True, f"Pesanan {status}"
		except Exception as e:
			return False, str(e)
			
	def proses_data():
		persen_pajak = pjk[0]["persen"] if pjk[0]["persen"] else 0 if pjk else 0
		status_pajak = pjk[0]["aktif"] if pjk else 0
		belanja = data.get("belanjaan", [])
		keranjang.clear()
		keranjang.extend(belanja)
		result = safe_run(seleksi_data, status_pajak, persen_pajak)
		return result
		
	def prepare_layout():
		clear_widgets(f3)
		atas, tengah, bawah = QFrame(), QFrame(), QFrame()
		atas.setObjectName("atas")
		atas.setStyleSheet(f"""
			QFrame#atas {{
				background-color: {bg};
				padding: 5px;
				border: none;
				border-radius: 2px;
			}}""")
		
		for i, p in enumerate([atas, tengah, bawah]):
			f3_layout.addWidget(p)
		return QGridLayout(atas, alignment=rata_kiri), QVBoxLayout(tengah, alignment=rata_kiri), QHBoxLayout(bawah, alignment=rata_kanan)
	
	def olahan_data():
		global pjk
		kena_pajak = cek_pajak(total, pjk[0]["aktif"], pjk[0]["persen"])
		kp = total - kena_pajak
		
		dt = {
			"pemesan": pemesan,
			"nama": data.get("nama", ""),
			"alamat": data.get("alamat", ""),
			"kontak": data.get("kontak", ""),
			"email": data.get("email", ""),
			"catatan": data.get("catatan", ""),
			"bayar": data.get("bayar", ""),
			"no_trans": nomor_transaksi,
			"kena_pajak": kp,
			"status_pajak": pjk[0]["aktif"],
			"persen_pajak": pjk[0]["persen"]
		}
		return dt
	
	def proses_pesanan_sampai_selesai():
		stts, pesan = cek_status_pesanan(id)
		if not stts:
			QMB.information(None, "Ditolak", pesan)
			return
		bayar, _ = input_int("Pembayaran", "Masukkan jumlah pembayaran customer yang tertera!")
			
		if askyesno(tr("Konfirmasi"), tr("Selesaikan data pesanan sekarang?")):
			data_for_olah = {
				"id": id,
				"bayar": bayar,
				"sumber": komputer(),
				"operator": nama_operator()
			}
			try:
				res = requests.post(f"{SERVER_URL}/olah_data_pesanan_sampai_selesai", json=data_for_olah)
				if res.status_code == 200:
					QMB.information(None, tr("Berhasil"), f"{tr('Data pesanan')} {tr('telah selesai diolah')}")
					permintaan()
				else:
					QMB.warning(None, tr("Gagal"), tr("Data gagal diolah") + ": " + str(res.status_code))
			except Exception as e:
				QMB.critical(None, "Error", str(e))
								
	def generate_pdf_pesanan():
		dt = olahan_data()
		safe_run(pdf_pesanan, dt, result, id)
		
	def show_data():
		label_total = QLabel(pretty_money(total))
		ttl = QLabel(tr("TOTAL BELANJA"))
		titik_dua = QLabel(":")
		for i, k in enumerate([ttl, titik_dua, label_total]):
			k.setStyleSheet(style_label_bold(font_size_normal))
			atas.addWidget(k, 11, i)
		datacopy = data.copy()
		datacopy.pop("belanjaan", None)
		
		for i, (a, b) in enumerate(list(datacopy.items())):
			labela, label, labelb = QLabel(a.capitalize()), QLabel(":"), QLabel(str(b))
			for c in [labela, label, labelb]:
				c.setStyleSheet(style_label_bold(font_size_judul))
			atas.addWidget(labela, i, 0)
			atas.addWidget(label, i, 1)
			atas.addWidget(labelb, i, 2)
		
		for p in result:
			model.appendRow([
				QStandardItem(p.get("id", "")),
				QStandardItem(p.get("nama", "")),
				QStandardItem(format_unit(p.get("qty_asli", 0), "unit")),
				QStandardItem(pretty_money(p.get("harga_jual", 0))),
				QStandardItem(pretty_money(p.get("subtotal_jual", 0))),
				QStandardItem(pretty_money(p.get("laba", 0)))
			])
		pdf = button(tr("Olah data"), font_size_normal, "lightgreen")
		pdf.clicked.connect(lambda: safe_run(generate_pdf_pesanan))
		proses = button(tr("Proses pesanan"), font_size_normal, "yellow")
		proses.clicked.connect(lambda: safe_run(proses_pesanan_sampai_selesai))
		bawah.addWidget(pdf, alignment=rata_kanan)
		bawah.addWidget(proses, alignment=rata_kanan)
		
	result = proses_data()
	total = sum(k.get("subtotal_jual", 0) for k in result)
	atas, tengah, bawah = prepare_layout()
	tabel, model = table_maker(["Id", "Nama", "Qty", "Harga jual", "Subtotal", "Laba"])
	tengah.addWidget(tabel, alignment=rata_atas)
	show_data()
	
def seleksi_data(status_pajak, persen_pajak):
	second_keranjang = []

	def kena_pajak(harga):
		if status_pajak == 1:
			return float(harga * (1 + persen_pajak / 100))
		else:
			return harga
				
	def hitung_potongan_tingkat(harga, qty, promo):
		if status_pajak == 1:
			return (harga * qty - promo) * (1 + persen_pajak / 100)
		else:
			return harga * qty - promo
				
	def hitung_potongan_diskon(harga, persen):
		if status_pajak == 1:
			return harga * persen / 100 * (1 + persen_pajak / 100)
		else:
			return harga * persen / 100
				
	for k in keranjang:
		nama = k.get("nama", "")
		qty = k.get("qty", 0)
		harga = k.get("harga", 0)
		barcode = k.get("barcode", "")
		id = k.get("id", "")
			
		ditemukan_tingkat = False
		for b in B:
			if b["id_produk"] != id:
				continue
			min_b = b["min_beli"]
			if qty < min_b:
				continue
			qty_b = qty // min_b
			qty %= min_b
			harga_persatuan = kena_pajak(b["harga_jual"])
			harga_modal = b["harga_modal"]
			subtotal_jual = harga_persatuan * qty_b
			subtotal_modal = harga_modal * qty_b
			laba = (b["harga_jual"] * qty_b) - subtotal_modal
			ditemukan_tingkat = True
			second_keranjang.append({
				"id": id,
				"nama": nama + " " + "x" + str(min_b),
				"barcode": barcode,
				"qty": qty_b,
				"qty_asli": qty_b * min_b,
				"harga_jual": harga_persatuan,
				"subtotal_jual": subtotal_jual,
				"harga_modal": harga_modal,
				"subtotal_modal": subtotal_modal,
				"laba": laba,
				"harga_asli": harga,
				"potongan_tingkat": hitung_potongan_tingkat(harga, min_b, b["harga_jual"]) * qty_b,
				"potongan_diskon": 0,
				"min_diskon": "",
				"min_tingkat": min_b,
				"tipe_promo": "tingkat",
				"persen_pajak": persen_pajak
			})
			break
			
		for a in A:
			if a["id_produk"] != id:
				continue
			min_a = a["min_beli"]
			if qty < min_a:
				continue
			qty_a = qty // min_a
			qty %= min_a
			harga_persatuan = kena_pajak(a["harga_jual"])
			subtotal_jual = harga_persatuan * qty_a
			harga_modal = a["harga_modal"]
			subtotal_modal = harga_modal * qty_a
			laba = (a["harga_jual"] * qty_a) - subtotal_modal
			ditemukan_tingkat = True
			second_keranjang.append({
				"id": id,
				"nama": nama + " " + "x" + str(min_a),
				"barcode": barcode,
				"qty": qty_a,
				"qty_asli": qty_a * min_a,
				"harga_jual": harga_persatuan,
				"subtotal_jual": subtotal_jual,
				"harga_modal": harga_modal,
				"subtotal_modal": subtotal_modal,
				"laba": laba,
				"harga_asli": harga,
				"potongan_tingkat": hitung_potongan_tingkat(harga, min_a, a["harga_jual"]) *qty_a,
				"potongan_diskon": 0,
				"min_diskon": "",
				"min_tingkat": min_a,
				"tipe_promo": "tingkat",
				"persen_pajak": persen_pajak
			})
			break
				
		if ditemukan_tingkat and qty > 0:
			for p in produk_data:
				if p["id_produk"] == id:
					hm = p["harga_modal"]
					subtotal_modal = hm * qty
			
					hj = p["harga_jual"]
					harga_value = kena_pajak(hj)
					subtotal = harga_value * qty
					laba = (hj * qty) - subtotal_modal
			
					second_keranjang.append({
						"id": id,
						"nama": nama,
						"barcode": barcode,
						"qty": qty,
						"qty_asli": qty,
						"harga_jual": harga_value,
						"subtotal_jual": subtotal,
						"harga_modal": hm,
						"subtotal_modal": subtotal_modal,
						"laba": laba,
						"harga_asli": harga,
						"potongan_tingkat": 0,
						"potongan_diskon": 0,
						"min_diskon": "",
						"min_tingkat": "",
						"tipe_promo": "",
						"persen_pajak": persen_pajak
					})
					break
				
		if not ditemukan_tingkat:
			for p in produk_data:
				if p["id_produk"] == id:
					hm = p["harga_modal"]
					subtotal_modal = hm * qty
					for q in diskon_data:
						if q["nama"].lower() == nama.lower() or q["barcode"] == barcode:
							min_qty = q["min"]
							if qty < min_qty:
								continue
							hj = p["harga_jual"]
							harga_diskon = hj * (1 - q["persen"] / 100)
							harga_value = kena_pajak(harga_diskon)
							subtotal = harga_value * qty
							laba = (harga_diskon * qty) - subtotal_modal
							second_keranjang.append({
								"id": id,
								"nama": nama + " " + f"Disk{q['persen']}%",
								"barcode": barcode,
								"qty": qty,
								"qty_asli": qty,
								"harga_jual": harga_value,
								"subtotal_jual": subtotal,
								"harga_modal": hm,
								"subtotal_modal": subtotal_modal,
								"laba": laba,
								"harga_asli": hj,
								"potongan_tingkat": 0,
								"potongan_diskon": hitung_potongan_diskon(hj, q["persen"]) * qty,
								"min_diskon": min_qty,
								"min_tingkat": "",
								"tipe_promo": "diskon",
								"persen_pajak": persen_pajak
							})
							break
					else:
						hj = p["harga_jual"]
						harga_value = kena_pajak(hj)
						subtotal = harga_value * qty
						laba = (hj * qty) - subtotal_modal
						second_keranjang.append({
							"id": id,
							"nama": nama,
							"barcode": barcode,
							"qty": qty,
							"qty_asli": qty,
							"harga_jual": harga_value,
							"subtotal_jual": subtotal,
							"harga_modal": hm,
							"subtotal_modal": subtotal_modal,
							"laba": laba,
							"harga_asli": hj,
							"potongan_tingkat": 0,
							"potongan_diskon": 0,
							"min_diskon": "",
							"min_tingkat": "",
							"tipe_promo": "",
							"persen_pajak": persen_pajak
						})
	return second_keranjang
								
def transaksi_baru():
	def hide_frames():
		for x in [f1, left]:
			x.hide()
		for x in [f2, f3]:
			clear_widgets(x)
			
	state_hide = True
	def show_and_hide_f1left():
		nonlocal state_hide
		if state_hide:
			for p in [f1, left]:
				p.show()
			state_hide = False
		else:
			for p in [f1, left]:
				p.hide()
			state_hide = True
	
	def kembali_tr():
		shortcuts.clear()
		for p in [left, f1]:
			p.show()
		transaksi()
		
	def do_undo():
		if penyimpanan_undo:
			if keranjang:
				penyimpanan_redo.append(copy.deepcopy(keranjang))
			keranjang.clear()
			keranjang.extend(copy.deepcopy(penyimpanan_undo[-1]))
			penyimpanan_undo.pop()
			safe_run(tampilkan_ringkasan)
			
	def do_redo():
		if penyimpanan_redo:
			if keranjang:
				penyimpanan_undo.append(copy.deepcopy(keranjang))
			keranjang.clear()
			keranjang.extend(copy.deepcopy(penyimpanan_redo[-1]))
			penyimpanan_redo.pop()
			safe_run(tampilkan_ringkasan)
				
	def go_focus_on_first_row(tab, col):
		index = tab.model().index(0, col)
		tab.setCurrentIndex(index)
		tab.scrollTo(index)
		tab.setFocus()
		
	def refresh_transaksi():
		global nomor_transaksi, bayar_separuh
		nonlocal total, kembali, bayar
		
		total, kembali, bayar, bayar_separuh = 0, 0, 0, 0
		penyimpanan_undo.append(copy.deepcopy(keranjang))
		keranjang.clear()
		second_keranjang.clear()
		cursor.execute("SELECT inisial_code FROM operator")
		idcode = cursor.fetchone()
		nomor_transaksi = idcode["inisial_code"][:3] + "_" + datetime.now().strftime("%f")
		safe_run(tampilkan_ringkasan)
			
	def make_frame_on_f2():
		kiri, kanan = QFrame(), QFrame()
		kanan_layout = QVBoxLayout(kanan, alignment=rata_atas)
		set_margin(kanan_layout, 0)
		atas, bawah = QFrame(), QFrame()
		for p in [kiri, atas]:
			p.setStyleSheet(style_frame_putih(bg))
		kiri.setFixedWidth(200)
		set_expanding(atas, expand, fix)
		for p in [kiri, kanan]:
			f2_layout.addWidget(p)
		for q in [atas, bawah]:
			kanan_layout.addWidget(q, alignment=rata_atas)
		return QVBoxLayout(kiri), QHBoxLayout(atas), QHBoxLayout(bawah)
	
	def set_f2_kiri_widgets():
		cursor.execute("SELECT nama, status FROM operator")
		opr = cursor.fetchone()
		nama_pisah = opr["nama"].split()
		teks = nama_pisah[0] + " | " + opr["status"]
		d = {
			"opr": button_photo(teks, resource_path("Pictures/profil.png"), icon_size, show_and_hide_f1left),
			"pjk": checkbutton(tr("Termasuk pajak"), font_size_normal),
			"qr": checkbutton(tr("Cetak QR/Barcode"), font_size_normal)
		}
		d["opr"].setStyleSheet(style_frame(bg))
		for i, p in enumerate(list(d.values())):
			if i == 0:
				f2_kiri.addWidget(p, alignment=rata_atas)
			else:
				f2_kiri.addWidget(p, alignment=rata_kiri)
			munculkan(p)
		return d["pjk"], d["qr"], d["opr"]
	
	def set_atas_kanan_widgets():
		widget = {
			"entri": entry(tr("Masukkan nama produk atau barcode..."), font_size_normal),
			"undo": QPushButton(),
			"redo": QPushButton(),
			"refresh": QPushButton(),
			"back": QPushButton()
		}
		list_icon = [
			"Pictures/undo.png",
			"Pictures/redo.png",
			"Pictures/refresh.png",
			"Pictures/kembali.png"
		]
		f2_atas.addWidget(widget["entri"])
		for i, p in enumerate(list(widget.values())[1:]):
			p.setIcon(QIcon(resource_path(list_icon[i])))
			p.setIconSize(QSize(icon_size[0], icon_size[1]))
			p.setStyleSheet(style_button("transparent", font_size_normal))
			f2_atas.addWidget(p, alignment=rata_kanan)
			munculkan(p)
		widget["back"].clicked.connect(kembali_tr)
		widget["refresh"].clicked.connect(refresh_transaksi)
		widget["undo"].clicked.connect(do_undo)
		widget["redo"].clicked.connect(do_redo)
		return widget["entri"], widget["undo"], widget["redo"], widget["refresh"], widget["back"]

	def set_price_and_change():
		style = f"""
		QPushButton {{
			background-color: transparent;
			font-size: 15px;
			font-weight: bold;
			border: 1px solid transparent;		
		}}"""
		harga = QPushButton(f"Total\n{pretty_money(0)}")
		change = QPushButton(tr("Kembalian") + "\n" + pretty_money(0))
		for x in [harga, change]:
			x.setStyleSheet(style)
			f2_bawah.addWidget(x, alignment=rata_atas)
		return harga, change
		
	def set_kiri_and_kanan_layout():
		return QVBoxLayout(kiri), QVBoxLayout(kanan, alignment=rata_atas), QVBoxLayout(struk_fr, alignment=Qt.AlignCenter), QVBoxLayout(frame_cadangan, alignment=rata_atas)
	
	def set_tabel():
		tabel, model = table_maker(["ID", "NAMA", "QTY", "HARGA JUAL", "SUBTOTAL"])
		kiri_layout.addWidget(tabel)
		return tabel, model
	
	status_input = False
	def input_jumlah_manual(p):
		nonlocal status_input
		status_input = True
		data = [p["id_produk"], p["nama"], "", pretty_money(p["harga_jual"]), pretty_money(p["harga_jual"])]
		data_input = [QStandardItem(str(x)) for x in data]
		model.appendRow(data_input)
		fokus = model.rowCount() - 1
		kolom = 2
		row_fokus = model.index(fokus, kolom)
		tabel.setCurrentIndex(row_fokus)
		tabel.edit(row_fokus)
		entry_barcode.setText("")
	
	def proses_data():
		nonlocal status_input
		data = take_data(tabel, model)
		id = data[0]
		try:
			qty = int(data[2])
		except ValueError as e:
			QMB.critical(None, tr("Gagal"), str(e))
			return
		if status_input:
			for p in produk_data:
				if p["id_produk"] == id:
					for k in keranjang:
						if k.get("id", "") == p["id_produk"]:
							k["qty"] += qty
							break
					else:
						keranjang.append({
							"barcode": p["barcode"],
							"nama": p["nama"],
							"id": p["id_produk"],
							"harga": p["harga_jual"],
							"qty": qty
						})
					break
		else:
			for k in keranjang:
				if k.get("id", "") == id:
					k["qty"] = qty
					break
		status_input = False
		entry_barcode.setFocus()
		safe_run(tampilkan_ringkasan)
			
	def tombol_enter():	
		teks = entry_barcode.text().strip()
		if teks.lower() == "f":
			return go_focus_on_first_row(tabel, 2)
		if teks == "":
			if not keranjang:
				QMB.warning(None, "Gagal", "Belum ada transaksi")
				return
			else:
				stok_kurang = any(k["qty"] > next((p["jumlah"] for p in produk_data if p["nama"] == k["nama"]), 0) for k in keranjang)
				if stok_kurang:
					for k in keranjang:
						produk = next((p for p in produk_data if p["nama"] == k["nama"]), None)
						if produk and k["qty"] > produk["jumlah"]:
							QMB.warning(None, "Stok kurang", f"Stok produk {k['nama']} tidak cukup. Transaksi ditolak!")
							break
					return
				menu_bayar()
				return
		produk_item = next((p for p in produk_data if p["barcode"] == teks or p["nama"].lower() == teks.lower()), None)
		if not produk_item:
			QMB.warning(None, "Gagal", f"Produk {teks} tidak ditemukan!")
			return
		if teks == produk_item["barcode"]:
			if produk_item["jumlah"] <= 0:
				QMB.warning(None, "Gagal", f"Stok produk {produk_item['nama']} habis. Silahkan tambah stok terlebih dahulu!")
				return
			for item in keranjang:
				if item["nama"].lower() == produk_item["nama"].lower():
					if item["qty"] + 1 > produk_item["jumlah"]:
						QMB.warning(None, "Gagal", f"Stok {produk_item['nama']} tidak cukup! Stok saat ini: {produk_item['jumlah']}")
						return
					item["qty"] += 1
					break
			else:
				keranjang.append({
					"nama": produk_item["nama"],
					"barcode": produk_item["barcode"],
					"qty": 1,
					"harga": produk_item["harga_jual"],
					"id": produk_item["id_produk"]
				})
			safe_run(tampilkan_ringkasan)
		else:
			input_jumlah_manual(produk_item)
	
	def tampilkan_ringkasan():
		nonlocal total
		total = 0
		second_keranjang.clear()
		entry_barcode.setText("")
		entry_barcode.setFocus()
		for i, p in enumerate([frame_cadangan, struk_fr, listbox, kiri, kanan]):
			p.hide() if i != 3 else munculkan(p)
			
		dt = safe_run(seleksi_data, status_pajak, persen_pajak)
		second_keranjang.extend(dt)
		
		model.removeRows(0, model.rowCount())
		for p in second_keranjang:
			total += p["subtotal_jual"]
			data = [
				QStandardItem(p.get("id", "")),
				QStandardItem(p.get("nama", "")),
				QStandardItem(str(p.get("qty", 0))),
				QStandardItem(pretty_money(p.get("harga_jual", 0))),
				QStandardItem(pretty_money(p.get("subtotal_jual", 0)))
			]
			model.appendRow(data)
			
		if bayar_separuh != 0:
			show_total = f"Belum dibayar\n{pretty_money(total - bayar_separuh)}"
		else:
			show_total = f"Total\n{pretty_money(total)}"				
		label_harga.setText(show_total)
		
	def hitung_kembalian():
		x = entry_uang.text().strip().replace(frr[0], "").replace(frr[2], "").replace(frr[3], ".")
		nonlocal bayar, kembali
		try:
			byr = float(x)
		except ValueError:
			label_kembali.setText(tr("Input salah"))
			label_kembali.setStyleSheet(salah("red", 15))
			return
		perlu_bayar = float(total) - float(bayar_separuh) if bayar_separuh != 0 else float(total)
		kembali = byr - perlu_bayar
		bayar = byr + bayar_separuh if bayar_separuh != 0 else byr
		if kembali < 0:
			warna = "red"
		elif kembali >= 0:
			warna = "green"
		label_kembali.setText(tr("Kembalian") + "\n" + pretty_money(kembali))
		label_kembali.setStyleSheet(benar(warna, 15))
		
	def menu_bayar():
		munculkan(kanan)
		entry_uang.setFocus()
			
	def update_list(teks):
		listbox.clear()	
		if not teks:
			listbox.hide()
			return
		for i in produk_data:
			if teks.lower() in i["nama"].lower():
				listbox.addItem(i["nama"])
		listbox.hide() if listbox.count() == 0 else munculkan(listbox)
		
	def on_klik():	
		item = listbox.currentItem()	
		if not item:
			return	
		entry_barcode.setText(item.text())
		listbox.hide()
		entry_barcode.setFocus()
		
	def set_input():
		persen_pajak = pjk[0]["persen"] if pjk[0]["persen"] else 0 if pjk else 0
		status_pajak = pjk[0]["aktif"] if pjk else 0
		c = getData("status_qr")
		if not c:
			status_qr = 0
		else:
			status_qr = c[0]["status"] if c[0]["status"] == 1 else 0 if c else 0	
		termasuk_pajak.setChecked(True if status_pajak == 1 else False)
		cetak_qr.setChecked(True if status_qr == 1 else False)
		return persen_pajak, status_pajak, status_qr
		
	def set_pajak():
		pajak_aktif = 1 if termasuk_pajak.isChecked() else 0
		if koneksi["connect"] == 1:
			upload_data("pajak_selalu_aktif", {"aktif": pajak_aktif}, "Selesai")
		else:
			cursor.execute("UPDATE pajak SET aktif = ? WHERE id = ?", (pajak_aktif, 1))
			conn.commit()
	
	def set_qr():
		st = 1 if cetak_qr.isChecked() else 0
		if koneksi["connect"] == 1:
			upload_data("cetak_qr_di_struk", {"status": st}, "Selesai")
		else:
			cursor.execute("SELECT * FROM status_qr")
			data = cursor.fetchone()
			if not data:
				cursor.execute("INSERT INTO status_qr (status, tipe) VALUES (?, ?)", (st, ""))
			else:
				cursor.execute("UPDATE status_qr SET status = ? WHERE id = ?", (st, data["id"]))
			conn.commit()
	
	def set_f3_widgets():
		main_frame = {
			"atas": QFrame(),
			"bawah": QFrame()
		}
		child_frame = {
			"cadang": QFrame(),
			"struk": QFrame(),
			"list": listbox_maker(),
			"kiri": QFrame(),
			"kanan": QFrame()
		}
		for i, p in enumerate(list(main_frame.values())):
			if i == 0:
				set_expanding(p, expand, expand)
			else:
				set_expanding(p, expand, fix)
			f3_layout.addWidget(p)
		layouts = {
			"atas": QHBoxLayout(main_frame["atas"], alignment=rata_atas),
			"bawah": QGridLayout(main_frame["bawah"], alignment=rata_kiri)
		}
		for p in list(layouts.values()):
			set_margin(p, 0)
			
		for i, p in enumerate(list(child_frame.values())):
			if i in [0, 1, 2, 4]:
				p.hide()
			else:
				p.show()
			layouts["atas"].addWidget(p)
		return child_frame["cadang"], child_frame["struk"], child_frame["list"], child_frame["kiri"], child_frame["kanan"], layouts["bawah"]

	def set_kanan_hiding_widgets():
		global pemesan, kontak_pemesan
		cust = getData("customer")
		cs_list = list({p["nama"] + " " + p["kontak"] for p in cust})
		d = {
			"lbl": label_photo(tr("BAYAR"), resource_path("Pictures/pemasukan_hari_ini.jpg"), icon_size),
			"uang": QLineEdit(),
			"npem": QComboBox(),
			"pem": QLineEdit(),
			"finish": QPushButton(tr("Selesai"))
		}
		
		d["lbl"].setStyleSheet(f"""
			QPushButton {{
				background-color: transparent;
				color: black;
				font-size: 15px;
				font-weight: bold;
				border: 1px solid transparent;
				border-radius: 2px;
				padding: 10px;
			}}""")
		for i, p in enumerate([d["uang"], d["pem"]]):
			if i == 1:
				p.setText("Customer")
				p.setPlaceholderText(tr("Masukkan pembeli baru..."))
			else:
				p.setPlaceholderText(tr("Masukkan jumlah uang..."))
			p.setStyleSheet(f"""
				QLineEdit {{
					border: 1px solid black;
					border-radius: 2px;
					padding: 10px;
					font-size: {font_size_normal}px;
				}}
				QLineEdit:focus {{
					border: 1px solid {bg};
				}}""")
		d["npem"].addItems(cs_list)
		d["npem"].setStyleSheet(f"""
			QComboBox {{
				border: 1px solid black;
				border-radius: 2px;
				padding: 10px;
				font-size: {font_size_normal}px;
			}}""")
		d["finish"].setStyleSheet(f"""
			QPushButton {{
				background-color: #63B44AFF;
				padding: 10px;
				font-size: {font_size_normal}px;
				font-weight: bold;
				border: 1px solid black;
				border-radius: 2px;
			}}""")
						
		for p in list(d.values()):
			kanan_layout.addWidget(p, alignment=rata_atas)
		return d["lbl"], d["uang"], d["npem"], d["pem"], d["finish"]
	
	def upload_keserver(d, w, n, b, k):
		nonlocal total
		try:
			res = requests.post(f"{SERVER_URL}/penjualan_campuran", json=d)
			if res.status_code == 200:
				preview(b, k, n, w)
				
				toko = profil_data[0]["nama"] if profil_data else "-"
				alamat = profil_data[0]["alamat"] if profil_data else "-"
				kontak = profil_data[0]["kontak"] if profil_data else "-"
				
				data_transaksi = {
					"toko": toko,
					"alamat": alamat,
					"kontak": kontak,
					"waktu": date_translator(w, bahasa_aplikasi),
					"operator": nama_operator(),
					"no_trans": n,
					"isi_keranjang": render_keranjang_khusus(second_keranjang),
					"total": pretty_money(total),
					"bayar": pretty_money(b),
					"kembali": pretty_money(k)
				}
				cetak_struk(data_transaksi, n)
				reset_gui()
		except Exception as e:
			QMB.critical(None, tr("Gagal"), f"Upload data gagal: {e}")
			return
				
	sedang_proses = False
	def update_stok():
		nonlocal sedang_proses
		tot = total - bayar_separuh if bayar_separuh != 0 else total
		if bayar < tot:
			QMB.critical(None, tr("Gagal"), tr("Pembayaran tidak cukup"))
			return
		if sedang_proses:
			return
		sedang_proses = True
		waktu = now_str()
		no_trans = nomor_transaksi
		if koneksi["connect"] == 1:
			data = {
				"items": copy.deepcopy(second_keranjang),
				"total": total,
				"bayar": bayar,
				"kembali": kembali,
				"sumber": komputer(),
				"operator": nama_operator(),
				"no_trans": no_trans,
				"waktu": waktu,
				"pembeli": pembeli.text() if pembeli.text() != "" else nama_pembeli.currentText() if nama_pembeli.currentText() != "" else "Customer"
			}
			if server_alive():
				upload_keserver(data, waktu, no_trans, bayar, kembali)
			else:
				cadangan_transaksi.append(data)
				simpan_semua(file_cadangan_transaksi, cadangan_transaksi)
				preview(bayar, kembali, no_trans, waktu)
				
				toko = profil_data[0]["nama"] if profil_data else "-"
				alamat = profil_data[0]["alamat"] if profil_data else "-"
				kontak = profil_data[0]["kontak"] if profil_data else "-"
				
				data_transaksi = {
					"toko": toko,
					"alamat": alamat,
					"kontak": kontak,
					"waktu": date_translator(waktu, bahasa_aplikasi),
					"operator": nama_operator(),
					"no_trans": no_trans,
					"isi_keranjang": render_keranjang_khusus(second_keranjang),
					"total": pretty_money(total),
					"bayar": pretty_money(bayar),
					"kembali": pretty_money(kembali)
				}
				cetak_struk(data_transaksi, no_trans)
				reset_gui()
		else:
			masuk, untung, total_poin, kena_pajak, status_pajak = 0, 0, 0, 0, 0
			for k in second_keranjang:
				id = k.get("id", "")
				cursor.execute("SELECT poin, jumlah FROM produk WHERE id_produk = ?", (id, ))
				jml = cursor.fetchone()
				cursor.execute("UPDATE produk SET jumlah = ? WHERE id_produk = ?", (jml["jumlah"] - k.get("qty_asli", 0), id))
				total_poin += jml["poin"] * k.get("qty_asli", 0)
				
				subtotal = k.get("subtotal_jual", 0)
				if termasuk_pajak.isChecked():
					harga = subtotal / (1 + persen_pajak / 100)
					status_pajak = 1 if termasuk_pajak.isChecked() else 0
					nilai_pajak = subtotal - harga
					kena_pajak += nilai_pajak
					cursor.execute("INSERT INTO riwayat_pajak (waktu, nama, pajak) VALUES (?, ?, ?)", (waktu, k.get("nama", ""), nilai_pajak))
				else:
					harga = subtotal
				masuk += harga
				untung += k.get("laba", 0)
			p = pembeli.text().strip().lower()
			np = nama_pembeli.currentText()
			npem = "-" if p == "customer" else np if not p else p
			cursor.execute("INSERT INTO riwayat_penjualan_campuran (waktu, total, total_laba, no_trans, operator, sumber, pembeli, bayar, kembali, data_belanja, kena_pajak, status_pajak) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (waktu, total, untung, no_trans, nama_operator(), komputer(), npem, bayar, kembali, json.dumps(second_keranjang), kena_pajak, status_pajak))

			cursor.execute("SELECT * FROM keuangan")
			j = cursor.fetchone()
			cursor.execute("UPDATE keuangan SET pemasukan = ?, keuntungan = ? WHERE id = ?", (j["pemasukan"] + masuk, j["keuntungan"] + untung, 1))
			
			pbeli = pembeli.text() if pembeli.text() != "" else nama_pembeli.currentText() if nama_pembeli.currentText() != "" else "Customer"
			if pbeli.lower() != "customer":
				n = pbeli.split()
				if len(n) < 2:
					mb.showerror("Gagal", "Input pembeli harus mempunyai nama dan kontak!")
					return
				nama = " ".join(n[:-1])
				kontak = n[-1]
				cursor.execute("SELECT * FROM customer WHERE nama = ? AND kontak = ?", (nama, kontak))
				cust = cursor.fetchone()
				if cust:
					cursor.execute("UPDATE customer SET poin = ? WHERE id = ?", (cust["poin"] + total_poin, cust["id"]))
				else:
					cursor.execute("INSERT INTO customer (nama, kontak, poin) VALUES (?, ?, ?)", (nama, kontak, total_poin))

			saldo_terakhir = j["saldo"]
			saldo_baru = saldo_terakhir + untung
			
			cursor.execute("""
			INSERT INTO riwayat_keuangan (waktu, jumlah, sumber,
			jenis, saldo_awal, saldo_akhir, pihak_terkait, keterangan,
			id_keuangan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (now_str(), untung, "Transaksi", "Keuntungan transaksi", saldo_terakhir, saldo_baru, "Customer", "Pemasukan dari keuntungan transaksi", datetime.now().strftime("%f")))
			
			conn.commit()
			preview(bayar, kembali, no_trans, waktu)
			
			toko = profil_data[0]["nama"] if profil_data else "-"
			alamat = profil_data[0]["alamat"] if profil_data else "-"
			kontak = profil_data[0]["kontak"] if profil_data else "-"
			
			data_transaksi = {
				"toko": toko,
				"alamat": alamat,
				"kontak": kontak,
				"waktu": date_translator(waktu, bahasa_aplikasi),
				"operator": nama_operator(),
				"no_trans": no_trans,
				"isi_keranjang": render_keranjang_khusus(second_keranjang),
				"total": pretty_money(total),
				"bayar": pretty_money(bayar),
				"kembali": pretty_money(kembali)
			}
			cetak_struk(data_transaksi, no_trans)
			reset_gui()

	def preview(b, k, n, w):
		nonlocal total
		for x in [lbl_struk, lbl_qr]:
			x.setText("")
		struk_fr.setVisible(True)
		profil = profil_data[0]
		if not second_keranjang:
			return
		nama_toko, alamat_toko, kontak_toko = profil["nama"], profil["alamat"], profil["kontak"]
		data_transaksi = {
			"toko": nama_toko,
			"alamat": alamat_toko,
			"kontak": kontak_toko,
			"waktu": w,
			"operator": nama_operator(),
			"no_trans": n,
			"isi_keranjang": render_keranjang_khusus(second_keranjang),
			"total": pretty_money(total),
			"bayar": pretty_money(b),
			"kembali": pretty_money(k)
		}
		path = os.path.join(folder_struk, "struk_1.txt")
		with open(path, "r") as f:
			template = f.read()
		if not template:
			QMB.warning(None, tr("Gagal"), "Format struk tidak tersedia. Silahkan buat format struk terlebih dahulu!")
			return safe_run(tampilkan_ringkasan)
			
		struk_final = template.format(**data_transaksi)
		lbl_struk.setText(struk_final)
			
		qr_struk = getData("status_qr")
		tipe, status = None, None
		for p in qr_struk:
			tipe, status = p["tipe"].lower(), p["status"]
		if status == 1:
			if tipe == "qr code":
				qr_teks = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=7, border=4)
				qr_teks.add_data(n)
				qr_teks.make(fit=True)
				img = qr_teks.make_image(fill_color="black", back_color="white").get_image()
				qt_img = ImageQt(img)
				pixmap = QPixmap.fromImage(qt_img)
				lbl_qr.setPixmap(pixmap)
				
			else:
				barcode_obj = barcode.get("code128", n, writer=ImageWriter())
				buffer = BytesIO()
				barcode_obj.write(buffer)
				img = Image.open(buffer)
				buffer.seek(0)
				pixmap = QPixmap()
				pixmap.loadFromData(buffer.read())
				lbl_qr.setPixmap(pixmap)
				
	calculate_transaction = 0	
	def reset_gui():
		global nomor_transaksi, bayar_separuh
		nonlocal calculate_transaction, sedang_proses, total, bayar, kembali

		calculate_transaction += 1
		if calculate_transaction >= 10:
			take_all_cache()
		sedang_proses = False
		label_kembali.setText(tr("Kembalian") + "\n" + pretty_money(0))
		bayar, total, kembali, bayar_separuh = 0, 0, 0, 0
		penyimpanan_undo.append(copy.deepcopy(keranjang))
		second_keranjang.clear()
		keranjang.clear()
		entry_barcode.setText("")
		cursor.execute("SELECT inisial_code FROM operator")
		id = cursor.fetchone()
		inisial_code = id["inisial_code"]
		nomor_transaksi = inisial_code[:3] + "_" + datetime.now().strftime("%f")
		
		safe_run(tampilkan_ringkasan)
		
	def set_struk():
		struk, qr = QLabel(), QLabel()
		struk.setStyleSheet(style_label_bold(font_size_normal))
		for x in [struk, qr]:
			struk_layout.addWidget(x, alignment=rata_atas)
		return struk, qr
		
	def simpan_transaksi():
		def set_layout():
			if not second_keranjang:
				QMB.critical(None, tr("Gagal"), tr("Belum ada data transaksi"))
				return
			clear_widgets(frame_cadangan)
			d = {
				"nama": entry(tr("Masukkan nama pembeli"), font_size_normal),
				"nope": entry(tr("Masukkan nomor telepon"), font_size_normal),
				"bayar": entry(tr("Masukkan jumlah dibayar"), font_size_normal),
				"simpan": button(tr("Simpan"), font_size_normal, bg),
				"batal": button(tr("Batal | Ctrl + B"), font_size_normal, bg)
			}
			for p in list(d.values()):
				cadangan_layout.addWidget(p, alignment=rata_atas)
			munculkan(frame_cadangan)
			return d
			
		def batalkan_simpan():
			clear_widgets(frame_cadangan)
			frame_cadangan.hide()
		
		def simpan():
			n = widgets["nama"].text().strip()
			np = widgets["nope"].text().strip()
			try:
				byr = float(widgets["bayar"].text().strip())
			except ValueError:
				QMB.critical(None, tr("Gagal"), tr("Masukkan jumlah dibayar dengan angka"))
				return
			if askyesno(tr("Konfirmasi"), f"{tr('Simpan data transaksi')} {n} sekarang?"):
				if koneksi["connect"] == 1:
					data = {
						"keranjang": keranjang,
						"nama": n + " " + np,
						"dibayar": byr,
						"status": "Belum lunas",
						"no": nomor_transaksi
					}
					upload_data("cadangkan_keranjang", data, tr("Data transaksi telah disimpan"))
				else:
					cursor.execute("SELECT * FROM cadangan_keranjang WHERE no = ?", (nomor_transaksi, ))
					cdg = cursor.fetchone()
					if cdg:
						cursor.execute("UPDATE cadangan_keranjang SET nama_pembeli = ?, jumlah_dibayar = ?, status = ?, keranjang = ? WHERE no = ?", (n + " " + np, cdg["jumlah_dibayar"] + byr, "Belum lunas", json.dumps(keranjang), nomor_transaksi))
					else:
						cursor.execute("INSERT INTO cadangan_keranjang (no, nama_pembeli, jumlah_dibayar, status, keranjang) VALUES (?, ?, ?, ?, ?)", (nomor_transaksi, n + " " + np, byr, "Belum lunas", json.dumps(keranjang)))
					conn.commit()
					QMB.information(None, tr("Berhasil"), tr("Data transaksi telah disimpan"))
				clear_widgets(frame_cadangan)
				frame_cadangan.hide()
			
		widgets = set_layout()
		widgets["simpan"].clicked.connect(simpan)
		widgets["batal"].clicked.connect(batalkan_simpan)
		widgets["nama"].setFocus()
		widgets["nama"].returnPressed.connect(widgets["nope"].setFocus)
		widgets["nope"].returnPressed.connect(widgets["bayar"].setFocus)
		widgets["bayar"].returnPressed.connect(simpan)
	
	def muat_transaksi():
		global bayar_separuh
		teks, _ = input_string(tr("Nama/Nomor transaksi"), tr("Masukkan nama dan nomor telepon atau nomor transaksi"))
		if teks:
			cadangan = getData("cadangan_keranjang")
			data = next((p for p in cadangan if p["no"] == teks or p["nama_pembeli"].lower() == teks.lower()), None)
			if not data:
				QMB.critical(None, tr("Tidak ditemukan"), tr("Data tidak ditemukan"))
				return
			dict_data = {
				"no": data["no"],
				"nama": data["nama_pembeli"],
				"bayar": pretty_money(data["jumlah_dibayar"]),
				"status": data["status"],
				"total": pretty_money(sum((p.get("harga", 0) * p.get("qty", 0)) for p in json.loads(data["keranjang"]))),
				"item": format_unit(len(json.loads(data["keranjang"])), "unit"),
				"btn": button(tr("Tambahkan ke keranjang"), font_size_normal, bg)
			}
			def tambah_keranjang():
				if data["status"].lower() == "lunas":
					QMB.warning(None, tr("Gagal"), f"{tr('Transaksi dengan nomor transaksi')} {data['no']} {tr('telah dilunasi')}")
					return
				global bayar_separuh
				bayar_separuh = data["jumlah_dibayar"]
				if keranjang:
					penyimpanan_undo.append(copy.deepcopy(keranjang))
				keranjang.clear()
				keranjang.extend(json.loads(data["keranjang"]))
				safe_run(tampilkan_ringkasan)
				frame_cadangan.hide()
				
			clear_widgets(frame_cadangan)
			fr = QFrame()
			layout = QGridLayout(fr)
			for i, (a, b) in enumerate(list(dict_data.items())[:-1]):
				label1, label2, label3 = QLabel(a.upper()), QLabel(":"), QLabel(b)
				for c in [label1, label2, label3]:
					c.setStyleSheet(style_label_bold(font_size_normal))
				layout.addWidget(label1, i, 0, alignment=rata_kiri)
				layout.addWidget(label2, i, 1, alignment=rata_kiri)
				layout.addWidget(label3, i, 2, alignment=rata_kiri)
			for x in [fr, dict_data["btn"]]:
				cadangan_layout.addWidget(x)
			frame_cadangan.show()
			dict_data["btn"].clicked.connect(tambah_keranjang)
			
	def show_produk():
		def prepare_layout():
			for i, p in enumerate([frame_cadangan, struk_fr, listbox, kiri, kanan]):
				p.hide() if i != 0 else munculkan(p)
			clear_widgets(frame_cadangan)
			tabel, model = table_maker(["Id produk", "Barcode", "Nama", "Jumlah", "Harga jual"])
			cari = entry(tr("Cari cepat..."), font_size_normal)
			add = button(tr("Tambahkan keranjang"), font_size_normal, bg)
			add.setFixedWidth(200)
			for p in [cari, tabel, add]:
				cadangan_layout.addWidget(p)
			cari.setFocus()
			return tabel, model, cari, add
			
		def set_data(teks=""):
			model.removeRows(0, model.rowCount())
			for p in produk:
				nama, barcode = p["nama"], p["barcode"]
				if teks.lower() in nama.lower() or teks in barcode:
					model.appendRow([
						QStandardItem(p["id_produk"]),
						QStandardItem(barcode),
						QStandardItem(nama),
						QStandardItem(format_unit(p["jumlah"], p["satuan_jual"])),
						QStandardItem(pretty_money(p["harga_jual"]))
					])
					
		def add_keranjang():
			data = take_data(tabel, model)
			if not data:
				return
			qty, _= input_int("Qty", tr("Masukkan jumlah qty"))
			if qty == 0:
				return
			for k in keranjang:
				if k.get("id", "") == data[0]:
					k["qty"] += qty
					break
			else:
				keranjang.append({
					"id": data[0],
					"barcode": data[1],
					"qty": qty,
					"harga": float(data[-1].replace(frr[0], "").replace(frr[2], "").replace(frr[3], ".")),
					"nama": data[2]
				})
			safe_run(tampilkan_ringkasan)
						
		produk = getData("produk")	
		tabel, model, cari, add = prepare_layout()
		cari.textChanged.connect(lambda: set_data(cari.text().strip()))
		set_data()
		cari.returnPressed.connect(lambda: go_focus_on_first_row(tabel, 0))
		tabel.activated.connect(add_keranjang)
		add.clicked.connect(add_keranjang)
		
	def refresh_biasa():
		for i, p in enumerate([frame_cadangan, struk_fr, listbox, kiri, kanan]):
			p.hide() if i != 3 else munculkan(p)
		entry_barcode.setFocus()
		
	def simpan_transaksi_sementara():
		if not keranjang:
			QMB.warning(None, tr("Gagal"), tr("Belum ada data transaksi"))
			return
		pengenal, _ = input_string(tr("Pengenal"), tr("Masukkan pengenal singkat pembeli (bisa nama atau ciri khusus)"))
		if not pengenal:
			return
		penyimpanan_sementara.append({
			"pengenal": pengenal,
			"data": copy.deepcopy(keranjang)
		})
		penyimpanan_undo.append(copy.deepcopy(keranjang))
		keranjang.clear()
		safe_run(tampilkan_ringkasan)
		
	def muat_simpanan_sementara_transaksi():
		for i, p in enumerate([frame_cadangan, struk_fr, listbox, kiri, kanan]):
			p.hide() if i in [1,2,4] else munculkan(p)
		clear_widgets(frame_cadangan)
		list_pengenal = [d.get("pengenal", "") for d in penyimpanan_sementara]
		combo = combobox(font_size_normal, list_pengenal)
		btn = button(tr("Tambahkan ke keranjang"), font_size_normal, bg)
		for p in [combo, btn]:
			cadangan_layout.addWidget(p)
		def muat():
			pengenal = combo.currentText()
			data = next((p["data"] for p in penyimpanan_sementara if p["pengenal"] == pengenal), [])
			if data:
				if keranjang:
					penyimpanan_undo.append(copy.deepcopy(keranjang))
				keranjang.clear()
				keranjang.extend(data)
				safe_run(tampilkan_ringkasan)
				
		btn.clicked.connect(muat)
	
	def buat_nota():
		if not second_keranjang:
			QMB.warning(None, tr("Gagal"), tr("Belum ada data transaksi"))
			return
		for i, p in enumerate([frame_cadangan, struk_fr, listbox, kiri, kanan]):
			p.hide() if i in [1, 2, 4] else munculkan(p)
			
		def prepare_entries():
			return {
				"pembeli": entry(tr("Pembeli..."), font_size_normal),
				"nama": entry(tr("Nama pembeli (personal)..."), font_size_normal),
				"alamat": entry(tr("Alamat pembeli..."), font_size_normal),
				"btn": button(tr("Buat nota"), font_size_normal, bg),
				"batal": button(tr("Batal"), font_size_normal, bg)
			}
			
		def set_on_layouts():
			clear_widgets(frame_cadangan)
			for p in list(widgets.values()):
				cadangan_layout.addWidget(p)
				
		def batalkan():
			clear_widgets(frame_cadangan)
			safe_run(tampilkan_ringkasan)
			
		def get_result():
			return {
				"p": widgets["pembeli"].text().strip(),
				"np": widgets["nama"].text().strip(),
				"a": widgets["alamat"].text().strip()
			}
			
		def simpan_pdf():
			hasil = get_result()
			pembeli = hasil["p"]
			nama_pembeli = hasil["np"]
			alamat = hasil["a"]
			kena_pajak = cek_pajak(total, termasuk_pajak.isChecked(), persen_pajak)
			kp = total - kena_pajak
			data = {
				"p": pembeli,
				"np": nama_pembeli,
				"a": alamat,
				"no": nomor_transaksi,
				"sp": termasuk_pajak.isChecked(),
				"pjk": persen_pajak,
				"kp": kp 
			}
			buat_nota_pdf(data, second_keranjang)
			menu_bayar()
				
		widgets = prepare_entries()
		set_on_layouts()
		widgets["batal"].clicked.connect(batalkan)
		widgets["btn"].clicked.connect(simpan_pdf)
			
	def set_bottom_frame_widgets():
		widgets = {
			"produk": button("Produk | Ctrl+P", font_size_normal, "transparent"),
			"refresh": button("Refresh | Ctrl+R", font_size_normal, "transparent"),
			"refresh_keranjang": button(tr("Refresh keranjang | Shift+Ctrl+R"), font_size_normal, "transparent"),
			"simpan": button(tr("Simpan transaksi | Ctrl+S"), font_size_normal, "transparent"),
			"muat": button(tr("Muat transaksi | Ctrl+L"), font_size_normal, "transparent"),
			"simpan_sementara": button(tr("Simpan sementara | Ctrl+Shift+S"), font_size_normal, "transparent"),
			"muat_sementara": button(tr("Muat transaksi cadangan | Ctrl+Shift+L"), font_size_normal, "transparent"),
			"nota": button(tr("Buat nota | Ctrl+N"), font_size_normal, "transparent")
		}
		for i, p in enumerate(list(widgets.values())):
			baris, kolom = i // 4, i % 4
			bawah_layout.addWidget(p, baris, kolom, alignment=rata_kiri)
		widgets["produk"].clicked.connect(show_produk)
		widgets["simpan"].clicked.connect(simpan_transaksi)
		widgets["refresh"].clicked.connect(refresh_biasa)
		widgets["refresh_keranjang"].clicked.connect(refresh_transaksi)
		widgets["muat"].clicked.connect(muat_transaksi)
		widgets["simpan_sementara"].clicked.connect(simpan_transaksi_sementara)
		widgets["muat_sementara"].clicked.connect(muat_simpanan_sementara_transaksi)
		widgets["nota"].clicked.connect(buat_nota)
	
	def delete_item_from_keranjang():
		data = take_data(tabel, model)
		if not data:
			return
		for k in keranjang[:]:
			if k.get("id", "") == data[0]:
				keranjang.remove(k)
				break
		safe_run(tampilkan_ringkasan)
		
	def make_shortcuts():
		delete = QShortcut(QKeySequence("F4"), window)
		refresh_b = QShortcut(QKeySequence("Ctrl+R"), window)
		refresh_total = QShortcut(QKeySequence("Shift+Ctrl+R"), window)
		simpan_tr = QShortcut(QKeySequence("Ctrl+S"), window)
		muat_tr = QShortcut(QKeySequence("Ctrl+L"), window)
		simpan_sementara = QShortcut(QKeySequence("Ctrl+Shift+S"), window)
		muat_sementara = QShortcut(QKeySequence("Ctrl+Shift+L"), window)
		nota = QShortcut(QKeySequence("Ctrl+N"), window)
		produk = QShortcut(QKeySequence("Ctrl+P"), window)
		focus_on_table = QShortcut(QKeySequence("Ctrl+F"), window)
		
		delete.activated.connect(lambda: safe_run(delete_item_from_keranjang))
		refresh_b.activated.connect(lambda: safe_run(refresh_biasa))
		refresh_total.activated.connect(lambda: safe_run(refresh_transaksi))
		simpan_tr.activated.connect(lambda: safe_run(simpan_transaksi))
		muat_tr.activated.connect(lambda: safe_run(muat_transaksi))
		simpan_sementara.activated.connect(lambda: safe_run(simpan_transaksi_sementara))
		muat_sementara.activated.connect(lambda: safe_run(muat_simpanan_sementara_transaksi))
		nota.activated.connect(lambda: safe_run(buat_nota))
		produk.activated.connect(lambda: safe_run(show_produk))
		focus_on_table.activated.connect(lambda: safe_run(go_focus_on_first_row))
		
		for p in [
			delete,
			refresh_b,
			refresh_total,
			simpan_tr,
			muat_tr,
			simpan_sementara,
			muat_sementara,
			nota,
			produk,
			focus_on_table
		]:
			shortcuts.append(p)
				
	global pjk, nomor_transaksi
	second_keranjang = []
	frr = format_uang_app		
	hide_frames()
	total, kembali, bayar = 0, 0, 0
	f2_kiri, f2_atas, f2_bawah = make_frame_on_f2()
	termasuk_pajak, cetak_qr, btn_opr = set_f2_kiri_widgets()
	entry_barcode, undo, redo, refresh, back = set_atas_kanan_widgets()
	label_harga, label_kembali = set_price_and_change()
	frame_cadangan, struk_fr, listbox, kiri, kanan, bawah_layout = set_f3_widgets()
	kiri_layout, kanan_layout, struk_layout, cadangan_layout = set_kiri_and_kanan_layout()
	tabel, model = safe_run(set_tabel)
	lbl_struk, lbl_qr = safe_run(set_struk)
	persen_pajak, status_pajak, status_qr = safe_run(set_input)
	label_bayar, entry_uang, nama_pembeli, pembeli, btn_selesai = safe_run(set_kanan_hiding_widgets)
	safe_run(set_bottom_frame_widgets)
	make_shortcuts()
	
	termasuk_pajak.toggled.connect(set_pajak)
	cetak_qr.toggled.connect(set_qr)
	entry_barcode.returnPressed.connect(tombol_enter)
	entry_barcode.textChanged.connect(update_list)
	listbox.itemClicked.connect(on_klik)
	QWidget.setTabOrder(entry_barcode, listbox)
	model.dataChanged.connect(proses_data)
	entry_uang.textChanged.connect(lambda: format_rupiah(entry_uang))
	entry_uang.textChanged.connect(hitung_kembalian)
	entry_uang.returnPressed.connect(lambda: safe_run(update_stok))
	btn_selesai.clicked.connect(lambda: safe_run(update_stok))
	safe_run(tampilkan_ringkasan)

def pdf_pesanan(p, b, id):
	spinner = set_spinner(window)
	global pjk, profil_data
	if not all([p, b]):
		return
	nama_toko = profil_data[0]["nama"] if profil_data else ""
	alamat_toko = profil_data[0]["alamat"] if profil_data else ""
	kontak_toko = profil_data[0]["kontak"] if profil_data else ""
	waktu = datetime.now().strftime("%d/%m/%Y")
	
	format_nota = getData("pengaturan_nota")
	if not format_nota:
		spinner.deleteLater()
		QMB.warning(None, tr("Gagal"), tr("Atur format terlebih dahulu!"))
		return
	fr = format_nota[0]
	judul = fr["judul"]
	catatan = fr["catatan"]
	penerima = fr["penerima"]
	penerbit = fr["penerbit"]
	
	path = BytesIO()
	doc = SimpleDocTemplate(path)
	c = []
	
	c.append(Paragraph(judul, ParagraphStyle(name="judul", fontName="Helvetica-bold", fontSize=12, textColor=colors.black, alignment=TA_CENTER, borderPadding=10, borderWidth=1, borderRadius=5, borderColor=colors.steelblue)))
	c.append(Spacer(1, 15))
	
	data1 = [
		[Paragraph(nama_toko, style_judul), None, mp(f"No: {p.get('no_trans', '')}")],
		[mp(alamat_toko), None, mp(f"Tgl: {waktu}")],
		[mp(kontak_toko), None, None]
	]
	tabel1 = Table(data1, colWidths=[60*mm, 50*mm, 50*mm])
	tabel1.setStyle(TableStyle([
		("SPAN", (0,1), (1,1))
	]))
	c.append(tabel1)
	c.append(Spacer(1,15))
	
	data2 = [
		[mp("Pembeli"), mp(":"), mp(p.get("nama", ""))],
		[mp("Alamat pembeli"), mp(":"), mp(p.get("alamat", ""))],
		[mp("Telp/WA"), mp(":"), mp(p.get("kontak", ""))],
		[mp("Email"), mp(":"), mp(p.get("email", ""))]
	]
	tabel2 = Table(data2, colWidths=[35*mm, 5*mm, 120*mm])
	tabel2.setStyle(TableStyle([
		("BOX", (0,0), (-1,-1), 0.5, colors.black)
	]))
	c.append(tabel2)
	c.append(Spacer(1, 15))
	
	data3 = [["NO", "ID", "NAMA", "QTY", "HARGA", "SUBTOTAL"]]
	total = 0
	for i, item in enumerate(b):
		subtotal = cek_pajak(item.get("subtotal_jual", 0), pjk[0]["aktif"], pjk[0]["persen"])
		total += subtotal
		data3.append([
			mp(str(i+1) + "."),
			mp(item.get("id", "")),
			mp(item.get("nama", "")),
			mp(str(item.get("qty", 0))),
			mp(pretty_money(cek_pajak(item.get("harga_jual", 0), pjk[0]["aktif"], pjk[0]["persen"]))),
			mp(pretty_money(subtotal))
		])
	total_keseluruhan = float(total + p.get("kena_pajak", 0))

	t = Terbilang()
	t.parse(str(total_keseluruhan))
	terb = t.getresult()
	data3.append([None, None, None, None, "Diskon", ""])
	data3.append([None, None, None, None, "EBT", pretty_money(total)])
	data3.append([None, None, None, None, "PPn", pretty_money(p.get("kena_pajak", 0))])
	data3.append([mp(f"Terbilang: {terb} rupiah"), None, None, None, "TOTAL", pretty_money(total_keseluruhan)])

	tabel3 = Table(data3, colWidths=[10*mm, 20*mm, 40*mm, 20*mm, 35*mm, 35*mm])
	tabel_tabel = zebra_style(tabel3, data3)
	c.append(tabel_tabel)
	c.append(Spacer(1, 15))
	
	c.append(mp(tr("Catatan penjual")))
	data_catatan = [[catatan]]
	tabel_catatan = Table(data_catatan, colWidths=[160*mm])
	c.append(tabel_catatan)
	c.append(Spacer(1, 15))
	
	c.append(mp(tr("Catatan pembeli")))
	c.append(mp("• " + p.get("catatan", "")))
	c.append(Spacer(1,20))
	if p.get("bayar", "").lower() != "cash on delivery (cod)":
		media_bayar = getData("media_bayar")
		info_bayar = next((inf for inf in media_bayar if inf["bank"].lower() == p.get("bayar", "").lower()), None)
		if info_bayar:
			nama_bank = info_bayar["bank"]
			pemilik = info_bayar["nama_pemilik"]
			name_info = nama_bank + pemilik + ".jpeg"
			try:
				res = requests.get(f"{SERVER_URL}/lihat_gambar_rekening", params={"name": name_info}, timeout=5) #request berhasil
				if res.status_code != 200:
					return
			except Exception:
				return
			
			img_data = BytesIO(res.content)
			tabel_rekening = [
			    [Paragraph("BANK", style_jago), Paragraph(":", style_jago), Paragraph(nama_bank, style_jago)],
			    [Paragraph("NAMA", style_jago), Paragraph(":", style_jago), Paragraph(pemilik, style_jago)],
			    [Paragraph("NOMOR REKENING", style_jago), Paragraph(":", style_jago), Paragraph(info_bayar["nomor_rekening"], style_jago)]
			]
			tabel_info_rekening = Table(tabel_rekening, colWidths=[45*mm, 5*mm, 50*mm])
			
			img = RLImage(img_data, width=60*mm, height=60*mm)
			img.hAlign = "center"
			
			lengkap = [[tabel_info_rekening, img]]
			tabel_lengkap = Table(lengkap, colWidths=[100*mm, 60*mm])
			tabel_lengkap.setStyle(TableStyle([
				("VALIGN", (0,0), (-1,-1), "TOP")
			]))
			c.append(tabel_lengkap)
			
	
	c.append(Spacer(1, 20))
	data4 = [
		[penerima, penerbit]
	]
	tabel4 = Table(data4, colWidths=[80*mm, 80*mm])
	tabel4.setStyle(TableStyle([
		("ALIGN", (0,0), (-1,0), "CENTER")
	]))
	c.append(tabel4)
	doc.build(c)
	spinner.deleteLater()
	if askyesno(tr("Berhasil"), tr("Nota telah dibuat, simpan sekarang?")):
		spinner = set_spinner(window)
		path.seek(0)
		files = {
			"file": ("Nota_" + p.get("nama", "") + "_" + str(id) + ".pdf", path, "application/pdf")
		}
		data = {
			"id": id,
			"data": p,
			"keranjang": b
		}
		info = {}
		try:
			res = requests.post(f"{SERVER_URL}/simpan_nota", files=files)
			if res.status_code == 200:
				info["status"] = "Berhasil"
				info["pesan"] = "Nota telah disimpan!"
			else:
				info["status"] = "Gagal"
				info["pesan"] = str(res.status_code)
		except Exception as e:
			info["status"] = "Error"
			info["pesan"] = str(e)
		
		spinner.deleteLater()
		upload_data("update_status_permintaan", data, tr("Status pesanan telah diupdate"))
		QMB.information(None, tr(info["status"]), tr(info["pesan"]))
		
def buat_nota_pdf(p, k):
	global pjk, profil_data
	if not all([p, k]):
		return
	nama_toko = profil_data[0]["nama"] if profil_data else ""
	alamat_toko = profil_data[0]["alamat"] if profil_data else ""
	kontak_toko = profil_data[0]["kontak"] if profil_data else ""
	waktu = datetime.now().strftime("%d/%m/%Y")
	
	pembeli = p.get("p", "")
	nama_pembeli = p.get("np", "")
	alamat_pembeli = p.get("a", "")
	pjk_value = p.get("sp", 0)
	pjk_persen = p.get("pjk", 0)
	kenapajak = p.get("kp", 0)
	no_trans = p.get("no", 0)
	
	format_nota = getData("pengaturan_nota")
	if not format_nota:
		QMB.warning(None, tr("Gagal"), tr("Atur format terlebih dahulu!"))
		return
	fr = format_nota[0]
	judul = fr["judul"]
	catatan = fr["catatan"]
	penerima = fr["penerima"]
	penerbit = fr["penerbit"]

	path = choose_save_path(f"Nota {no_trans}.pdf")
	if not path:
		return
	doc = SimpleDocTemplate(path)
	content = []
	style_biasa = ParagraphStyle(name="biasa", fontName="Helvetica", alignment=TA_LEFT)
	style_judul = ParagraphStyle(name="namaToko", fontName="Helvetica-Bold", fontSize=12, textColor=colors.green, alignment=TA_LEFT)
	
	content.append(Paragraph(judul, ParagraphStyle(name="judul", fontName="Helvetica-bold", fontSize=12, textColor=colors.black, alignment=TA_CENTER, borderPadding=10, borderWidth=1, borderRadius=5, borderColor=colors.steelblue)))
	content.append(Spacer(1, 15))
	data1 = [
		[Paragraph(nama_toko, style_judul), None, Paragraph(f"No: {no_trans}", style_biasa)],
		[Paragraph(alamat_toko, style_biasa), None, Paragraph(f"Tgl: {waktu}", style_biasa)],
		[Paragraph(kontak_toko, style_biasa), None, None]
	]
	tabel1 = Table(data1, colWidths=[60*mm, 50*mm, 50*mm])
	tabel1.setStyle(TableStyle([
		("SPAN", (0,1), (1,1))
	]))
	content.append(tabel1)
	content.append(Spacer(1,15))
	data2 = [
		[Paragraph("Pembeli", style_biasa), Paragraph(":", style_biasa), Paragraph(pembeli, style_biasa)],
		[Paragraph("Nama pembeli", style_biasa), Paragraph(":", style_biasa), Paragraph(nama_pembeli, style_biasa)],
		[Paragraph("Alamat pembeli", style_biasa), Paragraph(":", style_biasa), Paragraph(alamat_pembeli, style_biasa)]
	]
	tabel2 = Table(data2, colWidths=[35*mm, 5*mm, 120*mm])
	tabel2.setStyle(TableStyle([
		("BOX", (0,0), (-1,-1), 0.5, colors.black)
	]))
	content.append(tabel2)
	data3 = [["NO", "ID", "NAMA", "QTY", "HARGA", "SUBTOTAL"]]
	total = 0
	for i, p in enumerate(k):
		subtotal = cek_pajak(p.get("subtotal_jual", 0), pjk_value, pjk_persen)
		total += subtotal
		baris = [
			str(i+1) + ".",
			p.get("id", ""),
			p.get("nama", ""),
			p.get("qty", 0),
			pretty_money(cek_pajak(p.get("harga_jual", 0), pjk_value, pjk_persen)),
			pretty_money(subtotal)
		]
		data3.append(baris)
	total_keseluruhan = float(total + kenapajak)

	t = Terbilang()
	t.parse(str(total_keseluruhan))
	terb = t.getresult()
	data3.append([None, None, None, None, "Diskon", ""])
	data3.append([None, None, None, None, "EBT", pretty_money(total)])
	data3.append([None, None, None, None, "PPn", pretty_money(kenapajak)])
	data3.append([Paragraph(f"Terbilang: {terb} rupiah", style_biasa), None, None, None, "TOTAL", pretty_money(total_keseluruhan)])

	tabel3 = Table(data3, colWidths=[10*mm, 20*mm, 55*mm, 25*mm, 25*mm, 25*mm])
	tabel_tabel = zebra_style(tabel3, data3)
	content.append(tabel_tabel)
	content.append(Spacer(1, 15))
	data_catatan = [[catatan]]
	tabel_catatan = Table(data_catatan, colWidths=[160*mm])
	content.append(tabel_catatan)
	content.append(Spacer(1, 15))
	data4 = [
		[penerima, penerbit]
	]
	tabel4 = Table(data4, colWidths=[80*mm, 80*mm])
	tabel4.setStyle(TableStyle([
		("ALIGN", (0,0), (-1,0), "CENTER")
	]))
	content.append(tabel4)
	doc.build(content)
	QMB.information(None, tr("Berhasil"), f"{tr('File pdf telah disimpan kedalam')} {path}")

bayar_separuh = 0								
def transaksi():
	def middle_widget():
		lbl = QLabel()
		lbl.setStyleSheet(style_label_bold(font_size_normal))
		return {
			"waktu": combobox(font_size_normal, [tr("Terbaru"), tr("Terlama")]),
			"label": lbl
		}
		
	def up_widget():
		tgl = make_date()
		tgl.setCalendarPopup(True)
		tgl.setDate(QDate.currentDate())
		return {
			"cari": entry(tr("Masukkan nomor transaksi..."), font_size_normal),
			"tanggal": tgl,
			"lihat": button(tr("Lihat data"), font_size_normal, bg),
			"periode": combobox(font_size_normal, [tr("Semua periode"), tr("Bulan ini"), tr("Minggu ini"), tr("Hari ini")]),
			"operator": combobox(font_size_normal, [tr("Semua operator")] + list({p["nama"] for p in user_data})),
			"filter": button(tr("Filter"), font_size_normal, bg)
		}
			
	def layout_setup():
		for x in [f3, f2]:
			clear_widgets(x)
		fr1, fr2, fr3 = QFrame(), QFrame(), QFrame()
		for i, x in enumerate([fr1, fr2, fr3]):
			f3_layout.addWidget(x)
		return QHBoxLayout(fr1), QHBoxLayout(fr2), fr3
	
	def setup_up_widget():
		w = atas_widget
		for x in list(w.values()):
			atas.addWidget(x)
		w["cari"].setFocus()
	
	def setup_middle_widget():
		w = tengah_widget
		for i, x in enumerate(list(w.values())):
			tengah.addWidget(x, alignment=rata_kiri if i == 0 else rata_kanan)
			
	def collect_data_from_calendar():
		data_riwayat.clear()
		teks = datetime.strptime(atas_widget["tanggal"].text().strip(), "%d/%m/%y").date()
		try:
			for p in riwayat_jual:
				waktu = parse_date(p["waktu"])
				time_stamp = waktu.date()
				if time_stamp == teks:
					data_riwayat.append(p)
		except Exception as e:
			QMB.critical(None, "", str(e))
		
	def detail_transaksi(no_trans):
		label_judul_transaksi = QLabel(f"{tr('TABEL DATA TRANSAKSI NOMOR')} {no_trans}")
		label_judul_belanja = QLabel(tr('TABEL DATA PRODUK'))
		data = next((p for p in riwayat_jual if p["no_trans"].lower() == no_trans.lower()), None)
		data_belanja = json.loads(data["data_belanja"]) if data else []
		tabel, model = table_maker([tr("Aspek"), tr("Nilai"), tr("Aspek"), tr("Nilai")])
		info_data = [
			("Nomor transaksi", data["no_trans"], "Waktu", date_translator(data["waktu"], bahasa_aplikasi)),
			("Total belanja", pretty_money(data["total"]), "Total keuntungan", pretty_money(data["total_laba"])),
			("Operator", data["operator"], "Sumber", data["sumber"]),
			("Pembeli", data["pembeli"], "Bayar", pretty_money(data["bayar"])),
			("Kembali", pretty_money(data["kembali"]), "Status pajak", "Termasuk pajak" if data["status_pajak"] == 1 else "Tidak termasuk pajak"),
			("Nilai pajak", pretty_money(data["kena_pajak"]), "", "")
		]
		for a, b, c, d in info_data:
			model.appendRow([
				QStandardItem(str(a.upper())),
				QStandardItem(str(b)),
				QStandardItem(str(c.upper())),
				QStandardItem(str(d))
			])
		clear_widgets(f3)
		for x in [label_judul_transaksi, label_judul_belanja]:
			x.setStyleSheet(style_label_bold(font_size_normal))
		f3_layout.addWidget(label_judul_transaksi)	
		f3_layout.addWidget(tabel)
		f3_layout.addWidget(label_judul_belanja)
		for p in data_belanja:
			tab, mod = table_maker([tr("Aspek"), tr("Nilai"), tr("Aspek"), tr("Nilai")])
			info = [
				("id produk", p.get("id", ""), "barcode", p.get("barcode", "")),
				("nama", p.get("nama", ""), "qty", p.get("qty", 0)),
				("qty asli", p.get("qty_asli", 0), "harga modal", pretty_money(p.get("harga_modal", 0))),
				("harga jual", pretty_money(p.get("harga_jual", 0)), "subtotal modal", pretty_money(p.get("subtotal_modal", 0))),
				("subtotal jual", pretty_money(p.get("subtotal_jual", 0)), "keuntungan", pretty_money(p.get("laba", 0)))
			]
			for a, b, c, d in info:
				mod.appendRow([
					QStandardItem(str(a.upper())),
					QStandardItem(str(b)),
					QStandardItem(str(c.upper())),
					QStandardItem(str(d))
				])
			f3_layout.addWidget(tab)
	
	def cetak_struk_transaksi(no_trans):
		nama = f"STRUK_ONLINECAMPURANTRX-{no_trans}.txt" if koneksi["connect"] == 1 else f"STRUK_OFFLINECAMPURANTRX-{no_trans}.txt"
		data = next((p for p in riwayat_jual if p["no_trans"] == no_trans), None)
		data_belanja = json.loads(data["data_belanja"])
		if not data and not data_belanja:
			return
		profil = getData("profil")
		prf = profil[0] if profil else {}
		toko = prf["nama"]
		alamat = prf["alamat"]
		kontak = prf["kontak"]
		
		str_for_keranjang = ""
		for k in data_belanja:
			str_for_keranjang += f"{k['nama']}\n{k['qty']} x {pretty_money(k['harga_jual'])} = {pretty_money(k['subtotal_jual'])}\n"
	
		if data:
			data_transaksi = {
				"toko": toko,
				"alamat": alamat,
				"kontak": kontak,
				"waktu": date_translator(now_str(), bahasa_aplikasi),
				"no_trans": no_trans,
				"operator": nama_operator(),
				"isi_keranjang": str_for_keranjang,
				"bayar": pretty_money(data["bayar"]),
				"kembali": pretty_money(data["kembali"]),
				"total": pretty_money(data["total"])
			}
			path = os.path.join(folder_struk, "struk_1.txt")
			if not os.path.exists(path):
				QMB.critical(None, tr("Kosong"), tr("Template struk tidak tersedia"))
				return
			with open(path, "r") as f:
				template = f.read()
			struk_final = template.format(**data_transaksi)
			clear_widgets(f3)
			label_struk = QLabel(struk_final)
			label_struk.setStyleSheet(style_label_bold(font_size_normal))
			btn_cetak = label_photo(tr("Cetak"), resource_path("Pictures/ddd.png"), icon_size)
			btn_cetak.setStyleSheet(style_button(bg, font_size_normal))
			btn_cetak.clicked.connect(lambda: cetak_struk(data_transaksi, no_trans.upper()))
			for x in [label_struk, btn_cetak]:
				f3_layout.addWidget(x)
				
	def preparation_for_note(no_trans):
		data = None
		krg = None
		for p in riwayat_jual:
			if p["no_trans"].lower() == no_trans.lower():
				krg = json.loads(p["data_belanja"])
				data = {"p": "", "np": p["pembeli"], "a": "", "sp": p["status_pajak"], "pjk": pjk[0]['persen'] if pjk else 0, "kp": p["kena_pajak"], "no": p["no_trans"]}
				break
		buat_nota_pdf(data, krg)
		
	def hapus_riwayat_jual(no_trans):
		if askyesno(tr("Konfirmasi"), f"{tr('Hapus transaksi')} {no_trans} {tr('sekarang')}?"):
			if koneksi["connect"] == 1:
				data = {"no": no_trans}
				upload_data("hapus_transaksi_tertentu", data, f"{tr('Transaksi')} {no_trans} {tr('telah dihapus')}!")
			else:
				cursor.execute("DELETE FROM riwayat_penjualan_campuran WHERE no_trans = ?", (no_trans, ))
				conn.commit()
				QMB.information(None, tr("Berhasil"), f"{tr('Transaksi')} {no_trans} {tr('telah dihapus')}!")
			transaksi()
			
	def set_layout_for_bawah():
		clear_widgets(bawah)
		at, ba = QFrame(), QFrame()
		ala, bala = QVBoxLayout(at), QHBoxLayout(ba)
		for a in [at, ba]:
			bawah_layout.addWidget(a)
		return at, ala, bala
		
	def bala_widgets():
		d = {
			"prev": QPushButton(tr("« Sebelumnya")),
			"lbl": QLineEdit(),
			"next": QPushButton(tr("Selanjutnya »"))
		}
		for a in list(d.values()):
			set_expanding(a, fix, fix)
			a.setStyleSheet(f"""
				QPushButton {{
					background-color: {bg};
					font-size: {font_size_normal}px;
					padding: 10px;
					border: none;
					border-radius: 2px;
				}}
				QPushButton:pressed {{
					background-color: black;
					color: white;
				}}
				QLineEdit {{
					background-color: transparent;
					padding: 10px;
					border: 1px solid black;
					border-radius: 2px;
				}}""")
			bala.addWidget(a)
		d["prev"].clicked.connect(do_prev)
		d["next"].clicked.connect(do_next)
		d["lbl"].setFixedWidth(100)
		return d["lbl"]
		
	def write_data_now(teks=""):
		if not data_riwayat_split:
			return
		entry_index.setText(str(count_show + 1))
		data_from_newest = sorted(data_riwayat_split[count_show], key=lambda x: parse_date(x["waktu"]), reverse=True)
		data_from_oldest = sorted(data_riwayat_split[count_show], key=lambda x: parse_date(x["waktu"]), reverse=False)
		urut = tengah_widget["waktu"].currentText()
		data_filter = data_from_newest if urut.lower() in ["newest", "terbaru"] else data_from_oldest
		if not data_filter:
			return
		tengah_widget["label"].setText(f"{tr('Menampilkan sebanyak')} {len(data_filter)} data")		
		for i, p in enumerate(data_filter):
			no_trans = p["no_trans"]
			waktu = date_translator(p["waktu"], bahasa_aplikasi)
			operator = p["operator"]
			if teks.lower() in no_trans.lower() or teks.lower() in waktu.lower() or teks.lower() in operator.lower():
				frame, kiri, tengah, kanan = QFrame(), QFrame(), QFrame(), QFrame()
				frame.setObjectName("telur")
				frame.setStyleSheet(f"""
					QFrame#telur {{
						background-color: transparent;
						border: 1px solid {bg};
						border-radius: 2px;
						padding: 5px;
					}}""")
				frame_layout, kiri_layout, tengah_layout, kanan_layout = QVBoxLayout(frame, alignment=rata_atas), QHBoxLayout(kiri, alignment=rata_kiri), QHBoxLayout(tengah, alignment=rata_atas), QHBoxLayout(kanan, alignment=rata_kiri)
				frame_layout.setContentsMargins(0,0,0,0)
				frame_layout.setSpacing(0)
				for i, x in enumerate([kiri, tengah, kanan]):
					frame_layout.addWidget(x)
					QApplication.processEvents()
							
				ala.addWidget(frame)
				tabel, model = table_maker(["Nama", "Qty", "Harga", "Subtotal"])
				tengah_layout.addWidget(tabel, alignment=rata_atas)
				munculkan(tabel)
				data_belanja = json.loads(p["data_belanja"])
				
				for x in data_belanja:
					model.appendRow([
						QStandardItem(x.get("nama", "")),
						QStandardItem(str(x.get("qty", 0))),
						QStandardItem(pretty_money(x.get("harga_jual", 0))),
						QStandardItem(pretty_money(x.get("subtotal_jual", 0)))
					])
				label_nomor = QLabel(tr("Nomor transaksi") + ": " + no_trans)
				label_total = QLabel(tr("Total belanja") + ": " + pretty_money(p["total"]))
				for x in [label_nomor, label_total]:
					x.setStyleSheet(style_label_bold(font_size_normal))
				label_tgl = label_photo(waktu, resource_path("Pictures/bbb.png"), icon_size)
				label_opr = label_photo(operator, resource_path("Pictures/aaa.png"), icon_size)
				btn_detail = label_photo(tr("Detail"), resource_path("Pictures/ccc.png"), icon_size)
				btn_struk = label_photo(tr("Struk"), resource_path("Pictures/ddd.png"), icon_size)
				btn_nota = label_photo(tr("Nota"), resource_path("Pictures/eee.png"), icon_size)
				btn_hapus = label_photo(tr("Hapus"), resource_path("Pictures/hapus080102###.png"), icon_size)
				for i, x in enumerate([label_tgl, label_opr, btn_detail, btn_struk, btn_nota, btn_hapus]):
					x.setStyleSheet(style_button("transparent" if i in [0, 1] else bg, font_size_normal))
				for x in [label_nomor, label_tgl, label_opr, label_total]:
					kiri_layout.addWidget(x, alignment=rata_kiri)
					munculkan(x)
				for x in [btn_detail, btn_struk, btn_nota, btn_hapus]:
					kanan_layout.addWidget(x, alignment=rata_kiri)
					munculkan(x)
				btn_detail.clicked.connect(lambda *args, x=no_trans: detail_transaksi(x))
				btn_struk.clicked.connect(lambda *args, x=no_trans: cetak_struk_transaksi(x))
				btn_nota.clicked.connect(lambda *args, x=no_trans: preparation_for_note(x))
				btn_hapus.clicked.connect(lambda *args, x=no_trans: hapus_riwayat_jual(x))
												
	def filter_lanjutan():
		periode = atas_widget["periode"].currentText()
		opr = atas_widget["operator"].currentText()
		data_riwayat.clear()
		if periode.lower() in ["semua periode", "all period"]:
			if opr.lower() in ["all operator", "semua operator"]:
				for p in riwayat_jual:
					data_riwayat.append(p)
			else:
				for p in riwayat_jual:
					operator = p["operator"]
					if operator.lower() == opr.lower():
						data_riwayat.append(p)
		else:
			if periode.lower() in ["bulan ini", "this month"]:
				start, end = periode_bulan()
			elif periode.lower() in ["minggu ini", "this week"]:
				start, end = periode_minggu()
			else:
				start, end = periode_hari()
			if opr.lower() in ["semua operator", "all operator"]:
				for p in riwayat_jual:
					waktu = parse_date(p["waktu"])
					if start <= waktu <= end:
						data_riwayat.append(p)
			else:
				for p in riwayat_jual:
					if p["operator"].lower() == opr.lower():
						waktu = parse_date(p["waktu"])
						if start <= waktu <= end:
							data_riwayat.append(p)
		split_data()
		preparation()
			
	def filter_per_date():
		collect_data_from_calendar()
		split_data()
		preparation()
				
	def checkout_now(no):
		global bayar_separuh, nomor_transaksi
		cadangan = getData("cadangan_keranjang")
		status = next((p["status"] for p in cadangan if p["no"] == no), "Lunas")
		if status.lower() == "lunas":
			QMB.warning(None, tr("Gagal"), f"{tr('Transaksi dengan nomor transaksi')} {no} {tr('telah dilunasi')}")
			return
		trl = next((d["keranjang"] for d in cadangan if d["no"] == no), None)
		if trl:
			data = json.loads(trl)
			if keranjang:
				penyimpanan_undo.append(copy.deepcopy(keranjang))
			keranjang.clear()
			keranjang.extend(data)
			nomor_transaksi = no
			bayar_separuh = next((p["jumlah_dibayar"] for p in cadangan if p["no"] == no), 0)
			transaksi_baru()
			
	def hapus_cadangan_transaksi(no):
		if askyesno(tr("Konfirmasi"), f"{tr('Hapus data cadangan transaksi')} {no}?"):
			if koneksi["connect"] == 1:
				upload_data("hapus_cadangan", {"no": no}, f"{tr('Data cadangan transaksi')} {no} {tr('telah dihapus')}!")
			else:
				cursor.execute("DELETE FROM cadangan_keranjang WHERE no = ?", (no, ))
				conn.commit()
				QMB.information(None, tr("Berhasil"), f"{tr('Data cadangan transaksi')} {no} {tr('telah dihapus')}!")
			transaksi_pending()
				
	def transaksi_pending():
		if not va("transaksi pending"):
			QMB.warning(None, "", tr("Anda tidak diizinkan"))
			return
		def pencocokan_transaksi():
			for p in cadangan:
				no_trans = p["no"]
				keranjang = json.loads(p["keranjang"])
				subtotal = sum((a.get("harga", 0) * a.get("qty", 0)) for a in keranjang)
				bayar = next((b["bayar"] for b in riwayat if b["no_trans"] == no_trans), None)
				if not bayar:
					continue
				if subtotal <= bayar:
					if koneksi["connect"] == 1:
						data = {
							"no": no_trans,
							"status": "Lunas"
						}
						try:
							res = requests.post(f"{SERVER_URL}/update_status_cadangan", json=data)
							if res.status_code == 200:
								continue
						except:
							continue
					else:
						cursor.execute("UPDATE cadangan_keranjang SET status = ? WHERE no = ?", ("Lunas", no_trans))
			conn.commit()
					
		def prepare_layout():
			frames = {
				"atas": QFrame(),
				"bawah": QFrame(),
				"bawahkiri": QFrame(),
				"bawahkanan": QFrame()
			}
			layouts = {
				"atas": QGridLayout(frames["atas"], alignment=rata_kiri),
				"bawah": QHBoxLayout(frames["bawah"], alignment=rata_atas),
				"bawahkiri": QVBoxLayout(frames["bawahkiri"]),
				"bawahkanan": QVBoxLayout(frames["bawahkanan"], alignment=rata_atas)
			}
			widgets = {
				"tabel": table_maker(["ID", "NAMA", "QTY", "HARGA"]),
				"cek": button("Checkout", font_size_normal, bg),
				"hapus": button(tr("Hapus"), font_size_normal, bg)
			}
			for i in [frames["atas"], frames["bawah"]]:
				i.setObjectName("for_style")
				i.setStyleSheet(f"""
					QFrame#for_style {{
						border: 1px solid {bg};
						border-radius: 2px;
						background-color: transparent;
					}}""")
				
			return frames, layouts, widgets
		def show_data():
			for c in cadangan:
				info = [
					("Nomor", c["no"]),
					("Nama pembeli", c["nama_pembeli"]),
					("Dibayar", pretty_money(c["jumlah_dibayar"])),
					("Status", c["status"])
				]
				keranjang = json.loads(c["keranjang"])
				f, l, w = prepare_layout()
				tabel, model = w["tabel"]
				for i, (a, b) in enumerate(info):
					label1, label2, label3 = QLabel(a), QLabel(":"), QLabel(b)
					for p in [label1, label2, label3]:
						p.setStyleSheet(style_label_bold(font_size_normal))
					l["atas"].addWidget(label1, i, 0, alignment=rata_kiri)
					l["atas"].addWidget(label2, i, 1, alignment=rata_kiri)
					l["atas"].addWidget(label3, i, 2, alignment=rata_kiri)
					
				for p in keranjang:
					model.appendRow([
						QStandardItem(p["id"]),
						QStandardItem(p["nama"]),
						QStandardItem(str(p["qty"])),
						QStandardItem(pretty_money(p["harga"]))
					])
				for p in [w["cek"], w["hapus"]]:
					l["bawahkanan"].addWidget(p, alignment=rata_atas)
				l["bawahkiri"].addWidget(tabel)
				for p in [f["bawahkiri"], f["bawahkanan"]]:
					l["bawah"].addWidget(p)
				for p in [f["atas"], f["bawah"]]:
					f3_layout.addWidget(p)
				w["cek"].clicked.connect(lambda *args, x=c["no"]: checkout_now(x))
				w["hapus"].clicked.connect(lambda *args, x=c["no"]: hapus_cadangan_transaksi(x))
										
		clear_widgets(f3)
		cadangan = getData("cadangan_keranjang")
		riwayat = getData("riwayat_penjualan_campuran")
		pencocokan_transaksi()
		show_data()
		
	def search_for(teks):
		clear_widgets(at)
		write_data_now(teks)
		
	def preparation():
		clear_widgets(at)
		QTimer.singleShot(0, write_data_now)
		
	def split_data():
		nonlocal data_riwayat_split
		data_riwayat_split = [data_riwayat[i:i+5] for i in range(0, len(data_riwayat), 5)]
	
	def do_prev():
		nonlocal count_show
		if count_show <= 0:
			return
		count_show -= 1
		preparation()
		
	def do_next():
		nonlocal count_show
		if count_show >= len(data_riwayat_split) - 1:
			return
		count_show += 1
		preparation()
			
	data_riwayat = []
	data_riwayat_split = []
	count_show = 0
	user_data = getData("user")	
	riwayat_jual = getData("riwayat_penjualan_campuran")
	atas, tengah, bawah = layout_setup()
	bawah_layout = QVBoxLayout(bawah, alignment=rata_atas)
	atas_widget = up_widget()
	tengah_widget = middle_widget()
	setup_up_widget()
	setup_middle_widget()
	collect_data_from_calendar()
	split_data()
	at, ala, bala = set_layout_for_bawah()
	ala.addWidget(QLabel("Atas layout ada"))
	entry_index = bala_widgets()	
	preparation()
	
	atas_widget["filter"].clicked.connect(lambda: safe_run(filter_lanjutan))
	atas_widget["cari"].textChanged.connect(lambda: search_for(atas_widget["cari"].text().strip()))
	atas_widget["lihat"].clicked.connect(lambda: safe_run(filter_per_date))
	
	def transaksi_offline_riwayat():
		if not va("transaksi offline"):
			QMB.warning(None, "", tr("Anda tidak diizinkan"))
			return
		def lihat_keranjang():
			clear_widgets(frame)
			data = take_data(tabel, model)
			if not data:
				return
			no_trans = data[0]
			isi = next((p.get("items", []) for p in cadangan_transaksi if p.get("no_trans", "") == no_trans), None)
			label = QLabel(f"{tr('Menampilkan')} {len(isi)} data")
			label.setStyleSheet(style_label_bold(font_size_judul))
			keranjang_layout.addWidget(label)
			if isi:
				for p in isi:
					tab, mod = table_maker(["ASPEK", "VALUES"])
					for a, b in p.items():
						mod.appendRow([
							QStandardItem(a.replace("_", " ").upper()),
							QStandardItem(str(b))
						])
					keranjang_layout.addWidget(tab)
					
		def konfigurasi_server():
			data = take_data(tabel, model)
			if not data:
				return
			no = data[0]
			d = next((p for p in cadangan_transaksi if p.get("no_trans", "").upper() == no.upper()), None)
			if d:
				if server_alive():
					if askyesno(tr("Konfirmasi"), tr("Upload sekarang?")):
						try:
							res = requests.post(f"{SERVER_URL}/penjualan_campuran", json=d, timeout=5)
							if res.status_code == 200:
								for p in cadangan_transaksi[:]:
									if p.get("no_trans", "").upper() == no.upper():
										cadangan_transaksi.remove(p)
										break
								simpan_semua(file_cadangan_transaksi, cadangan_transaksi)
								QMB.information(None, tr("Berhasil"), f"{tr('Transaksi')} {no} {tr('telah diupload')}!")
								transaksi_offline_riwayat()
						except Exception as e:
							QMB.critical(None, "Error", str(e))
							
				else:
					QMB.critical(None, "OFFLINE", tr("Server tidak aktif"))					
			transaksi_offline_riwayat()
		
		def hapus_offline():
			data = take_data(tabel, model)
			if not data:
				return
			for p in cadangan_transaksi[:]:
				if p.get("no_trans", "").upper() == data[0].upper():
					cadangan_transaksi.remove(p)
					break
			simpan_semua(file_cadangan_transaksi, cadangan_transaksi)
			transaksi_offline_riwayat()
		
		def konfigurasi_semua():
			if cadangan_transaksi:
				if askyesno(tr("Konfirmasi"), tr("Upload seluruh data?")):
					if server_alive():
						count_uploaded, count_deleted = 0, 0
						for p in cadangan_transaksi[:]:
							try:
								res = requests.post(f"{SERVER_URL}/penjualan_campuran", json=p, timeout=5)
								if res.status_code == 200:
									count_uploaded += 1
									cadangan_transaksi.remove(p)
									count_deleted += 1
								else:
									continue
							except Exception:
								continue
						simpan_semua(file_cadangan_transaksi, cadangan_transaksi)
						QMB.information(None, tr("Berhasil"), f"{tr('Data berhasil diupload:')} {count_uploaded} data\n {tr('Data berhasil dihapus:')} {count_deleted} data\n{tr('Riwayat transaksi offline tersisa:')} {len(cadangan_transaksi)} data")
						transaksi_offline_riwayat()
					else:
						QMB.warning(None, tr("Gagal"), tr("Server tidak aktif"))
					
		def prepare_layout():
			clear_widgets(f3)
			tabel, model = table_maker(["Nomor transaksi", "Total", "Sumber", "Operator", "Waktu"])
			wd = {
				"keranjang": button(tr("Lihat isi transaksi"), font_size_normal, "lightblue"),
				"konfig": button(tr("Konfigurasi ke server"), font_size_normal, "lightgreen"),
				"konfig_all": button(tr("Konfigurasi seluruh data"), font_size_normal, "yellow"),
				"hapus": button(tr("Hapus transaksi"), font_size_normal, "red")
			}
			command = [lihat_keranjang, konfigurasi_server, konfigurasi_semua, hapus_offline]
			fr, detail = QFrame(), QFrame()
			layout = QHBoxLayout(fr)
			for i, p in enumerate(list(wd.values())):
				layout.addWidget(p)
				p.clicked.connect(command[i])
			for p in [tabel, fr, detail]:
				f3_layout.addWidget(p)
			return tabel, model, detail, QVBoxLayout(detail)
			
		def isi_data():
			for p in cadangan_transaksi:
				model.appendRow([
					QStandardItem(p.get("no_trans", "")),
					QStandardItem(pretty_money(p.get("total", 0))),
					QStandardItem(p.get("sumber", "")),
					QStandardItem(p.get("operator", "")),
					QStandardItem(date_translator(p.get("waktu", ""), bahasa_aplikasi))
				])
			
		tabel, model, frame, keranjang_layout = prepare_layout()
		isi_data()
		
	def ekspor_penjualan():
		if not va("ekspor transaksi"):
			QMB.warning(None, "", tr("Anda tidak diizinkan"))
			return
		def prepare_ui():
			clear_widgets(f3)
			atas, label_jumlah, label_periode, tengah, bawah = QFrame(), QLabel(), QLabel(), QFrame(), QFrame()
			alay, balay, telay = QHBoxLayout(atas), QHBoxLayout(bawah), QGridLayout(tengah)
			tabel, model = table_maker(["Id produk", "Barcode", "Nama", "Qty", "Harga jual", "Subtotal"])
			for i, p in enumerate([label_jumlah, label_periode]):
				p.setStyleSheet(f"QLabel {{font-size: {font_size_judul}px; font-weight: bold; }}")
				QTimer.singleShot(i * 30, lambda x=p: munculkan(x))
			for p in [atas, label_jumlah, label_periode, tengah, tabel, bawah]:
				f3_layout.addWidget(p)
			return alay, telay, balay, tabel, model, label_jumlah, label_periode, tengah
		
		def prepare_ui_atas():
			wd = {
				"cari": entry(tr("Cari transaksi..."), font_size_normal),
				"periode": combobox(font_size_normal, [tr("Semua periode"), tr("Bulan ini"), tr("Minggu ini"), tr("Hari ini")]),
				"operator": combobox(font_size_normal, [tr("Semua operator")] + list({p["nama"] for p in user_data})),
				"lanjut": button(tr("Lanjut"), font_size_normal, bg),
				"pdf": button(tr("Ekspor PDF"), font_size_normal, "lightgreen"),
				"csv": button(tr("Ekspor CSV"), font_size_normal, "lavender")
			}
			for i, p in enumerate(list(wd.values())):
				layout_atas.addWidget(p)
				QTimer.singleShot(i*30, lambda x=p: munculkan(x))
					
			wd["lanjut"].clicked.connect(lanjut)
			wd["pdf"].clicked.connect(ekspor_riwayat_pdf)
			wd["csv"].clicked.connect(ekspor_riwayat_csv)
			return wd
			
		def prepare_ui_bawah():
			wd = {
				"prev": QPushButton(tr("« Sebelumnya")),
				"lbl": QLineEdit(),
				"next": QPushButton(tr("Selanjutnya »"))
			}
			for w in list(wd.values()):
				set_expanding(w, fix, fix)
				w.setStyleSheet(f"""
					QPushButton {{
						background-color: {bg};
						font-size: {font_size_normal}px;
						font-weight: bold;
						border: none;
						padding: 10px;
						border-radius: 2px;
					}}
					QPushButton:pressed {{
						background-color: black;
						color: white;
					}}
					QLineEdit {{
						background-color: transparent;
						border: 1px solid black;
						border-radius: 2px;
						padding: 10px;
					}}""")
				layout_bawah.addWidget(w)
				munculkan(w)
			wd["prev"].clicked.connect(do_prev)
			wd["next"].clicked.connect(do_next)
			wd["lbl"].setFixedWidth(100)
			return wd["lbl"]
				
		def get_data():
			list_data = []
			periode = awid["periode"].currentText().lower()
			operator = awid["operator"].currentText().lower()
			if periode in ["semua periode", "all period"]:
				start, end = None, None
			else:
				list_periode = ["bulan ini", "minggu ini", "hari ini"]
				list_periode_english = ["this month", "this week", "today"]
				func = [periode_bulan, periode_minggu, periode_hari]
				index_periode = list_periode.index(periode) if periode in list_periode else list_periode_english.index(periode)
				start, end = func[index_periode]()
			if operator == "semua operator":
				if start and end:
					for p in riwayat_jual:
						waktu = parse_date(p["waktu"])
						if start <= waktu <= end:
							list_data.append(p)
				else:
					list_data = [p for p in riwayat_jual]
			else:
				if start and end:
					for p in riwayat_jual:
						opr, waktu = p["operator"], parse_date(p["waktu"])
						if opr.lower() == operator:
							if start <= waktu <= end:
								list_data.append(p)
				else:
					for p in riwayat_jual:
						if p["operator"].lower() == operator:
							list_data.append(p)
			return start, end, list_data
			
		def write_data():
			mulai = date_translator(start.strftime(format_waktu_app), bahasa_aplikasi) if start else ""
			selesai = date_translator(end.strftime(format_waktu_app), bahasa_aplikasi) if start else ""
			jumlah.setText(f"{tr('Menampilkan')} {len(data)} data")
			prd.setText(f"{tr('Periode')}: {mulai} - {selesai}")
			label_count.setText(str(count_run + 1))
			sd = data[count_run]
			info = [
				("WAKTU TRANSAKSI", date_translator(sd["waktu"], bahasa_aplikasi)),
				("NOMOR TRANSAKSI", sd["no_trans"]),
				("TOTAL TRANSAKSI", pretty_money(sd["total"])),
				("TOTAL LABA TRANSAKSI", pretty_money(sd["total_laba"])),
				("OPERATOR", sd["operator"]),
				("SUMBER", sd["sumber"]),
				("PEMBELI", sd["pembeli"]),
				("BAYAR", pretty_money(sd["bayar"])),
				("KEMBALI", pretty_money(sd["kembali"])),
				("BIAYA PAJAK", pretty_money(sd["kena_pajak"])),
				("STATUS PAJAK", "Termasuk pajak" if sd["status_pajak"] == 1 else "Tidak termasuk pajak")
			]
			clear_widgets(tengah)
			for i, (a, b) in enumerate(info):
				labela, labelb, labelc = QLabel(a), QLabel(":"), QLabel(b)
				for x in [labela, labelb, labelc]:
					x.setStyleSheet(style_label_bold(font_size_normal))
				layout_tengah.addWidget(labela, i, 0)
				munculkan(labela)
				layout_tengah.addWidget(labelb, i, 1)
				munculkan(labelb)
				layout_tengah.addWidget(labelc, i, 2)
				munculkan(labelc)
			
			model.removeRows(0, model.rowCount())
			for p in json.loads(sd["data_belanja"]):
				model.appendRow([
					QStandardItem(p.get("id", "")),
					QStandardItem(p.get("barcode", "")),
					QStandardItem(p.get("nama", "")),
					QStandardItem(format_unit(p.get("qty", 0), "unit")),
					QStandardItem(pretty_money(p.get("harga_jual", 0))),
					QStandardItem(pretty_money(p.get("subtotal_jual", 0)))
				])
							
		def do_next():
			nonlocal count_run
			if count_run >= len(data) - 1:
				return
			count_run += 1
			write_data()
		
		def do_prev():
			nonlocal count_run
			if count_run <= 0:
				return
			count_run -= 1
			write_data()
			
		def lanjut():
			nonlocal count_run, start, end, data
			count_run = 0
			start, end, data = get_data()
			write_data()
			
		def ekspor_riwayat_csv():
			mulai = date_translator(start.strftime(format_waktu_app), bahasa_aplikasi) if start else ""
			selesai = date_translator(end.strftime(format_waktu_app), bahasa_aplikasi) if end else ""
			if askyesno(tr("Konfirmasi"), tr("Ekspor riwayat penjualan ke file CSV?")):
				path = choose_save_path(f"{tr('Riwayat penjualan')} {datetime.now().strftime('%Y%m%d')}.csv")
				if not path:
					return
				with open(path, "w", encoding="utf-8", newline="") as f:
					w = csv.writer(f)
					w.writerow(["RIWAYAT PENJUALAN"])
					w.writerow([])
					w.writerow(["Periode", ":", mulai + " - " + selesai])
					w.writerow(["Tanggal", ":", date_translator(now_str(), bahasa_aplikasi)])
					w.writerow([])
					for sd in reversed(data):
						info = [
							("WAKTU TRANSAKSI", date_translator(sd["waktu"], bahasa_aplikasi)),
							("NOMOR TRANSAKSI", sd["no_trans"]),
							("TOTAL TRANSAKSI", pretty_money(sd["total"])),
							("TOTAL LABA TRANSAKSI", pretty_money(sd["total_laba"])),
							("OPERATOR", sd["operator"]),
							("SUMBER", sd["sumber"]),
							("PEMBELI", sd["pembeli"]),
							("BAYAR", pretty_money(sd["bayar"])),
							("KEMBALI", pretty_money(sd["kembali"])),
							("BIAYA PAJAK", pretty_money(sd["kena_pajak"])),
							("STATUS PAJAK", "Termasuk pajak" if sd["status_pajak"] == 1 else "Tidak termasuk pajak")
						]
						for a, b in info:
							w.writerow([a, ":", b])
						w.writerow([])
						w.writerow(["Id produk", "Barcode", "Nama", "Qty", "Harga jual", "Subtotal"])
						keranjang = json.loads(sd["data_belanja"])
						for p in keranjang:
							w.writerow([p.get("id", ""), p.get("barcode", ""), p.get("nama", ""), format_unit(p.get("qty", 0), "unit"), pretty_money(p.get("harga_jual", 0)), pretty_money(p.get("subtotal_jual", 0))])							
						w.writerow([])
						w.writerow([])
				QMB.information(None, tr("Berhasil"), f"{tr('Data riwayat penjualan telah disimpan dalam')} {path}")		
					
		def ekspor_riwayat_pdf():
			def make_zebra_skin(tabel, data, first_color=colors.aliceblue, second_color=colors.mintcream):
				style = [
					("BOX", (0,0), (-1,-1), 0.5, colors.steelblue),
					("FONTSIZE", (0,0), (-1,-1), 8),
					("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
					("BACKGROUND", (0,0), (-1,0), colors.lightgreen),
					("FONTNAME", (0,1), (-1,-1), "Helvetica"),
					("GRID", (0,0), (-1,-1), 0.5, colors.black)
				]
				for i in range(1, len(data)):
					warna = second_color if i % 2 == 0 else first_color
					style.append(("BACKGROUND", (0,i), (-1,i), warna))
				tabel.setStyle(TableStyle(style))
				return tabel
				
			mulai = date_translator(start.strftime(format_waktu_app), bahasa_aplikasi) if start else ""
			selesai = date_translator(end.strftime(format_waktu_app), bahasa_aplikasi) if end else ""
			if askyesno(tr("Konfirmasi"), tr("Ekspor riwayat penjualan ke file pdf?")):
				path = choose_save_path(f"Riwayat penjualan {datetime.now().strftime('%Y%m%d')}.pdf")
				if not path:
					return
				
				doc = SimpleDocTemplate(path)
				spinner = set_spinner(window)
				QApplication.processEvents()
				c = []
				c.append(Paragraph(tr("RIWAYAT PENJUALAN"), style_header))
				c.append(Spacer(1,20))
				c.append(Paragraph(tr("Tanggal") + ": " + date_translator(now_str(), bahasa_aplikasi), style_judul))
				c.append(Spacer(1, 10))
				c.append(Paragraph(tr("Periode") + ": " + mulai + " - " + selesai, style_judul))
				c.append(Spacer(1,20))
				for sd in reversed(data):
					tabel_data = [
						[mp("WAKTU TRANSAKSI"), mp(":"), mp(date_translator(sd["waktu"], bahasa_aplikasi))],
						[mp("NOMOR TRANSAKSI"), mp(":"), mp(sd["no_trans"])],
						[mp("TOTAL TRANSAKSI"), mp(":"), mp(pretty_money(sd["total"]))],
						[mp("TOTAL LABA TRANSAKSI"), mp(":"), mp(pretty_money(sd["total_laba"]))],
						[mp("OPERATOR"), mp(":"), mp(sd["operator"])],
						[mp("SUMBER"), mp(":"), mp(sd["sumber"])],
						[mp("PEMBELI"), mp(":"), mp(sd["pembeli"])],
						[mp("BAYAR"), mp(":"), mp(pretty_money(sd["bayar"]))],
						[mp("KEMBALI"), mp(":"), mp(pretty_money(sd["kembali"]))],
						[mp("BIAYA PAJAK"), mp(":"), mp(pretty_money(sd["kena_pajak"]))],
						[mp("STATUS PAJAK"), mp(":"), mp(tr("Termasuk pajak") if sd["status_pajak"] == 1 else tr("Tidak termasuk pajak"))]
					]
					tabel_data_tabel = Table(tabel_data)
					tabel_data_tabel.setStyle(TableStyle([
						("FONTSIZE", (0,0), (-1,-1), 8),
						("FONTNAME", (0,0), (-1,-1), "Helvetica"),
						("BOX", (0,0), (-1,-1), 0.5, colors.black)
					]))
					c.append(tabel_data_tabel)
					keranjang = json.loads(sd["data_belanja"])
					tabel_data_belanja = [
						[mp("ID PRODUK"), mp("BARCODE"), mp("NAMA"), mp("QTY"), mp("HARGA JUAL"), mp("SUBTOTAL")]
					]
					for p in keranjang:
						tabel_data_belanja.append([
							p.get("id", ""),
							p.get("barcode", ""),
							p.get("nama", ""),
							p.get("qty", 0),
							pretty_money(p.get("harga_jual", 0)),
							pretty_money(p.get("subtotal_jual", 0))
						])
						QApplication.processEvents()
					tabtab = Table(tabel_data_belanja)
					new_tabel = make_zebra_skin(tabtab, keranjang)
					c.append(new_tabel)
					c.append(Spacer(1, 30))
					QApplication.processEvents()
					
				doc.build(c)
				spinner.deleteLater()
				QMB.information(None, tr("Berhasil"), f"{tr('Data riwayat telah disimpan dalam')} {path}")
												
		count_run = 0
		layout_atas, layout_tengah, layout_bawah, tabel, model, jumlah, prd, tengah = prepare_ui()
		awid = prepare_ui_atas()
		start, end, data = safe_run(get_data)
		label_count = prepare_ui_bawah()
		write_data()
		
	def hapus_riwayat_penjualan():
		if not va("hapus transaksi"):
			QMB.warning(None, "", tr("Anda tidak diizinkan"))
			return
		def prepare_ui():
			clear_widgets(f3)
			frames = {
				"atas": QFrame(),
				"bawah": QFrame()
			}
			for p in list(frames.values()):
				f3_layout.addWidget(p)
			frames["atas"].setStyleSheet(style_frame_putih(bg))
			return QHBoxLayout(frames["atas"]), QVBoxLayout(frames["bawah"]), frames["bawah"]
			
		def prepare_top_ui():
			widgets = {
				"date": make_date(),
				"periode": combobox(font_size_normal, [tr("Semua periode"), tr("Bulan ini"), tr("Minggu ini"), tr("Hari ini")]),
				"opr": combobox(font_size_normal, [tr("Semua operator")] + list({p["nama"] for p in user_data})),
				"filter": button(tr("Filter"), font_size_normal, bg),
				"pilih": button(tr("Pilih hapus"), font_size_normal, "lightgreen"),
				"hapus": button(tr("Hapus"), font_size_normal, "yellow"),
				"all": button(tr("Hapus semua"), font_size_normal, "red")
			}
			widgets["date"].setCalendarPopup(True)
			widgets["date"].setDate(QDate.currentDate())
			widgets["filter"].clicked.connect(filter_data)
			widgets["pilih"].clicked.connect(select_delete)
			widgets["hapus"].clicked.connect(hapus_data_filter)
			widgets["all"].clicked.connect(hapus_seluruh_riwayat_penjualan)
			for p in list(widgets.values()):
				atas_layout.addWidget(p)
				munculkan(p)
			return widgets
			
		def filter_data():
			data_filter.clear()
			periode = awid["periode"].currentText().lower()
			operator = awid["opr"].currentText().lower()
			if periode in ["all period", "semua periode"]:
				start, end = None, None
			else:
				list_periode = ["bulan ini", "minggu ini", "hari ini"]
				list_periode_english = ["this month", "this week", "today"]
				list_funx = [periode_bulan, periode_minggu, periode_hari]
				idx = list_periode.index(periode) if periode in list_periode else list_periode_english.index(periode)
				start, end = list_funx[idx]()
			if start and end:
				if operator in ["all operator", "semua operator"]:
					for p in riwayat_jual:
						waktu = parse_date(p["waktu"])
						if start <= waktu <= end:
							data_filter.append(p)
				else:
					for p in riwayat_jual:
						waktu = parse_date(p["waktu"])
						if start <= waktu <= end:
							if p["operator"].lower() == operator:
								data_filter.append(p)
			else:
				if operator in ["all operator", "semua operator"]:
					for p in riwayat_jual:
						data_filter.append(p)
				else:
					for p in riwayat_jual:
						if p["operator"].lower() == operator:
							data_filter.append(p)
							
			show_pratinjau_now()
							
		def first_data():
			tm = awid["date"].text().strip()
			waktu = datetime.strptime(tm, "%d/%m/%y")
			data_filter.clear()
			for p in riwayat_jual:
				if parse_date(p["waktu"]).date() == waktu.date():
					data_filter.append(p)
					
		def select_delete():
			clear_widgets(bawah)
			data_all = {}
			ld = []
			cmb_select_all = checkbutton(tr("Pilih semua"), font_size_normal)
			btn_pilih = button(tr("Lanjutkan"), font_size_normal, bg)
			frame = QFrame()
			layout = QHBoxLayout(frame, alignment=rata_kanan)
			for p in [cmb_select_all, btn_pilih]:
				layout.addWidget(p, alignment=rata_kanan)
				munculkan(p)
			bawah_layout.addWidget(frame)
			for p in riwayat_jual:
				cmb = checkbutton(p["no_trans"] + " | " + pretty_money(p["total"]) + " | " + p["operator"] + p["waktu"], font_size_normal)
				bawah_layout.addWidget(cmb)
				data_all[p["no_trans"]] = cmb
				ld.append(cmb)
				munculkan(cmb)
			
			def select_all():
				if cmb_select_all.isChecked():
					for p in ld:
						p.setChecked(True)
				else:
					for p in ld:
						p.setChecked(False)
			
			def select_now():
				data_filter.clear()
				terpilih = [no for no, v in data_all.items() if v.isChecked()]
				for p in riwayat_jual:
					if p["no_trans"] in terpilih:
						data_filter.append(p)
				show_pratinjau_now()
				
			cmb_select_all.toggled.connect(select_all)
			btn_pilih.clicked.connect(select_now)	
		
		def show_pratinjau_now():
			clear_widgets(bawah)
			QTimer.singleShot(0, show_data)
		
		def show_data():
			tabel, model = table_maker(["Nomor transaksi", "Waktu", "Total", "Operator", "Sumber", "Jumlah produk"])
			for p in data_filter:
				model.appendRow([
					QStandardItem(p["no_trans"]),
					QStandardItem(date_translator(p["waktu"], bahasa_aplikasi)),
					QStandardItem(pretty_money(p["total"])),
					QStandardItem(p["operator"]),
					QStandardItem(p["sumber"]),
					QStandardItem(format_unit(len(json.loads(p["data_belanja"])), "jenis"))
				])
			bawah_layout.addWidget(tabel)
			munculkan(tabel)
			
		def hapus_data_filter():
			if askyesno(tr("Konfirmasi"), f"{tr('Hapus')} {len(data_filter)} data {tr('dari riwayat penjualan')}?"):
				if koneksi["connect"] == 1:
					upload_data("hapus_riwayat_penjualan", [dict(p) for p in data_filter], f"{len(data_filter)} {tr('riwayat penjualan telah dihapus')}")
				else:
					spinner = set_spinner(window)
					QApplication.processEvents()
					for p in data_filter:
						no_trans = p["no_trans"]
						cursor.execute("DELETE FROM riwayat_penjualan_campuran WHERE no_trans = ?", (no_trans, ))
						QApplication.processEvents()
					conn.commit()
					spinner.deleteLater()
					QMB.information(None, tr("Berhasil"), f"{len(data_filter)} {tr('data riwayat penjualan telah berhasil dihapus')}")					
					hapus_riwayat_penjualan()
					
		def hapus_seluruh_riwayat_penjualan():
			if askyesno(tr("Konfirmasi"), f"{tr('Hapus')} {len(riwayat_jual)} data {tr('dari riwayat penjualan')}?"):
				if koneksi["connect"] == 1:
					upload_data("hapus_riwayat_penjualan", [dict(p) for p in riwayat_jual], f"{len(riwayat_jual)} {tr('riwayat penjualan telah dihapus')}")
				else:
					spinner = set_spinner(window)
					QApplication.processEvents()
					for p in riwayat_jual:
						no_trans = p["no_trans"]
						cursor.execute("DELETE FROM riwayat_penjualan_campuran WHERE no_trans = ?", (no_trans, ))
						QApplication.processEvents()
					conn.commit()
					spinner.deleteLater()
					QMB.information(None, tr("Berhasil"), f"{len(riwayat_jual)} {tr('data riwayat penjualan telah berhasil dihapus')}")					
					hapus_riwayat_penjualan()
								
		data_filter = []		
		atas_layout, bawah_layout, bawah = prepare_ui()
		awid = prepare_top_ui()
		first_data()
		show_pratinjau_now()
	
	def set_f2_button():
		btn = {
			"transaksi_baru": button_photo(tr("Transaksi baru"), resource_path("Pictures/buat nota.png"), icon_size, transaksi_baru),
			"transaksi_pending": button_photo(tr("Transaksi pending"), resource_path("Pictures/master.png"), icon_size, transaksi_pending),
			"offline": button_photo(tr("Transaksi offline"), resource_path("Pictures/transaksi offline.png"), icon_size, transaksi_offline_riwayat),
			"ekspor": button_photo(tr("Ekspor riwayat"), resource_path("Pictures/ekspor_pemasukan.png"), icon_size, ekspor_penjualan),
			"hapus": button_photo(tr("Hapus riwayat"), resource_path("Pictures/hehehe.png"), icon_size, hapus_riwayat_penjualan),
			"retur": button_photo(tr("Retur produk"), resource_path("Pictures/retur.png"), icon_size, lambda: safe_run(retur.prepare_frames))
		}
		for p in list(btn.values()):
			p.setStyleSheet(f2_btn(font_size_normal))
			f2_layout.addWidget(p)
		return btn
	
	retur = Retur()	
	btn = set_f2_button()
	
class Pengeluaran:
	def __init__(self):
		self.pengeluaran = None
		
	def filter_pengeluaran(self, ktgr, prd):
		kategori = ktgr.currentText().strip().lower()
		periode = prd.currentText().strip().lower()
		if periode in ["semua periode", "all period"]:
			data_periode = self.pengeluaran
		else:
			id = ["hari ini", "minggu ini", "bulan ini"]
			eng = ["today", "this week", "this month"]
			func = [periode_hari, periode_minggu, periode_bulan]
			idx = id.index(periode) if periode in id else eng.index(periode)
			self.start, self.end = func[idx]()
			data_periode = [dt for dt in self.pengeluaran if self.start <= parse_date(dt["waktu"]) <= self.end]
		
		if kategori in ["semua kategori", "all categories"]:
			data = data_periode
		else:
			data = [dt for dt in data_periode if dt["kategori"].lower() == kategori]	
		return data
		
	def tambah_pengeluaran(self):
		if not va("tambah pengeluaran"):
			QMB.warning(None, tr("Ditolak"), tr("Anda tidak diizinkan"))
			return
		clear_widgets(f3)
		inp = [
			("nama", "Nama pengeluaran"),
			("jumlah", "Jumlah pengeluaran"),
			("satuan", "Satuan pembelian"),
			("harga", "Harga peritem"),
			("total", "Total pengeluaran"),
			("kategori", "Kategori pengeluaran"),
			("keterangan", "Keterangan pengeluaran")
		]
		self.ent = entry_maker(f3_layout, inp)
		btn = button(tr("Simpan"), font_size_normal, bg)
		btn.clicked.connect(lambda: safe_run(self.simpan_tambah))
		f3_layout.addWidget(btn)
		
	def simpan_tambah(self):
		d = self.ent
		try:
			n = d["nama"].text().strip()
			j = int(d["jumlah"].text().strip())
			s = d["satuan"].text().strip()
			h = float(d["harga"].text().strip())
			t = float(d["total"].text().strip())
			kat = d["kategori"].text().strip()
			ket = d["keterangan"].text().strip()
			
		except ValueError as e:
			QMB.critical(None, "", str(e))
			return
		if not all([n, j, h, t, kat, ket]):
			QMB.critical(None, tr("Gagal"), tr("Data tidak lengkap"))
			return
			
		data = {
			"waktu": now_str(),
			"nama": n,
			"jumlah": j,
			"satuan_jumlah": s,
			"harga": h,
			"total": t,
			"kategori": kat,
			"keterangan": ket,
			"operator": nama_operator(),
			"sumber": komputer()
		}
		if askyesno(tr("Konfirmasi"), tr("Simpan data pengeluaran?")):
			if koneksi["connect"] == 1:
				setData("tambah_pengeluaran", data)
			else:
				spinner = set_spinner(window)
				cursor.execute("""
					INSERT INTO Pengeluaran
					(waktu, nama, jumlah, satuan_jumlah, harga, total, kategori, keterangan, operator, sumber)
					VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
					""",
					(
						now_str(),
						n,
						j,
						s,
						h,
						t,
						kat,
						ket,
						nama_operator(),
						komputer()
					)
				)
				
				cursor.execute("UPDATE keuangan SET total_pengeluaran = total_pengeluaran + ? WHERE id = ?",(t, 1))
				conn.commit()
				spinner.deleteLater()
				QMB.information(None, tr("Berhasil"), f"{tr('Pengeluaran')} {n} {tr('telah disimpan')}!")
			self.setup()
					
	def set_f2(self):	
		fr, lay = frame(QVBoxLayout, bg="transparent")
		set_expanding(fr, expand, fix)
		
		atas, atas_layout = frame(QHBoxLayout, bg="transparent")
		bawah, bawah_layout = frame(QHBoxLayout, bg="transparent", rata=rata_kiri)
		
		self.a = {
			"kembali": button_photo(tr("Kembali"), resource_path("Pictures/kembali.png"), icon_size, master),
			"refresh": button_photo("Refresh", resource_path("Pictures/refresh.png"), icon_size, self.setup),
			"baru": button_photo(tr("Pengeluaran baru"), resource_path("Pictures/pengeluaran_baru.png"), icon_size, self.tambah_pengeluaran),
			"cari": entry(tr("Cari pengeluaran..."), font_size_normal)
		}
		
		self.a["cari"].textChanged.connect(lambda: self.set_data_tabel(self.a["cari"].text().strip()))
		
		for i, p in enumerate(self.a.values()):
			if i != 3:
				p.setStyleSheet(f2_btn(font_size_normal))
				atas_layout.addWidget(p, alignment=rata_kiri)
			else:
				atas_layout.addWidget(p, alignment=rata_atas)
				
		self.b = {
			"kategori": combobox(font_size_normal, [tr("Semua kategori")] + list({p["kategori"] for p in self.pengeluaran})),
			"periode": combobox(font_size_normal, [tr("Semua periode"), tr("Hari ini"), tr("Minggu ini"), tr("Bulan ini")]),
			"ekspor_pdf": button(tr("Ekspor PDF"), font_size_normal, bg),
			"ekspor_csv": button(tr("Ekspor CSV"), font_size_normal, bg)
		}
		self.b["kategori"].currentTextChanged.connect(lambda _: self.set_data_tabel())
		self.b["periode"].currentTextChanged.connect(lambda _: self.set_data_tabel())
		self.b["ekspor_pdf"].clicked.connect(lambda: safe_run(self.ekspor_pengeluaran, "pdf"))
		self.b["ekspor_csv"].clicked.connect(lambda: safe_run(self.ekspor_pengeluaran, "csv"))
		
		for p in self.b.values():
			bawah_layout.addWidget(p, alignment=rata_kiri)
			
		for p in [atas, bawah]:
			lay.addWidget(p)
		f2_layout.addWidget(fr)
		
	def ekspor_pdf(self):
		if askyesno(tr("Konfirmasi"), tr("Ekspor pengeluaran ke file pdf sekarang") + "?"):
			spin = set_spinner(window)
			path = choose_save_path(f"Data pengeluaran {datetime.now().strftime('%d %m %y')}.pdf")
			if not path:
				return
			doc = SimpleDocTemplate(path, pagesize=landscape(A4))
			content = []
			content.append(Paragraph("DATA PENGELUARAN", style_header))
			content.append(Spacer(1, 20))
			profil = getData("profil")
			if not profil:
				mb.showwarning("Gagal", "Sepertinya Anda belum melengkapi profil!")
				return
			pr = profil[0]
			data1 = [
				[Paragraph(pr["nama"], style_judul), Paragraph(f"No: {pr['nama'][:3]}_{datetime.now().strftime('%f%Y')}", ParagraphStyle(name="cook", fontName="Helvetica", alignment=TA_RIGHT))],
				[Paragraph(pr["kontak"], style_biasa), None],
				[Paragraph(f"Periode: {date_translator(self.start.strftime('%A, %d %B %Y %H.%M.%S'), bahasa_aplikasi)} / {date_translator(self.end.strftime('%A, %d %B %Y %H.%M.%S'), bahasa_aplikasi)}", style_biasa), None]
			]
			tabel1 = Table(data1, colWidths=[125*mm, 125*mm])
			tabel1_style = TableStyle([
				('SPAN', (0,2), (1,2)),
			])
			tabel1.setStyle(tabel1_style)
			content.append(tabel1)
			content.append(Spacer(1, 20))
					
			def zebra_style(data, tabel, warna_ganjil=colors.lightgrey, warna_genap=colors.lavender):
				style = [
					("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
					("BACKGROUND", (0,0), (-1,0), colors.lightblue),
					("BACKGROUND", (0,-1), (-1,-1), colors.lightblue),
					("BOX", (0,0), (-1,-1), 0.5, colors.black)
				]
				for i in range(1, len(data) - 1):
					warna = warna_genap if i % 2 == 0 else warna_ganjil
					style.append(("BACKGROUND", (0,i), (-1,i), warna))
					tabel.setStyle(TableStyle(style))
				return tabel
					
			data2 = [["WAKTU", "NAMA", "JUMLAH", "TOTAL HARGA", "KATEGORI", "KETERANGAN"]]
			total_jumlah, total_harga = 0, 0
			for p in self.sorted_data:
				total_jumlah += p["jumlah"]
				total_harga += p["total"]
				data2.append([
					mp(p["waktu"]),
					mp(p["nama"]),
					mp(format_unit(p["jumlah"], p["satuan_jumlah"])),
					mp(pretty_money(p["total"])),
					mp(p["kategori"]),
					mp(p["keterangan"])
				])
			data2.append([mp("TOTAL"), None, format_unit(total_jumlah, "Unit"), pretty_money(total_harga), None, None])
			tabel2 = Table(data2, colWidths=[60*mm, 70*mm, 30*mm, 30*mm, 30*mm, 30*mm])
			tabel_data2 = zebra_style(data2, tabel2)
			content.append(tabel_data2)
			content.append(Spacer(1, 15))
			doc.build(content)
			spin.deleteLater()
			QMB.information(None, tr("Berhasil"), f"{tr('File telah tersimpan dalam')} {path}")
	
	def ekspor_csv(self):
		if askyesno(tr("Konfirmasi"), tr("Ekspor pengeluaran ke file csv sekarang") + "?"):
			spin = set_spinner(window)
			path = choose_save_path(f"Data pengeluaran {datetime.now().strftime('%d %m %y')}.csv")
			if not path:
				return
			mulai = date_translator(self.start.strftime(format_waktu_app), bahasa_aplikasi)
			akhir = date_translator(self.end.strftime(format_waktu_app), bahasa_aplikasi)
					
			with open(path, "w", encoding="utf-8", newline="") as f:
				wr = csv.writer(f)
				wr.writerow([tr("DATA PENGELUARAN")])
				wr.writerow([])
				wr.writerow([tr("Periode") + ": " + mulai + " - " + akhir])
				wr.writerow(["WAKTU", "NAMA", "JUMLAH", "TOTAL HARGA", "KATEGORI", "KETERANGAN"])
				total = 0
				total_jumlah = 0
				for p in self.sorted_data:
					total += p["total"]
					total_jumlah += p["jumlah"]
					wr.writerow([p["waktu"], p["nama"], format_unit(p["jumlah"], p["satuan_jumlah"]), pretty_money(p["total"]), p["kategori"], p["keterangan"]])
				wr.writerow(["Total:", "", format_unit(total_jumlah, "Unit"), pretty_money(total), "", ""])
				spin.deleteLater()
				QMB.information(None, tr("Berhasil"), f"{tr('Data pengeluaran telah tersimpan dalam')} {path}")
												
	def ekspor_pengeluaran(self, tipe):
		if not va("ekspor pengeluaran"):
			QMB.warning(None, tr("Ditolak"), tr("Anda tidak diizinkan"))
			return
		teks_peringatan = """
			Fitur ekspor data akan menyimpan data hasil filter kedalam file.
			Silahkan pastikan Anda menyimpan filter data yang benar
			dan sesuai untuk kebutuhan Anda!
			
			Filter lebih lanjut, opsi tersedia dalam filter kategori
			dan filter periode.
		"""
		if askyesno(tr("Peringatan"), tr(teks_peringatan)):
			if tipe.lower() == "pdf":
				self.ekspor_pdf()
			else:
				self.ekspor_csv()
				
	def lihat_detail(self):
		data = take_data(self.tabel, self.model)
		if not data:
			return
		id = int(data[0])
		d = next((p for p in self.pengeluaran if p["id"] == id), None)
		if d:
			clear_widgets(self.fr)
			tbl, mdl = table_maker(["",""])
			for p in [tbl.horizontalHeader(), tbl.verticalHeader()]:
				p.hide()
				
			for i, (key, value) in enumerate(d.items()):
				if key.lower() in ["harga", "total"]:
					val = pretty_money(value)
				else:
					val = str(value)
				mdl.appendRow([
					QStandardItem(str(key.replace("_", " ").lower().capitalize())),
					QStandardItem(val)
				])
			self.lay.addWidget(tbl)
			
	def simpan_edit(self):
		d = {key: value.text().strip() for key, value in self.inp_edit.items()}
		if not self.data_lama:
			return
		try:
			n = d["nama"]
			j = int(d["jumlah"])
			s = d["satuan_jumlah"]
			h = float(d["harga"])
			t = float(d["total"])
			kat = d["kategori"]
			ket = d["keterangan"]
		except Exception:
			QMB.critical(None, tr("Gagal"), tr("Beberapa data harus berisi angka"))
			return
				
		data = {
			"waktu": now_str(),
			"nama": n,
			"jumlah": j,
			"satuan_jumlah": s,
			"harga": h,
			"total": t,
			"kategori": kat,
			"keterangan": ket,
			"operator": nama_operator(),
			"sumber": komputer(),
			"total_awal": self.data_lama["total"],
			"id": self.data_lama["id"]
		}
		if askyesno(tr("Konfirmasi"), tr("Simpan data pengeluaran?")):
			if koneksi["connect"] == 1:
				setData("edit_pengeluaran", data)
			else:
				spin = set_spinner(window)
				cursor.execute("UPDATE keuangan SET total_pengeluaran = total_pengeluaran - ? + ? WHERE id = ?",
					(
						self.data_lama["total"],
						t,
						1
					)
				)
				cursor.execute("UPDATE Pengeluaran SET waktu = ?, nama = ?, jumlah = ?, harga = ?, total = ?, kategori = ?, keterangan = ?, operator = ?, sumber = ?, satuan_jumlah = ? WHERE id = ?", (now_str(), n, j, h, t, kat, ket, nama_operator(), komputer(), s, self.data_lama["id"]))
				conn.commit()
				spin.deleteLater()
				QMB.information(None, tr("Berhasil"), f"{tr('Pengeluaran')} {n} {tr('telah diperbarui')}!")
			self.setup()
			
	def edit_pengeluaran(self):
		if not va("edit pengeluaran"):
			QMB.warning(None, tr("Ditolak"), tr("Anda tidak diizinkan"))
			return
		data = take_data(self.tabel, self.model)
		if not data:
			return
		self.data_lama = None
		try:
			self.data_lama = next((p for p in self.pengeluaran if p["id"] == int(data[0])), None)
		except Exception as e:
			QMB.critical(None, "Error", str(e))
			return
		if not self.data_lama:
			return
		clear_widgets(f3)
		inp = [
			("nama", "Masukkan nama baru"),
			("jumlah", "Masukkan jumlah baru"),
			("satuan_jumlah", "Masukkan satuan baru"),
			("harga", "Masukkan harga baru"),
			("total", "Masukkan total pengeluaran baru"),
			("kategori", "Kategori baru"),
			("keterangan", "Keterangan baru")
		]
		self.inp_edit = entry_maker(f3_layout, inp)
		for key in self.inp_edit.keys():
			self.inp_edit[key.lower()].setText(str(self.data_lama.get(key.lower(), "")))
		btn = button(tr("Simpan"), font_size_normal, bg)
		btn.clicked.connect(self.simpan_edit)
		f3_layout.addWidget(btn)
		
	def hapus_pengeluaran(self):
		if not va("hapus pengeluaran"):
			QMB.warning(None, tr("Ditolak"), tr("Anda tidak diizinkan"))
			return
		data = take_data(self.tabel, self.model)
		if not data:
			return
		if askyesno(tr("Konfirmasi"), tr("Apakah Anda yakin ingin menghapus pengeluaran") + " " + data[1] + "?"):
			if koneksi["connect"] == 1:
				data = {
					"id": int(data[0]),
					"total": float(replace_money(data[4]))
				}
				setData("hapus_pengeluaran", data)
			else:
				spin = set_spinner(window)
				try:
					cursor.execute("UPDATE keuangan SET total_pengeluaran = total_pengeluaran - ? WHERE id = ?",(float(replace_money(data[4])),1))
					cursor.execute("DELETE FROM Pengeluaran WHERE id = ?",(int(data[0]),))
					conn.commit()
					spin.deleteLater()
					QMB.information(None, tr("Berhasil"), f"{tr('Data pengeluaran dengan id')} {data[0]} {tr('telah dihapus')}")
					
				except Exception as e:
					conn.rollback()
					spin.deleteLater()
					QMB.critical(None, "Error", str(e))
			self.setup()
						
	def set_f3(self):
		self.fr, self.lay = frame(QGridLayout, bg="rgba(0,120,100,0.06)")
		
		self.tabel, self.model = table_maker(["ID", "NAMA", "JUMLAH", "HARGA", "TOTAL", "KATEGORI", "KETERANGAN"])
		fr, lay = frame(QHBoxLayout, bg="rgba(0,120,100,0.06)", rata=rata_kiri)
		
		self.c = {
			"detail": button(tr("Detail pengeluaran"), font_size_normal, bg),
			"hapus": button(tr("Hapus pengeluaran"), font_size_normal, bg),
			"edit": button(tr("Edit pengeluaran"), font_size_normal, bg)
		}
		self.c["detail"].clicked.connect(self.lihat_detail)
		self.c["hapus"].clicked.connect(lambda: safe_run(self.hapus_pengeluaran))
		self.c["edit"].clicked.connect(lambda: safe_run(self.edit_pengeluaran))

		self.lay.addWidget(self.tabel)
		for p in self.c.values():
			lay.addWidget(p, alignment=rata_kiri)
			
		for p in [self.fr, fr]:
			f3_layout.addWidget(p, alignment=rata_atas)
	
	def set_data_tabel(self, teks=""):	
		self.data = self.filter_pengeluaran(self.b["kategori"], self.b["periode"])
		self.sorted_data = sorted(self.data, key=lambda x: parse_date(x["waktu"]), reverse=True)
		self.model.removeRows(0, self.model.rowCount())
		total_jumlah, total_total = 0, 0	
		for p in self.sorted_data:
			total_jumlah += p.get("jumlah",0)
			total_total += p.get("total",0)
			if teks.lower() in p.get("nama","").lower() or teks.lower() in p.get("kategori","").lower():
				self.model.appendRow([
					QStandardItem(str(p["id"])),
					QStandardItem(p["nama"]),
					QStandardItem(format_unit(p["jumlah"], p["satuan_jumlah"])),
					QStandardItem(pretty_money(p["harga"])),
					QStandardItem(pretty_money(p["total"])),
					QStandardItem(p["kategori"]),
					QStandardItem(p["keterangan"])
				])
		self.model.appendRow([
			QStandardItem("TOTAL"),
			QStandardItem(""),
			QStandardItem(format_unit(total_jumlah, "unit")),
			QStandardItem(""),
			QStandardItem(pretty_money(total_total)),
			QStandardItem(""),
			QStandardItem("")
		])
		row = self.model.rowCount() - 1
		self.tabel.setSpan(row,0,1,2)
		self.tabel.setSpan(row,2,1,2)
		self.tabel.setSpan(row,4,1,3)
		
	def setup(self):
		self.pengeluaran = getData("Pengeluaran") or []
		
		for p in [f2, f3]:
			clear_widgets(p)
		self.set_f2()
		self.set_f3()
		self.set_data_tabel()
		
class Retur:
	def __init__(self):
		self.no = None
		self.data = []
		self.keranjang_retur = []
		self.total_retur = 0
		self.riwayat_retur = []
		
	def tampilkan_retur(self):
		clear_widgets(self.bawah_tengah)
		self.judul.setText(tr("TOTAL RETUR") + ": " + pretty_money(self.total_retur))
		for i, p in enumerate(self.keranjang_retur):
			fr, lay = frame(QGridLayout, bg="qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2)", rata=rata_atas)
			for j, (key, value) in enumerate(p.items()):
				for k, item in enumerate([key.capitalize(), ":", str(value)]):
					teks = label(item, color="white")
					lay.addWidget(teks, j, k, alignment=rata_kiri)
			self.btl.addWidget(fr, i//3, i%3, alignment=rata_kiri)
			munculkan(fr)
			
	def tambah_keranjang(self, id, jumlah):
		try:
			qty_retur = int(jumlah.text().strip())
		except ValueError as e:
			QMB.critical(None, "Error", str(e))
			return
		if qty_retur <= 0:
			return
		item_keranjang = next((p for p in self.keranjang if p["id"] == id), None)
		if item_keranjang is None:
			QMB.warning(None, tr("Gagal"), tr("Produk tidak ditemukan"))
			return
			
		item_retur = next((p for p in self.keranjang_retur if p["id"] == id), None)
		qty_sudah_ada = item_retur["jumlah"] if item_retur else 0
		total_qty_retur = qty_sudah_ada + qty_retur
		qty_asli = item_keranjang.get("qty_asli",0)

		if total_qty_retur > qty_asli:
			return
		qty_sisa = qty_asli - total_qty_retur
		
		subtotal_retur = 0
		if item_keranjang.get("tipe_promo","").lower() == "diskon":
			potongan_promo_batal = 0
			if qty_sisa < item_keranjang.get("min_diskon",0):
				potongan_promo_batal = item_keranjang.get("potongan_diskon",0) / qty_asli * qty_sisa
			subtotal_retur = total_qty_retur * item_keranjang.get("harga_jual",0) - potongan_promo_batal
		elif item_keranjang.get("tipe_promo","").lower() == "tingkat":
			potongan_promo_batal = 0
			if qty_sisa < item_keranjang.get("min_tingkat",0):
				potongan_promo_batal = item_keranjang.get("potongan_tingkat",0) / qty_asli * qty_sisa						
			total_refund_kotor = item_keranjang.get("harga_jual",0) / qty_asli * total_qty_retur
			subtotal_retur = total_refund_kotor - potongan_promo_batal
		else:
			subtotal_retur = total_qty_retur * item_keranjang.get("harga_jual",0)
			
		if subtotal_retur > 0:			
			if item_retur:
				item_retur["jumlah"] = total_qty_retur
				item_retur["subtotal"] = subtotal_retur
			else:
				self.keranjang_retur.append({
					"id": id,
					"nama": next((p["nama"] for p in self.keranjang if p["id"] == id), ""),
					"jumlah": total_qty_retur,
					"subtotal": subtotal_retur
				})
			self.total_retur = sum(p["subtotal"] for p in self.keranjang_retur)
			self.tampilkan_retur()
		else:
			#TO DO: Nanti kita buat untuk kondisi lain
			QMB.warning(None, tr("Gagal"), tr("Sepertinya ada yang salah dengan perhitungan retur. Hasil: Subtotal retur = {subtotal_retur}"))
						
	def show_data(self):
		self.total_retur = 0
		self.keranjang_retur = []
		for p in [self.bawah_atas, self.bawah_bawah]:
			clear_widgets(p)
			
		self.no = self.cari.text().strip()
		self.data = getData("riwayat_penjualan_campuran")
		self.dt = next((p for p in self.data if p["no_trans"] == self.no), None)
		
		if not self.dt:
			warn_label = red_label(tr("Transaksi tidak ditemukan"))
			self.bawah_layout.addWidget(warn_label)
		d = self.dt
		info = [
			("Nomor transaksi", d["no_trans"]),
			("Tanggal pembelian", d["waktu"]),
			("Total belanja", pretty_money(d["total"])),
			("Total bayar", pretty_money(d["bayar"])),
			("Pembeli", d["pembeli"]),
			("Transaksi oleh", d["operator"]),
			("Transaksi dari", d["sumber"])
		]
		for i, (key, value) in enumerate(info):
			for j, teks in enumerate([tr(key), ":", value]):
				label_teks = label(teks, font_weight=500)
				self.bal.addWidget(label_teks, i, j, alignment=rata_atas)
				munculkan(label_teks)
	
		self.keranjang = json.loads(d["data_belanja"])
		self.entries = {}
		for i, item in enumerate(self.keranjang):
			fr, lay = frame(QVBoxLayout, bg="qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0,100,120,0.06), stop:1 rgba(0,190,70,0.06))", rata=rata_atas)
			nama = label(
				item.get("nama","").upper(),
				font_size=font_size_judul,
				font_weight=600,
				color="green",
				border="0.5px solid green",
				border_radius=2,
				padding=5
			)
			lay.addWidget(nama)
			info_field = [
				"Jumlah pembelian: " + str(item.get("qty_asli",0)) + " unit",
				"Harga jual: " + pretty_money(item.get("harga_jual",0)),
				"Subtotal jual: " + pretty_money(item.get("subtotal_jual",0))
			]
			for teks in info_field:
				lbl_teks = label(teks, font_weight=500)
				lay.addWidget(lbl_teks)
	
			jumlah_retur = entry(tr("Masukkan jumlah retur"), font_size_normal)
			jumlah_retur.setText(str(item.get("qty_asli",0)))
			btn_tambah = button(tr("Tambah"), font_size_normal, bg)
			btn_tambah.clicked.connect(lambda *args, id=item["id"], j=jumlah_retur: safe_run(self.tambah_keranjang, id, j))
			for wd in [jumlah_retur, btn_tambah]:
				lay.addWidget(wd)
			self.bbl.addWidget(fr, i//2, i%2)
			munculkan(fr)
	
	def hitung_pajak(self, harga_jual, status_pajak, persen_pajak):
		if status_pajak == 1:
			harga_awal = harga_jual / (1 + persen_pajak / 100)
			nilai_pajak = harga_jual - harga_awal
			return round(nilai_pajak)
		else:
			return 0
			
	def ajukan_retur_sekarang(self):
		if askyesno(tr("Konfirmasi"), tr("Ajukan retur sekarang") + "?"):
			if koneksi["connect"] == 1:
				data = {
					"belanja": self.dt,
					"retur": self.keranjang_retur,
					"alasan": self.alasan.text().strip(),
					"operator": nama_operator()
				}
				setData("proses_retur", data)
			else:
				status_pajak = self.dt.get("status_pajak",0)
				for p in self.keranjang_retur:
					cursor.execute("SELECT jumlah FROM produk WHERE id_produk = ?",(p.get("id",""),))
					jumlah = cursor.fetchone()
					if not jumlah:
						conn.rollback()
						QMB.warning(None, tr("Gagal"), f"{tr('Produk')} {p.get('nama','')} {tr('tidak ditemukan')}")
						return
					cursor.execute("UPDATE produk SET jumlah = ? WHERE id_produk = ?",(jumlah["jumlah"] + p.get("jumlah",0), p.get("id","")))
					
					item_jual = next((k for k in self.keranjang if k.get("id","") == p.get("id","")), None)
					if status_pajak == 1:
						if item_jual.get("tipe_promo","").lower() == "tingkat":
							harga_jual_peritem = item_jual.get("harga_jual",0) / item_jual.get("qty_asli",0)
							nilai_pajak = self.hitung_pajak(harga_jual_peritem, status_pajak, item_jual.get("persen_pajak",0))
						else:
							nilai_pajak = self.hitung_pajak(item_jual.get("harga_jual",0), status_pajak, item_jual.get("persen_pajak",0))
						cursor.execute("INSERT INTO riwayat_pajak (waktu, nama, pajak) VALUES (?, ?, ?)",
							(
								now_str(),
								item_jual.get("nama",""),
								-nilai_pajak * p.get("jumlah",0)
							)
						)
					laba_terkurang = item_jual["laba"] / item_jual["qty_asli"] * p["jumlah"]
					pemasukan_terkurang = p.get("subtotal", 0)
					cursor.execute("SELECT pemasukan, keuntungan FROM keuangan")
					keuangan = cursor.fetchone()
					
					cursor.execute("UPDATE keuangan SET pemasukan = ?, keuntungan = ? WHERE id = ?",
						(
							(keuangan["pemasukan"] if keuangan else 0) - pemasukan_terkurang,
							(keuangan["keuntungan"] if keuangan else 0) - laba_terkurang,
							1
						)
					)
				cursor.execute("INSERT INTO riwayat_retur (waktu, no_trans, pembeli, data, alasan) VALUES (?, ?, ?, ?, ?)",
					(
						now_str(),
						self.dt.get("no_trans",""),
						self.dt.get("pembeli", ""),
						json.dumps(self.keranjang_retur),
						self.alasan.text().strip()
					)
				)
				cursor.execute("SELECT * FROM keuangan")
				uang = cursor.fetchone()
				saldo_awal = (uang["pemasukan"] - uang["total_pengeluaran"] + uang["saldo"]) if uang else 0
				cursor.execute("INSERT INTO riwayat_keuangan (waktu, jumlah, jenis, sumber, saldo_awal, saldo_akhir, pihak_terkait, keterangan, id_keuangan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
					(
						now_str(),
						self.total_retur,
						"Retur produk",
						"Saldo kas",
						saldo_awal,
						saldo_awal - self.total_retur,
						json.dumps([self.dt.get("pembeli",""), nama_operator()]),
						"Selesai",
						str(uuid.uuid4())[:5]
					)
				)
				conn.commit()
				QMB.information(None, tr("Berhasil"), tr("Proses retur berhasil"))
				
	def riwayat_retur_transaksi(self):
		self.riwayat_retur = getData("riwayat_retur")
		if not self.riwayat_retur:
			QMB.warning(None, tr("Kosong"), tr("Data retur belum tersedia"))
			return
		clear_widgets(self.bawah_atas)
		
	def prepare_frames(self):
		self.total_retur = 0
		self.keranjang_retur = []
		clear_widgets(f3)
		atas, atas_layout = frame(QHBoxLayout, rata=rata_atas)
		self.bawah, self.bawah_layout = frame(QHBoxLayout, rata=rata_atas)
		
		self.fr_judul, jl = frame(QHBoxLayout, rata=rata_kiri)
		self.bawah_atas, self.bal = frame(QGridLayout, rata=rata_kiri, bg="rgba(0,120,100,0.06)", padding=10, border_radius=2)
		self.bawah_tengah, self.btl = frame(QGridLayout, rata=rata_kiri)
		self.bawah_bawah, self.bbl = frame(QGridLayout, rata=rata_atas)
		
		kanan, layout_kanan = frame(QVBoxLayout)
		self.alasan = entry(tr("Alasan melakukan retur") + "...", font_size_normal)
		
		self.cari = entry(tr("Masukkan nomor transaksi..."), font_size_normal)
		self.cari.setText("F06_142070")
		btn_cari = button(tr("Cari"), font_size_normal, bg)
		btn_cari.clicked.connect(lambda: safe_run(self.show_data))
		btn_riwayat = button(tr("Riwayat retur"), font_size_normal, bg)
		btn_riwayat.clicked.connect(self.riwayat_retur_transaksi)
		
		self.judul = label(tr("TOTAL RETUR") + ": " + pretty_money(0), font_size=font_size_judul, font_weight=700)
		self.btn_retur = button(tr("Ajukan retur"), font_size_normal, bg)
		self.btn_retur.clicked.connect(lambda: safe_run(self.ajukan_retur_sekarang))
		
		
		for p in [self.alasan, self.fr_judul, self.bawah_tengah, self.bawah_bawah]:
			layout_kanan.addWidget(p)
		for p in [self.judul, self.btn_retur]:
			jl.addWidget(p, alignment=rata_kiri)
		for p in [self.bawah_atas, kanan]:
			self.bawah_layout.addWidget(p, alignment=rata_atas)
		for p in [self.cari, btn_cari, btn_riwayat]:
			atas_layout.addWidget(p)
		for p in [atas, self.bawah]:
			f3_layout.addWidget(p, alignment=rata_atas)
	
def lainnya():
	def pengaturan_bahasa():
		def prepare_widgets():
			clear_widgets(f3)
			wd = {
				"judul": QLabel(tr("PILIH BAHASA")),
				"id": QRadioButton("Bahasa Indonesia"),
				"eng": QRadioButton("English"),
				"btn": button(tr("Simpan"), font_size_normal, bg)
			}
			if bahasa_aplikasi == "bahasa indonesia":
				wd["id"].setChecked(True)
			else:
				wd["eng"].setChecked(True)
			grup = QButtonGroup()
			for p in [wd["id"], wd["eng"]]:
				grup.addButton(p)
			wd["btn"].clicked.connect(set_bahasa)			
			for i, p in enumerate(list(wd.values())[:-1]):
				p.setStyleSheet(style_label_bold(font_size_normal) if i == 0 else style_label(font_size_normal))
			for p in list(wd.values()):
				f3_layout.addWidget(p)
				munculkan(p)
			return grup
		
		def set_bahasa():
			bahasa = grup.checkedButton()
			if not bahasa:
				QMB.critical(None, tr("Gagal"), tr("Pilih bahasa terlebih dahulu"))
				return
			lg = bahasa.text().lower()
			if askyesno(tr("Konfirmasi"), f"{tr('Tetapkan')} {lg} {tr('sebagai bahasa default')}?"): 
				if koneksi["connect"] == 1:
					upload_data("ganti_bahasa", {"bahasa": lg}, tr("Bahasa default berhasil diubah"))
				else:
					cursor.execute("SELECT bahasa FROM pengaturan_format")
					b = cursor.fetchone()
					if b:
						cursor.execute("UPDATE pengaturan_format SET bahasa = ? WHERE id = ?", (lg.lower(), 1))
					else:
						cursor.execute("INSERT INTO pengaturan_format (bahasa) VALUES (?)", (lg.lower(), ))
					conn.commit()
					QMB.information(None, "Berhasil", "Pengaturan bahasa telah diperbarui")
		
		grup = prepare_widgets()
	
	def pengaturan_mata_uang():
		def prepare_frames():
			clear_widgets(f3)
			fr, frb = QFrame(), QFrame()
			lay = QHBoxLayout(fr)
			kiri, kanan = QFrame(), QFrame()
			kanan.hide()
			for p in [kiri, kanan]:
				lay.addWidget(p)
			for p in [fr, frb]:
				f3_layout.addWidget(p)
			return QVBoxLayout(kiri, alignment=rata_atas), QGridLayout(kanan, alignment=rata_atas), kanan, QGridLayout(frb, alignment=rata_atas)
		
		def prepare_kiri_widgets():
			wd = {
				"judul": QLabel(tr("Simbol mata uang")),
				"entry_cur": entry(tr("Masukkan format uang..."), font_size_normal),
				"btn_choose": button(tr("Atau pilih simbol mata uangmu!"), font_size_normal, bg),
				"pos": combobox(font_size_normal, [tr("Posisi simbol"), tr("Kiri"), tr("Kanan")]),
				"rib": combobox(font_size_normal, [tr("Pemisah ribuan"), "Comma ,", "Dot ."]),
				"des": combobox(font_size_normal, [tr("Pemisah desimal"), "Comma ,", "Dot ."]),
				"izin_des": checkbutton(tr("Izinkan desimal"), font_size_normal),
				"sbs": checkbutton(tr("Spasi sebelum simbol"), font_size_normal),
				"sas": checkbutton(tr("Spasi setelah simbol"), font_size_normal),
				"max_des": entry(tr("Maksimal batas desimal (2 atau 3 direkomendasikan)"), font_size_normal),
				"save": button(tr("Simpan"), font_size_normal, bg)
			}
			wd["judul"].setStyleSheet(style_label_bold(font_size_normal))
			wd["btn_choose"].clicked.connect(show_and_hide_kanan_frame)
			wd["save"].clicked.connect(simpan)
			for p in list(wd.values()):
				kiri_layout.addWidget(p)
				munculkan(p)
			return wd
		
		def give(x):
			teks = x.split()
			wd["entry_cur"].setText(teks[0].strip())
			
		def show_and_hide_kanan_frame():
			nonlocal state_show
			if not state_show:
				state_show = True
				munculkan(kanan_frame)
			else:
				state_show = False
				kanan_frame.hide()
					
		def prepare_currency_symbols():
			simbol_mata_uang = ["$ Dolar", "€ Euro", "£ Pound sterling", "¥ Yen", "₹ Rupee India", "₩ Won Korea Selatan", "₽ Rubel Rusia", "₺ Lira Turki", "₦ Naira Nigeria", "฿ Baht Thailand", "₫ Dong Vietnam", "₱ Peso Filipina", "₲ Guarani Paraguay", "₴ Hryvnia Ukraina", "﷼ Rial Iran", "៛ Riel Kamboja", "₭ Kip Laos", "₮ Tugrik Mongolia", "₡ Colon Kosta Rika"]
			for i in range(len(simbol_mata_uang)):
				baris = i // 3
				kolom = i % 3
				btn = button(simbol_mata_uang[i], font_size_normal, bg)
				btn.clicked.connect(lambda checked, x=simbol_mata_uang[i]: give(x))
				kanan_layout.addWidget(btn, baris, kolom, alignment=rata_atas)
				
		def simpan():
			try:
				nilai_simbol = wd["entry_cur"].text().strip()
				posisi = "kiri" if wd["pos"].currentText().lower() in ["left", "kiri"] else "kanan"
				pr = wd["rib"].currentText().split()
				pembagi_ribuan = pr[-1]
				pd = wd["des"].currentText().split()
				pembagi_desimal = pd[-1]
				max_desimal = wd["max_des"].text()
				gunakan_desimal = wd["izin_des"].isChecked()
				sb = " " if wd["sbs"].isChecked() else ""
				sa = " " if wd["sas"].isChecked() else ""
				
				list_data = json.dumps([sb+nilai_simbol+sa, posisi, pembagi_ribuan, pembagi_desimal, max_desimal])
				if QMB.question(None, tr("Konfirmasi"), tr("Simpan sekarang?"), QMB.Yes | QMB.No) == QMB.Yes:
					if koneksi["connect"] == 1:
						data = {"data": list_data, "use_decimal": gunakan_desimal}
						upload_data("tambah_mata_uang", data, tr("Format mata uang telah ditambahkan"))
					else:
						cursor.execute("SELECT format_uang FROM pengaturan_format")
						d = cursor.fetchone()
						if d:
							cursor.execute("UPDATE pengaturan_format SET format_uang = ? WHERE id = ?", (list_data, 1))
						else:
							cursor.execute("INSERT INTO pengaturan_format (format_uang) VALUES (?)", (list_data, ))
						conn.commit()
						desimal["approved"] = gunakan_desimal
						simpan_semua(file_desimal, desimal)
						QMB.information(None, tr("Berhasil"), tr("Format mata uang telah ditambahkan"))
				
			except Exception as e:
				QMB.critical(None, "", str(e))
				
		def show_pratinjau():
			try:
				my = getData("pengaturan_format")
				if not my or not my[0]:
					bawah_layout.addWidget(red_label(tr("Tidak ada mata uang terdaftar")), 0, 0)
					return
				uang = next((json.loads(p["format_uang"]) for p in my), None)
				try:
					mmm = float(datetime.now().strftime("%f%y"))
					teks_uang = f"{mmm:,.{int(uang[-1])}f}".replace(".", ",").split(",")
					if uang[1].lower() == "kiri":
						teks_uang = uang[0] + uang[2].join(teks_uang[:-1]) + uang[3] + teks_uang[-1]
					else:
						teks_uang = uang[2].join(teks_uang[:-1]) + uang[3] + teks_uang[-1] + " " + uang[0]
				except Exception:
					teks_uang = "Rp1.234,56"
					
				info = [
					(tr("Simbol atau format mata uang"), uang[0]),
					(tr("Posisi simbol"), uang[1]),
					(tr("Pemisah ribuan"), uang[2]),
					(tr("Pemisah desimal"), uang[3]),
					(tr("Maksimal batas desimal"), uang[4])
				]
				for i, (a, b) in enumerate(info):
					labela, label, labelb = QLabel(a.upper()), QLabel(":"), QLabel(b)
					for p in [labela, label, labelb]:
						p.setStyleSheet(style_label_bold(font_size_normal))
					bawah_layout.addWidget(labela, i, 0, alignment=rata_kiri)
					bawah_layout.addWidget(label, i, 1, alignment=rata_kiri)
					bawah_layout.addWidget(labelb, i, 2)
					for p in [labela, label, labelb]:
						munculkan(p)
				label_uang = QLabel(teks_uang)
				label_uang.setStyleSheet(style_label_bold(font_size_normal))
				bawah_layout.addWidget(label_uang, 0, 3)
				munculkan(label_uang)
			except Exception as e:
				QMB.critical(None, "", str(e))
			
		state_show = False
		kiri_layout, kanan_layout, kanan_frame, bawah_layout = prepare_frames()
		wd = prepare_kiri_widgets()
		prepare_currency_symbols()
		show_pratinjau()
		
	def pengaturan_format_waktu():
		def prepare_widgets():
			clear_widgets(f3)
			wd = {
				"judul tanggal": QLabel(tr("PILIH FORMAT TANGGAL")),
				"grid tanggal": QFrame(),
				"hbox tanggal": QFrame(),
				"judul waktu": QLabel(tr("PILIH FORMAT WAKTU")),
				"grid waktu": QFrame(),
				"hbox waktu": QFrame(),
				"btn": button(tr("Simpan"), font_size_normal, bg)
			}
			wd["btn"].clicked.connect(simpan)
			for p in [wd["grid tanggal"], wd["grid waktu"]]:
				p.setStyleSheet(style_frame_putih("transparent"))
			for p in [wd["judul tanggal"], wd["judul waktu"]]:
				p.setStyleSheet(style_label_bold(font_size_normal))
			for p in list(wd.values()):
				f3_layout.addWidget(p, alignment=rata_atas)
				munculkan(p)
			return wd

		def prepare_date_and_time_buttons():
			list_tanggal = [
				"DD/MM/YYYY",
				"MM/DD/YYYY",
				"DD-MM-YYYY",
				"MM-DD-YYYY",
				"YYYY/MM/DD",
				"YYYY-MM-DD",
				"DD/MM/YY",
				"DD-MM-YY",
				"MM/DD/YY",
				"MM-DD-YY",
				"YY/MM/DD",
				"YY-MM-DD",		
				f"{tr('Hari')}, DD {tr('Bulan')} YYYY",
			]
			list_waktu = [
				"HH:MM:SS",
				"HH/MM/SS",
				"HH.MM.SS",
				"HH:MM",
				"HH/MM",
				"HH.MM"
			]
			try:
				for i in range(len(list_tanggal)):
					baris, kolom = i // 5, i % 5
					btn = button(list_tanggal[i], font_size_normal, bg)
					btn.clicked.connect(lambda *args, x=list_tanggal[i]: give_tgl(x))
					layout_tanggal.addWidget(btn, baris, kolom)
					
				for i in range(len(list_waktu)):
					baris, kolom = i // 5, i % 5
					btn = button(list_waktu[i], font_size_normal, bg)
					btn.clicked.connect(lambda *args, x=list_waktu[i]: give_tm(x))
					layout_waktu.addWidget(btn, baris, kolom)
			except Exception as e:
				QMB.critical(None, "", str(e))
				
		def give_tgl(tgl):
			date = tgl.replace("DD", "%d").replace("Day", "%A").replace("Month", "%B").replace("MM", "%m").replace("YYYY", "%Y").replace("YY", "%y").replace("Hari", "%A").replace("Bulan", "%B")
			tanggal = datetime.now().strftime(date)
			label_tgl.setText(tr("Sebagai contoh") + ":" + " " + tanggal)
			entry_tgl.setText(date)
			
		def give_tm(tm):
			waktu = tm.replace("HH", "%H").replace("MM", "%M").replace("SS", "%S")
			time = datetime.now().strftime(waktu)
			label_tm.setText(tr("Sebagai contoh") + ":" + " " + time)
			entry_tm.setText(waktu)
			
		def prepare_entry_and_label():
			wd = [
				entry("", font_size_normal),
				QLabel(),
				entry("", font_size_normal),
				QLabel()
			]
			for p in [wd[1], wd[3]]:
				p.setStyleSheet(style_label(font_size_normal))
			for i,p in enumerate(wd):
				lt.addWidget(p) if i in [0, 1] else lw.addWidget(p)
			return wd[0], wd[1], wd[2], wd[3]
			
		def simpan():
			try:
				str_tanggal = entry_tgl.text().strip()
				str_waktu = entry_tm.text().strip()
				if not str_tanggal:
					QMB.warning(None, tr("Gagal"), tr("Format tanggal harus diisi"))
					return
				teks_for_format = str_tanggal + " " + str_waktu
				if askyesno(tr("Konfirmasi"), tr("Simpan format waktu sekarang?")):
					if koneksi["connect"] == 1:
						data = {"format": teks_for_format}
						upload_data("tambah_format_waktu", data, tr("Format waktu telah diperbarui"))
					else:
						cursor.execute("SELECT format_waktu FROM pengaturan_format")
						frmt = cursor.fetchone()
						if frmt:
							cursor.execute("UPDATE pengaturan_format SET format_waktu = ? WHERE id = ?", (teks_for_format, 1))
						else:
							cursor.execute("INSERT INTO pengaturan_format (format_waktu) VALUES (?)", (teks_for_format, ))
						conn.commit()
						QMB.information(None, tr("Berhasil"), tr("Format waktu telah diperbarui"))
			except Exception as e:
				QMB.information(None, "", str(e))
								
		wd = prepare_widgets()
		layout_tanggal, layout_waktu = QGridLayout(wd["grid tanggal"], alignment=rata_kiri), QGridLayout(wd["grid waktu"], alignment=rata_kiri)
		lt, lw = QHBoxLayout(wd["hbox tanggal"]), QHBoxLayout(wd["hbox waktu"])
		prepare_date_and_time_buttons()
		entry_tgl, label_tgl, entry_tm, label_tm = prepare_entry_and_label()
		
	def pengaturan_koneksi():
		def prepare_parents():
			clear_widgets(f3)
			wd = {
				"koneksi": QLabel(tr("Koneksi database")),
				"cek": checkbutton(tr("Sambungkan ke server atau gunakan database lokal"), font_size_normal),
				"fr": QFrame(),
				"fr koneksi": QFrame(),
				"printer": QLabel(tr("Koneksi printer")),
				"fr printer": QFrame()
			}
			wd["fr"].setStyleSheet(style_frame_putih("transparent"))
			wd["cek"].setChecked(koneksi["connect"])
			wd["cek"].toggled.connect(switch)
			for p in [wd["koneksi"], wd["printer"]]:
				p.setStyleSheet(style_label_bold(font_size_normal))
			for i, p in enumerate(list(wd.values())):
				f3_layout.addWidget(p)
			for p in [wd["koneksi"], wd["cek"], wd["fr koneksi"], wd["printer"]]:
				munculkan(p)
			return wd
			
		def switch():
			cek = wd["cek"].isChecked()
			koneksi["connect"] = cek
			simpan_semua(file_koneksi, koneksi)
			konfigurasi_koneksi()
			
		def info_koneksi():
			try:
				data = cek_kekuatan_koneksi()
				for i, (a, b) in enumerate(data.items()):
					labela, label, labelb = QLabel(a.replace("_", " ")), QLabel(":"), QPushButton(str(b))
					for c in [labela, label]:
						c.setStyleSheet(style_label_bold(font_size_normal))
					labelb.setStyleSheet(style_button("yellow", font_size_normal) if i == 3 else style_button("transparent", font_size_normal))
					layout_info.addWidget(labela, i, 0)
					layout_info.addWidget(label, i, 1)
					layout_info.addWidget(labelb, i, 2, alignment=rata_kiri)
			except Exception as e:
				QMB.critical(None, "", str(e))
		
		def select_printer(p):
			if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
				cursor.execute("INSERT INTO universal_printer (tipe, info) VALUES (?, ?)", ("Usb port", json.dumps([p.get("vid", ""), p.get("pid", "")])))
				conn.commit()
				printer.clear()
				printer.append({
					"tipe": "Usb port",
					"nama": p.get("nama", ""),
					"id_vendor": p.get("vid", ""),
					"id_produk": p.get("pid", "")
				})
				simpan_semua(file_printer, printer)
				QMB.information(None, tr("Berhasil"), tr("Printer sukses ditambahkan"))
								
		def find_printer():
			clear_widgets(kanan_frame)
			try:
				devices = usb.core.find(find_all=True)
				printer_ditemukan = []
				for device in devices:
					vid = device.idVendor
					pid = device.idProduct
					nama = "Unknown printer"
					if device.manufacturer and device.product:
						nama = device.manufacturer + " " + device.product
						
					printer_info = {
						"vid": vid,
						"pid": pid,
						"vid_hex": f"0x{vid:04x}",
						"pid_hex": f"0x{pid:04x}",
						"nama": nama
					}
					printer_ditemukan.append(printer_info)
				if printer_ditemukan:
					for p in printer_ditemukan:
						btn = label_photo(p.get("nama", ""), resource_path("Pictures/ddd.png"), icon_size)
						btn.setStyleSheet(style_button("lightgreen", font_size_normal))
						btn.clicked.connect(lambda *args, p=p: select_printer(p))
						kanan.addWidget(btn, alignment=rata_atas)
						munculkan(btn)
			except Exception as e:
				lbl = red_label(str(e))
				kanan.addWidget(lbl, alignment=rata_atas)
				munculkan(lbl)
			except usb.core.NoBackendError as e:
				lbl = red_label(str(e))
				kanan.addWidget(lbl, alignment=rata_atas)
				munculkan(lbl)
				
		def add_printer():
			clear_widgets(kanan_frame)
			type = combobox(font_size_normal, ["Usb port"])
			nama = entry(tr("Nama printer"), font_size_normal)
			idv = entry("Id vendor", font_size_normal)
			idp = entry("Id produk", font_size_normal)
			btn_save = button(tr("Simpan"), font_size_normal, bg)
				
			def simpan():
				tipe = type.currentText()
				n = nama.text()
				v = idv.text()
				p = idp.text()
				if not all([v, p]):
					QMB.warning(None, tr("Gagal"), tr("Id vendor dan id produk harus diisi"))
					return
				data = json.dumps([v, p])
				cursor.execute("INSERT INTO universal_printer (tipe, info) VALUES (?, ?)", (tipe, data))
				conn.commit()
				printer.clear()
				printer.append({
					"tipe": tipe,
					"nama": n,
					"id_vendor": v,
					"id_produk": p
				})
				simpan_semua(file_printer, printer)
				QMB.information(None, tr("Berhasil"), tr("Printer sukses ditambahkan"))
	                    
			btn_save.clicked.connect(simpan)
			for x in [type, idv, idp, btn_save]:
				kanan.addWidget(x, alignment=rata_atas)
				munculkan(x)
									
		def prepare_printer_layout():
			kiri, kanan = QFrame(), QFrame()
			for p in [kiri, kanan]:
				printer_layout.addWidget(p)
			return QVBoxLayout(kiri, alignment=rata_atas), QVBoxLayout(kanan, alignment=rata_atas), kanan
			
		def prepare_kiri_widgets():
			cari = label_photo(tr("Cari printer"), resource_path("Pictures/cari.png"), icon_size)
			add = label_photo(tr("Tambahkan printer manual"), resource_path("Pictures/ddd.png"), icon_size)
			for p in [cari, add]:
				p.setStyleSheet(style_button(bg, font_size_normal))
				kiri.addWidget(p, alignment=rata_atas)
				munculkan(p)
			cari.clicked.connect(find_printer)
			add.clicked.connect(add_printer)
		
		def set_opsi_server():
			online = QRadioButton("Online server")
			lan = QRadioButton("Local server")
			btn = button(tr("Simpan"), font_size_normal, bg)
			btn.clicked.connect(lambda: safe_run(simpan_opsi))
			if opsi_server.get("opsi", "Local server") == "Local server":
				lan.setChecked(True)
			else:
				online.setChecked(True)
				
			grup = QButtonGroup()
			for p in [online, lan]:
				p.setStyleSheet(f"""
					QRadioButton {{
						font-size: {font_size_normal}px;
					}}""")
				grup.addButton(p)
				layout_opsi.addWidget(p, alignment=rata_kiri)
			layout_opsi.addWidget(btn, alignment=rata_kiri)
			for p in [online, lan, btn]:
				munculkan(p)
			return grup
		
		def simpan_opsi():
			ch = grup.checkedButton()
			cek = ch.text()
			if askyesno(tr("Konfirmasi"), f"{tr('Gunakan')} {cek}?"):
				sp = set_spinner(window)
				try:
					res = requests.post(f"{SERVER_URL}/opsi_server_utama", json={"opsi": cek})
					if res.status_code == 200:
						opsi_server["opsi"] = cek
						simpan_semua(file_server, opsi_server)
						sp.deleteLater()
						QMB.information(None, tr("Berhasil"), f"{tr('Server digunakan')}: {cek}")
					else:
						sp.deleteLater()
						QMB.warning(None, "", str(res.status_code))
				except Exception as e:
					sp.deleteLater()
					QMB.critical(None, "", str(e))
									
		wd = prepare_parents()
		layout_info = QGridLayout(wd["fr koneksi"], alignment=rata_atas)
		layout_opsi = QHBoxLayout(wd["fr"], alignment=rata_kiri)
		printer_layout = QHBoxLayout(wd["fr printer"], alignment=rata_atas)
		kiri, kanan, kanan_frame = prepare_printer_layout()
		grup = set_opsi_server()		
		prepare_kiri_widgets()
		info_koneksi()
				
	def pengaturan_izin_akses():
		fitur_terpilih = {}
		pemilik = [
			"pemilik",
			"profil",
			"produk",
			"pengguna",
			"customer",
			"supplier",
			"pajak",
			"media bayar",
			"tulis struk",
			"biaya",
			"permintaan",
			"setujui permintaan",
			"hapus permintaan"
		]
		pro = [
			"edit profil",
			"hapus profil",
			"ganti foto profil",
			"hapus foto profil",
			"tambah keuangan",
			"reset keuangan"
		]
		produk = [
			"tambah produk baru",
			"detail produk",
			"tambah stok",
			"edit produk",
			"hapus produk",
			"multi price produk",
			"info kadaluarsa",
			"katalog produk",
			"info produk",
			"pengaturan margin",
			"daftar stok",
			"produk diskon",
			"produk tingkat",
			"ekspor dan impor",
			"hapus produk lanjutan"
		]
		user = [
			"tambah pengguna baru",
			"lihat riwayat pengguna",
			"atur shift",
			"tambah shift baru",
			"edit shift",
			"lihat anggota",
			"hapus shift"
		]
		customer_supplier = [
			"tambah customer",
			"tambah supplier",
			"edit customer",
			"edit supplier",
			"hapus customer",
			"hapus supplier",
			"atur pajak",
			"alat pembayaran",
			"pengaturan nota",
			"ambil struk",
			"tulis ulang struk"
		]
		pengeluaran = [
			"tambah pengeluaran",
			"edit pengeluaran",
			"ekspor pengeluaran",
			"hapus pengeluaran"
		]
		trx = [
			"transaksi pending",
			"transaksi offline",
			"ekspor transaksi",
			"hapus transaksi"
		]
		
		def simpan_izin():
			terpilih = [izin for izin, cek in fitur_terpilih.items() if cek.isChecked()]
			if not terpilih:
				return
			if askyesno(tr("Konfirmasi"), tr("Atur izin sekarang?")):
				if koneksi["connect"] == 1:
					data = {
						"status": cmb.currentText(),
						"izin": json.dumps(terpilih)
					}
					upload_data("tambah_izin", data, f"{tr('Izin terhadap')} {cmb.currentText().lower()} {tr('telah diperbarui')}")
				else:
					spin = set_spinner(window)
					QApplication.processEvents()
					cursor.execute("DELETE FROM hak_akses WHERE status = ?", (cmb.currentText(), ))
					cursor.execute("INSERT INTO hak_akses (status, izin) VALUES (?, ?)", (cmb.currentText(), json.dumps(terpilih)))
					conn.commit()
					spin.deleteLater()
					QMB.information(None, tr("Berhasil"), f"{tr('Izin terhadap')} {cmb.currentText().lower()} {tr('telah diperbarui')}")
						
		def prepare_layout():
			clear_widgets(f3)
			atas, bawah = QFrame(), QFrame()
			alay, balay = QHBoxLayout(atas, alignment=rata_kiri), QVBoxLayout(bawah)
			user = getData("user")
			status = list({p["status"] for p in user})
			cmb = combobox(font_size_normal, [tr("Pilih status user")] + status)
			btn = button(tr("Simpan"), font_size_normal, bg)
			btn.clicked.connect(lambda: safe_run(simpan_izin))
			for p in [cmb, btn]:
				alay.addWidget(p, alignment=rata_kiri)
			for p in [atas, bawah]:
				f3_layout.addWidget(p)
			return cmb, balay
		
		def render(data, judul):
			jdl = QLabel(judul)
			jdl.setStyleSheet(style_label_bold(font_size_judul))
			frame = QFrame()
			frame.setStyleSheet(style_frame_putih("transparent"))
			layout = QGridLayout(frame)
			for i, p in enumerate(data):
				baris, kolom = i // 4, i % 4
				cb = checkbutton(p.capitalize(), font_size_normal)
				fitur_terpilih[p] = cb
				layout.addWidget(cb, baris, kolom)
				
			for p in [jdl, frame]:
				bawah.addWidget(p, alignment=rata_atas)
				munculkan(p)
				
		def set_izin():
			status = cmb.currentText()
			if status.lower() in ["pilih status user", "choose user status"]:
				for p in list(fitur_terpilih.values()):
					p.setChecked(False)
				return
			izin = getData("hak_akses")
			if not izin:
				return
			for p in list(fitur_terpilih.values()):
				p.setChecked(False)
			found = False
			for p in izin:
				if p["status"].lower() == status.lower():
					iz = json.loads(p["izin"])
					for p in iz:
						fitur_terpilih[p].setChecked(True)
					found = True
					break
			if not found:
				for p in list(fitur_terpilih.values()):
					p.setChecked(False)
				
		cmb, bawah = prepare_layout()
		render(pemilik, tr("IZIN OWNER"))
		render(pro, tr("IZIN PROFIL"))
		render(produk, tr("IZIN PENGELOLA PRODUK"))
		render(user, tr("IZIN PENGGUNA"))
		render(customer_supplier, tr("IZIN CUSTOMER, SUPPLIER, PAJAK, ALAT PEMBAYARAN"))
		render(pengeluaran, tr("IZIN PENGELUARAN"))
		render(trx, tr("IZIN TRANSAKSI"))
		cmb.currentTextChanged.connect(set_izin)
				
	def pengaturan_tema():
		def animation_set():
			cek = wd["anim"].isChecked()
			animasi["yes"] = 1 if cek else 0
			simpan_semua(file_animasi, animasi)
			
		def prepare_layout():
			clear_widgets(f3)
			d = {
				"main_color": QLabel(tr("WARNA UTAMA")),
				"atas": QFrame(),
				"main_bg": QLabel(tr("WALLPAPER FRAME UTAMA")),
				"bawah": QFrame(),
				"normal": entry(tr("Masukkan ukuran huruf normal..."), font_size_normal),
				"judul": entry(tr("Masukkan ukuran huruf judul..."), font_size_normal),
				"icon": entry(tr("Masukkan ukuran ikon..."), font_size_normal),
				"anim": checkbutton(tr("Sertakan animasi"), font_size_normal),
				"btn_simpan": button(tr("Simpan"), font_size_normal, bg),
				"choose": button(tr("Pilih wallpaper login"), font_size_normal, bg)
			}
			cursor.execute("SELECT font_normal, font_judul, ikon FROM pengaturan_tema")
			tm = cursor.fetchone()
			d["normal"].setText(str(tm["font_normal"]) if tm else "10")
			d["judul"].setText(str(tm["font_judul"]) if tm else "10")
			d["icon"].setText(str(tm["ikon"]) if tm else "15")
			d["anim"].setChecked(animasi["yes"])
			
			for p in list(d.values()):
				f3_layout.addWidget(p)
				munculkan(p)
			d["btn_simpan"].clicked.connect(save_size)
			d["choose"].clicked.connect(wal_choose)
			d["anim"].toggled.connect(animation_set)
			for p in [d["main_color"], d["main_bg"]]:
				p.setStyleSheet(f"""
					QLabel {{
						font-size: {font_size_judul}px;
						background-color: transparent;
						font-weight: bold;
					}}""")
			d["bawah"].setStyleSheet(style_frame_putih(bg))
			return d
		
		def set_layout():
			return QGridLayout(wd["atas"]), QGridLayout(wd["bawah"])
		
		def update_bg(p):
			teks = p.replace(" ", "").replace("-", " ").split()
			a = teks[0]
			b = teks[1]
			if askyesno(tr("Konfirmasi"), f"{tr('Update latar utama dengan')} {a}/{b}?"):
				cursor.execute("SELECT latar, warna_huruf FROM pengaturan_tema")
				tm = cursor.fetchone()
				if tm:
					cursor.execute("UPDATE pengaturan_tema SET latar = ?, warna_huruf = ? WHERE id = ?", (a, b, 1))
				else:
					cursor.execute("INSERT INTO pengaturan_tema (latar, warna_huruf) VALUES (?, ?)", (a, b))
				conn.commit()
				QMB.information(None, tr("Berhasil"), tr("Warna latar dan huruf telah diperbarui"))
				
		def prepare_wallpaper():
			path_list = [
				"Pictures/wall_default.png",
				"Pictures/wall_01.png",
				"Pictures/wall_02.png",
				"Pictures/wall_03.png",
				"Pictures/wall_04.png",
				"Pictures/walpaper_login.png"
			]
			for i in range(len(path_list)):
				baris, kolom = i // 3, i % 3
				btn = QPushButton()
				btn.setIcon(QIcon(resource_path(path_list[i])))
				btn.setIconSize(QSize(100,100))
				btn.setStyleSheet(style_button("transparent", font_size_normal))
				btn.clicked.connect(lambda *args, p=resource_path(path_list[i]): give(p))
				layout_bawah.addWidget(btn, baris, kolom)
						
		def save_size():
			font_normal = wd["normal"].text().strip()
			font_judul = wd["judul"].text().strip()
			ic = wd["icon"].text().strip()
			if not all([font_normal, font_judul, ic]):
				QMB.warning(None, tr("Gagal"), tr("Semua entry harus diisi"))
				return
			cursor.execute("SELECT * FROM pengaturan_tema")
			tm = cursor.fetchone()
			if tm:
				cursor.execute("UPDATE pengaturan_tema SET font_normal = ?, font_judul = ?, ikon = ? WHERE id = ?", (font_normal, font_judul, ic, 1))
			else:
				cursor.execute("INSERT INTO pengaturan_tema (font_normal, font_judul, ikon) VALUES (?, ?, ?)", (font_normal, font_judul, ic))
			conn.commit()
			QMB.information(None, tr("Berhasil"), tr("Warna latar dan huruf telah diperbarui"))
		
		def give(path):
			path_tujuan = os.path.join(folder_foto_profil, "Wallpaperforrightframeinmyappveryimportantandmostpowerfull.png")
			if not path and not path_tujuan:
				return
			shutil.copy(path, path_tujuan)
			QMB.information(None, tr("Berhasil"), tr("Wallpaper halaman utama telah diperbarui"))
				
		def wal_choose():
			path, _ = QFileDialog.getSaveFileName()
			path_tujuan = os.path.join(folder_foto_profil, "walpaper login.png")
			if not path and not path_tujuan:
				return
			shutil.copy(path, path_tujuan)
			QMB.information(None, tr("Berhasil"), tr("Wallpaper halaman login diperbarui"))
										
		def prepare_button_for_bg():
			list_warna_background = [
				"#57EACF - black",
				"#5B714C - white",
				"#924444 - white",
				"#445792 - white",
				"#AFBBDF - black",
				"skyblue - black",
				"lightgreen - black",
				"lightblue - black"
			]
			for i, x in enumerate(list_warna_background):
				baris = i // 3
				kolom = i % 3
				teks = x.replace(" ", "").replace("-", " ").split()
				background = teks[0]
				foreground = teks[1]
				btn = QPushButton()
				btn.setStyleSheet(f"""
					QPushButton {{
						background-color: {background};
						font-size: {font_size_normal}px;
						color: {foreground};
						border: 0px solid {background};
						border-radius: 2px;
						padding: 20px;
					}}
					QPushButton:hover {{
						background-color: {foreground};
						color: {background};
						border: 0.5px solid black;
					}}
					QPushButton:pressed {{
						border: 0.5px solid black;
					}}
				""")
				btn.clicked.connect(lambda *args, p=x: update_bg(p))
				layout_atas.addWidget(btn, baris, kolom)
	
		wd = prepare_layout()
		layout_atas, layout_bawah = set_layout()
		prepare_button_for_bg()
		prepare_wallpaper()
		
	def prepare_f2_buttons():
		try:
			clear_widgets(f2)
			list_btn = [
				("Bahasa", "Pictures/pengaturan_bahasa.png", pengaturan_bahasa),
				("Mata uang", "Pictures/mata_uang.png", pengaturan_mata_uang),
				("Format waktu", "Pictures/pengaturan_format_waktu.png", pengaturan_format_waktu),
				("Koneksi", "Pictures/konsev.png", pengaturan_koneksi),
				("Hak akses", "Pictures/akses.png", pengaturan_izin_akses),
				("Tema", "Pictures/tema.png", lambda: safe_run(pengaturan_tema)),
				("Kelola database", "Pictures/kelola database.png", kelola_database)
			
			]

			for a, b, c in list_btn:
				btn = button_photo(tr(a), resource_path(b), icon_size, c)
				btn.setStyleSheet(f2_btn(font_size_normal))
				f2_layout.addWidget(btn, alignment=rata_kiri)
		except Exception as e:
			QMB.information(None, "", str(e))
			
	prepare_f2_buttons()
	pengaturan_bahasa()

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

		return {"folder": daftar_folder, "folder_and_file": list_folder_and_files}
	else:
		return "Not found"
						
def kelola_database():
	def prepare_data():
		if koneksi["connect"] == 1:
			if server_alive():
				try:
					res = requests.get(f"{SERVER_URL}/see_main_database")
					if res.status_code == 200:
						data = res.json()
					else:
						data = {}
				except Exception as e:
					QMB.critical(None, "Error", str(e))
			else:
				QMB.warning(None, "Offline", tr("Server tidak aktif"))
		else:
			data = see_main_database()
		return data

	def open_file():
		nonlocal item_selected
		if not item_selected:
			return
		clear_widgets(bawah_fr)
		path = next((p for p in paths if item_selected in p), None)
		label = QLabel()
		label.setStyleSheet(style_label(font_size_judul))
		bawah.addWidget(label)
		if koneksi["connect"] == 1:
			try:
				res = requests.post(f"{SERVER_URL}/take_file", json={"path": path})
				if res.status_code == 200:
					if path.endswith((".jpg", ".jpeg", ".png")):
						pixmap = QPixmap()
						pixmap.loadFromData(res.content)
						pix = pixmap.scaled(500,500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
						label.setPixmap(pix)
						label.setAlignment(Qt.AlignCenter)
					elif path.endswith(".txt"):
						teks = res.text
						label.setText(teks)
					elif path.endswith(".json"):
						data = res.json()
						teks = json.dumps(data, indent=4, ensure_ascii=False)
						label.setText(str(teks))
					else:
						QMB.warning(None, tr("Gagal"), tr("File tidak didukung"))
			except Exception as e:
				label.setText(str(e))
		else:
			if path.endswith((".jpg", ".jpeg", ".png")):
				pix = QPixmap(path)
				pixmap = pix.scaled(500,500,Qt.KeepAspectRatio, Qt.SmoothTransformation)
				label.setPixmap(pixmap)
				label.setAlignment(Qt.AlignCenter)
			elif path.endswith(".txt"):
				with open(path, "r") as f:
					teks = f.read()
				label.setText(teks)
			elif path.endswith(".json"):
				with open(path, "r") as f:
					data = json.load(f)
				teks = json.dumps(data, indent=4, ensure_ascii=False)
				label.setText(str(teks))
			else:
				QMB.warning(None, tr("Gagal"), tr("File tidak didukung"))
		munculkan(label)
							
	def open_folder():
		nonlocal item_selected
		if not item_selected:
			return
		clear_widgets(bawah_fr)
		files = next((p.get("files", []) for p in folder_and_files if p.get("folder", "").lower() == item_selected.lower()), None)
		if not files:
			bawah.addWidget(red_label(tr("Folder kosong")))
			return
		
		for i, p in enumerate(files):
			baris, kolom = i // 3, i % 3
			btn = button(p, font_size_normal, "transparent")
			btn.clicked.connect(lambda *args, p=p: safe_run(select, p))
			bawah.addWidget(btn, baris, kolom, alignment=rata_kiri)
			munculkan(btn)
	
	def select(item):
		nonlocal item_selected
		item_selected = item
		lbl.setText(tr("Terpilih") + ": " + item_selected)
		
	def open_validation():
		if not item_selected:
			return
		if item_selected.endswith((".jpg", ".jpeg", ".png", ".txt", ".json", ".db")):
			open_file()
		else:
			open_folder()
			
	def delete_now(path_hapus):
		if koneksi["connect"] == 1:
			upload_data("hapus_file", {"path": path_hapus}, f"{item_selected} {tr('telah dihapus')}")
		else:
			try:
				os.remove(path_hapus)
				QMB.information(None, tr("Berhasil"), f"{item_selected} {tr('telah dihapus')}")
			except Exception as e:
				QMB.critical(None, tr("Gagal"), str(e))
	
	def delete_folder(path_folder):
		if koneksi["connect"] == 1:
			upload_data("hapus_folder", {"path": path_folder}, f"{item_selected} {tr('telah dihapus')}")
		else:
			try:
				shutil.rmtree(path_folder)
				QMB.information(None, tr("Berhasil"), f"{item_selected} {tr('telah dihapus')}")
			except Exception as e:
				QMB.critical(None, tr("Gagal"), str(e))
		
	def hapus_validation():
		if not item_selected:
			return
		if askyesno(tr("Konfirmasi"), f"{tr('Anda yakin ingin menghapus')} {item_selected}?"):
			path = next((p for p in paths if item_selected in p), None)
			fold = next((p for p in path_folder if item_selected in p), None)
			if item_selected.endswith((".jpg", ".jpeg", ".png", ".txt", ".json", ".db")):
				safe_run(delete_now, path)
			else:
				safe_run(delete_folder, fold)
					
	def tampilkan_folder():
		clear_widgets(bawah_fr)
		for i in range(len(folder)):
			baris = i // 5
			kolom = i % 5
			btn = QToolButton()
			btn.setText(folder[i])
			btn.setStyleSheet(f"""
				QToolButton {{
					background-color: transparent;
					font-size: {font_size_normal}px;
					border: 0px solid transparent;
					border-radius: 2px;
					padding: 5px;
				}}
				QToolButton:hover {{
					border: 1px solid black;
					background-color: lightgrey;
					border-radius: 2px;
				}}""")
			btn.setIcon(QIcon(resource_path("Pictures/folder_icon.png")))
			btn.setIconSize(QSize(50,50))
			btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
			btn.clicked.connect(lambda *args, x=folder[i]: safe_run(select, x))
			bawah.addWidget(btn, baris, kolom)
			munculkan(btn)

	def get_all_paths():
		if koneksi["connect"] == 1:
			return get_server_file_paths()
		else:
			return get_lokal_file_paths(basedir)
	
	def get_folders(main_folder):
		paths = []
		for p in os.listdir(main_folder):
			pt = os.path.join(main_folder, p)
			if os.path.isdir(pt):
				paths.append(pt)
				paths.extend(get_folders(pt))
		return paths
		
	def get_path_folder():
		if koneksi["connect"] == 1:
			if server_alive():
				try:
					res = requests.get(f"{SERVER_URL}/get_path_folders")
					if res.status_code == 200:
						return res.json()
				except Exception:
					return []
		else:
			return get_folders(basedir)
			
	def prepare_frames():
		top, bottom = QFrame(), QFrame()
		lt, lb = QHBoxLayout(top, alignment=rata_kiri), QGridLayout(bottom)
		clear_widgets(f3)
		bottom.setStyleSheet(style_frame_putih("transparent"))
		for p in [top, bottom]:
			f3_layout.addWidget(p)
		return lt, bottom, lb
		
	def do_restore():
		def get_backup_folder_paths():
			if koneksi["connect"] == 1:
				try:
					res = requests.get(f"{SERVER_URL}/ambil_info_backup")
					if res.status_code == 200:
						return res.json()
				except Exception as e:
					QMB.critical(None, "", str(e))
			else:
				return ambil_info_backup()
		
		def open_folder_backup(folder):
			def get_file_paths_backup(folder):
				if koneksi["connect"] == 1:
					try:
						res = requests.post(f"{SERVER_URL}/ambil_path_file_backup", json={"path": folder})
						if res.status_code == 200:
							return res.json()
					except Exception as e:
						QMB.critical(None, "", str(e))
				else:
					return ambil_path_file_backup(folder)
			
			files = get_file_paths_backup(folder)
			clear_widgets(bawah_fr)
			atas, bawh = QFrame(), QFrame()
			alay, balay = QGridLayout(atas), QHBoxLayout(bawh)
			for i, p in enumerate([atas, bawh]):
				bawah.addWidget(p, i, 0)
				munculkan(p)
				
			fil = files.get("path files", [])
			ori = files.get("path original", [])
			d, l = {}, []
			for i, p in enumerate(fil):
				nama = os.path.basename(p)
				clb = checkbutton(nama, font_size_normal)
				d[nama] = clb
				l.append(clb)
				alay.addWidget(clb, i//3, i%3, alignment=rata_kiri)
			
			def pilih_semua():
				for p in l:
					p.setChecked(pilih.isChecked())
			
			def muat_data():
				terpilih = [nama for nama, cek in d.items() if cek.isChecked()]
				if not terpilih:
					return
				if askyesno(tr("Konfirmasi"), f"{tr('Restore data')} {len(terpilih)} item {tr('sekarang')}?"):
					if koneksi["connect"] == 1:
						data = {
							"pilih": terpilih,
							"path": fil,
							"path ori": ori
						}
						upload_data("lakukan_restore", data, f"{tr('Sebanyak')} {len(terpilih)} item {tr('telah dipulihkan')}!")
					else:
						map_asal = {p.split("/")[-1].lower(): p for p in fil}
						map_tujuan = {p.split("/")[-1].lower(): p for p in ori}
						for p in terpilih:
							shutil.copy(map_asal.get(p.lower(), ""), map_tujuan.get(p.lower(), ""))
						QMB.information(None, tr("Berhasil"), f"{tr('Sebanyak')} {len(terpilih)} {tr('telah berhasil dipulihkan')}")
									
			pilih = checkbutton(tr("Pilih semua"), font_size_normal)
			btn = button(tr("Muat sekarang"), font_size_normal, bg)
			for p in [pilih, btn]:
				balay.addWidget(p)
			pilih.toggled.connect(pilih_semua)
			btn.clicked.connect(lambda: safe_run(muat_data))
			
		def tampilkan_folders():
			clear_widgets(bawah_fr)
			for i, p in enumerate(folders):
				nama = os.path.basename(p)
				btn = button(nama, font_size_normal, "transparent")
				btn.clicked.connect(lambda *args, p=p: safe_run(open_folder_backup, p))
				bawah.addWidget(btn, i//3, i%3, alignment=rata_kiri)
				munculkan(btn)
								
		folders = get_backup_folder_paths()
		tampilkan_folders()
		
	def do_backup():
		def set_frames():
			atas, baah = QFrame(), QFrame()
			alay, balay = QGridLayout(atas, alignment=rata_atas), QHBoxLayout(baah, alignment=rata_kiri)
			clear_widgets(bawah_fr)
			for i, p in enumerate([atas, baah]):
				bawah.addWidget(p, i, 0)
				munculkan(p)
			return alay, balay
		
		def set_bawah():
			wd = {
				"cek": checkbutton(tr("Pilih semua"), font_size_normal),
				"on": button(tr("Backup online"), font_size_normal, bg),
				"off": button(tr("Backup offline"), font_size_normal, bg)
			}
			wd["on"].clicked.connect(backup_online)
			wd["off"].clicked.connect(backup_offline)
			for p in list(wd.values()):
				b.addWidget(p, alignment=rata_kiri)
			return wd
			
		def set_files():
			for i, p in enumerate(paths):
				nama = os.path.basename(p)
				cek = checkbutton(nama, font_size_normal)
				dicti[nama] = cek
				listi.append(cek)
				a.addWidget(cek, i//3, i%3)
		
		def pilih_semua():
			cek = wd["cek"].isChecked()
			for p in listi:
				p.setChecked(cek)
		
		def backup_offline():
			if askyesno(tr("Konfirmasi"), tr("Backup sekarang?")):
				terpilih = [file for file, cek in dicti.items() if cek.isChecked()]
				if not terpilih:
					return
				path_files = []
				for p in terpilih:
					for q in get_lokal_file_paths(basedir):
						if p.lower() in q.lower():
							path_files.append(q)
				folder = datetime.now().strftime("Backup %A, %d %B %Y %H_%M_%S")
				path_folder = os.path.join(folder_backup, folder)
				os.makedirs(path_folder, exist_ok=True)
				try:
					for p in path_files:
						nama_file = os.path.basename(p)
						path_tujuan = os.path.join(path_folder, nama_file)
						shutil.copy(p, path_tujuan)
					info = {
						"waktu": now_str(),
						"original path": path_files
					}
					info_backup = os.path.join(path_folder, "Info.json")
					with open(info_backup, "w", encoding="utf-8") as f:
						json.dump(info, f, indent=4, ensure_ascii=False)
						
					QMB.information(None, tr("Berhasil"), f"{len(path_files)} file {tr('telah dicadangkan')}")
				except FileNotFoundError as e:
					QMB.critical(None, "Error", str(e))
				except Exception as e:
					QMB.critical(None, "Error", str(e))
							
		def backup_online():
			if koneksi["connect"] == 0:
				QMB.warning(None, tr("Gagal"), tr("Anda sedang offline"))
				return
			if askyesno(tr("Konfirmasi"), tr("Cadangkan sekarang?")):
				terpilih = [file for file, cek in dicti.items() if cek.isChecked()]
				if not terpilih:
					return
				path_files = []
				for p in terpilih:
					for q in get_server_file_paths():
						if p.lower() in q.lower():
							path_files.append(q)
				if server_alive():
					upload_data("lakukan_backup", path_files, f"{len(path_files)} data {tr('telah dicadangkan')}")
				else:
					QMB.warning(None, tr("Gagal"), tr("Sepertinya server sedang offline"))
							
		dicti = {}
		listi = []					
		a, b = set_frames()
		wd = set_bawah()
		set_files()
		wd["cek"].toggled.connect(pilih_semua)
		
	def prepare_atas_widgets():
		kiri, kanan = QFrame(), QFrame()
		set_expanding(kiri, expand, fix)
		set_expanding(kanan, expand, fix)
		kiri_wd = {
			"folder": button("Folder", font_size_normal, "transparent"),
			"backup": button("Backup", font_size_normal, "transparent"),
			"restore": button("Restore", font_size_normal, "transparent")
		}
		kanan_wd = {
			"buka": button(tr("Buka"), font_size_normal, "transparent"),
			"hapus": button(tr("Hapus"), font_size_normal, "transparent"),
			"selected": QLabel()
		}
		kanan_wd["selected"].setStyleSheet(style_label_bold(font_size_normal))
		kanan_wd["buka"].clicked.connect(open_validation)
		kanan_wd["hapus"].clicked.connect(hapus_validation)
		kiri_wd["folder"].clicked.connect(tampilkan_folder)
		kiri_wd["backup"].clicked.connect(lambda: safe_run(do_backup))
		kiri_wd["restore"].clicked.connect(do_restore)
		lk, lkn = QHBoxLayout(kiri, alignment=rata_kiri), QHBoxLayout(kanan, alignment=rata_kiri)
		for p in list(kiri_wd.values()):
			lk.addWidget(p, alignment=rata_kiri)
		for p in list(kanan_wd.values()):
			lkn.addWidget(p, alignment=rata_kiri)
		for p in [kiri, kanan]:
			atas.addWidget(p)
		return kanan_wd["selected"]
	
	item_selected = None
	paths = get_all_paths()
	path_folder = get_path_folder()
	atas, bawah_fr, bawah = prepare_frames()
	lbl = prepare_atas_widgets()
	data = prepare_data()
	folder = data.get("folder", [])
	folder_and_files = data.get("folder_and_file", [])		
	tampilkan_folder()

def tentang():
	print()
	
def keluar():
	if askyesno(tr("Konfirmasi"), tr("Apakah Anda ingin menyimpan login Anda. Klik yes untuk lanjutkan")):
		app.quit()
	else:
		cursor.execute("DELETE FROM operator")
		conn.commit()
		app.quit()
		
def filter_data_periode(data, periode, operator=None):
	if periode in ["", None, "semua periode", "all period"]:
		dt = data
	else:
		prd_id = ["hari ini", "minggu ini", "bulan ini"]
		prd_eng = ["today", "this week", "this month"]
		func = [periode_hari, periode_minggu, periode_bulan]
		idx = prd_id.index(periode) if periode in prd_id else prd_eng.index(periode)
		start, end = func[idx]()
		dt = [p for p in data if start <= parse_date(p["waktu"]) <= end]
	if operator in [None, "", "semua operator", "all operator"]:
		return dt
	else:
		return [p for p in dt if p["operator"].lower() == operator]
		
def prepare_data_perbulan(bulan, riwayat=[], pengeluaran=[]):
	start, end = rentang(bulan)
	data = [p for p in riwayat if start <= parse_date(p["waktu"]) <= end]
	penge = [p for p in pengeluaran if start <= parse_date(p["waktu"]) <= end]
	masuk, hpp, diskon, tingkat = 0, 0, 0, 0
	for p in data:
		keranjang = json.loads(p["data_belanja"])
		for k in keranjang:
			masuk += k.get("harga_asli", 0) * k.get("qty_asli", 0)
			hpp += k.get("subtotal_modal", 0)
			diskon += k.get("potongan_diskon", 0)
			tingkat += k.get("potongan_tingkat", 0)
	keluar = sum(p["total"] for p in penge)
	pemasukan_bersih = masuk - diskon - tingkat
	laba_kotor = pemasukan_bersih - hpp
	laba_bersih = laba_kotor - keluar
	return {
		"Pemasukan kotor": masuk,
		"Pengeluaran": keluar,
		"Pemasukan bersih": pemasukan_bersih,
		"Keuntungan kotor": laba_kotor,
		"Keuntungan bersih": laba_bersih
	}
		
class LaporanCepat:
	def __init__(
		self,
		pengeluaran=None,
		riwayat=None,
		user=None
	):
		self.pengeluaran = pengeluaran or []
		self.riwayat = riwayat or []
		self.user = user or []
		
	def ekspor_csv(self):
		if askyesno(tr("Konfirmasi"), tr("Anda akan ekspor laporan cepat ke file .csv")):
			path = choose_save_path(f"Laporan cepat {datetime.now().strftime('%y%m%d')}.csv")
			if not path:
				return
			try:
				with open(path, "w", encoding="utf-8", newline="") as f:
					w = csv.writer(f)
					w.writerow(["Tanggal batas awal", ":", self.w["date_mulai"].text().strip()])
					w.writerow(["Tanggal batas akhir", ":", self.w["date_akhir"].text().strip()])
					w.writerow(["Periode", ":", self.w["prd"].currentText()])
					w.writerow(["Operator", ":", self.w["opr"].currentText()])
					w.writerow([])
					format = ["transaksi", "unit"]
					for i, (a, b) in enumerate(self.data.items()):
						w.writerow([a.upper(), ":", format_unit(b, format[i]) if i in [0, 1] else pretty_money(b)])
					
				QMB.information(None, tr("Berhasil"), tr("Laporan cepat telah berhasil diekspor ke file csv"))
			except Exception as e:
				QMB.critical(None, "", str(e))
								
	def ekspor_pdf(self):
		def style_tabel(tabel, data, warna_ganjil=colors.aliceblue, warna_genap=colors.mintcream):
			style = [
				("BOX", (0,0), (-1,-1), 0.5, colors.black),
				("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold")
			]
			for i in range(len(data)):
				warna = warna_genap if i % 2 == 0 else warna_ganjil
				style.append(("BACKGROUND", (0,i), (-1,i), warna))
			tabel.setStyle(TableStyle(style))
			return tabel
				
		start = self.w["date_mulai"].text().strip()
		end = self.w["date_akhir"].text().strip()
		prd = self.w["prd"].currentText()
		opr = self.w["opr"].currentText()
		if askyesno(tr("Konfirmasi"), tr("Ekspor laporan cepat sekarang?")):
			path = choose_save_path(f"Laporan cepat {datetime.now().strftime('%y%m%d')}.pdf")
			if not path:
				return
			try:
				doc = SimpleDocTemplate(path)
				c = []
				data1 = [
					[mp("Tanggal batas awal"), ":", mp(start)],
					[mp("Tanggal batas akhir"), ":", mp(end)],
					[mp("Periode"), ":", mp(prd)],
					[mp("Operator"), ":", mp(opr)]
				]
				table1 = Table(data1)
				table1.setStyle(TableStyle([
					("BOX", (0,0), (-1,-1), 0.5, colors.blue),
					("ROUNDEDCORNERS", (0,0), (-1,-1), 5)
				]))
				data2 = []
				form = ["transaksi", "unit"]
				for i, (a, b) in enumerate(self.data.items()):
					tup = [mp(a.upper()), ":", mp(format_unit(b, form[i]) if i in [0, 1] else pretty_money(b))]
					data2.append(tup)
				c.append(table1)
				c.append(Spacer(1,20))
				table2 = Table(data2)
				table2_style = style_tabel(table2, data2)
				c.append(table2_style)
				doc.build(c)
				QMB.information(None, tr("Berhasil"), tr("Data berhasil diekspor ke file pdf"))
			except Exception as e:
				QMB.critical(None, "", str(e))
	
	def set_atas(self):
		self.w = {
			"mulai": label(tr("Mulai"), color="darkgreen"),
			"date_mulai": make_date(),
			"akhir": label(tr("Selesai"), color="darkgreen"),
			"date_akhir": make_date(),
			"prd": combobox(font_size_normal, [tr("Semua periode"), tr("Bulan ini"), tr("Minggu ini"), tr("Hari ini")]),
			"opr": combobox(font_size_normal, [tr("Semua operator")] + list({p["nama"] for p in self.user}))
		}
		for i, p in enumerate(self.w.values()):
			self.atas_layout.addWidget(p, 0, i, alignment=rata_kiri)
		
		btn = [
			button(tr("Filter per tanggal"), font_size_normal, bg),
			button(tr("Filter periode"), font_size_normal, bg),
			button(tr("Ekspor PDF"), font_size_normal, bg),
			button(tr("Ekspor CSV"), font_size_normal, bg)
		]
		cm = [
			self.filter_tanggal,
			self.filter_periode,
			self.ekspor_pdf,
			self.ekspor_csv
		]
		for i, p in enumerate(btn):
			p.clicked.connect(lambda *args, c=cm[i]: safe_run(c))
			self.atas_layout.addWidget(p, 1, i, alignment=rata_kiri)
		
	def reset_data(self):
		for k in self.data:
			self.data[k] = 0
				
	def prepare_data(self, start, end, opr):
		riwayat = self.riwayat
		pengeluaran = self.pengeluaran
		data = self.data
		self.reset_data()
		filtered_trx = []
		filtered_exp = []
		if opr.lower() in ["all operator", "semua operator"]:
			if start and end:
				filtered_trx = [p for p in riwayat if start <= parse_date(p["waktu"]) <= end]
				filtered_exp = [p for p in pengeluaran if start <= parse_date(p["waktu"]) <= end]
			else:
				filtered_trx = [p for p in riwayat]
				filtered_exp = [p for p in pengeluaran]
		else:
			if start and end:
				filtered_trx = [p for p in riwayat if p["operator"].lower() == opr.lower() and start <= parse_date(p["waktu"]) <= end]
				filtered_exp = [p for p in pengeluaran if p["operator"].lower() == opr.lower() and start <= parse_date(p["waktu"]) <= end]
			else:
				filtered_trx = [p for p in riwayat if p["operator"].lower() == opr.lower()]
				filtered_exp = [p for p in pengeluaran if p["operator"].lower() == opr.lower()]
			
		for p in filtered_trx:
			data["total transaksi"] += 1
			data["total pajak"] += p["kena_pajak"]
			keranjang = json.loads(p["data_belanja"])
			for d in keranjang:
				data["total produk terjual"] += d.get("qty_asli", 0)
				data["penjualan kotor"] += d.get("harga_asli", 0) * d.get("qty_asli", 0)
				data["total diskon"] += d.get("potongan_diskon", 0)
				data["total promo tingkat"] += d.get("potongan_tingkat", 0)
				data["total harga pokok penjualan"] += d.get("subtotal_modal", 0)
			
		for p in filtered_exp:
			data["total pengeluaran"] += p["total"]
				
		data["penjualan bersih"] += data["penjualan kotor"] - data["total diskon"] - data["total promo tingkat"]
		data["laba kotor"] += data["penjualan bersih"] - data["total harga pokok penjualan"]
		data["laba bersih"] += data["laba kotor"] - data["total pengeluaran"]
	
	def tampilkan_data(self):
		satuan = ["transaksi", "unit"]
		for i, (p, q) in enumerate(self.data.items()):
			self.model.appendRow([
				QStandardItem(p.upper()),
				QStandardItem(format_unit(q, satuan[i]) if i in [0, 1] else pretty_money(q))		
			])
		munculkan(self.tabel)
		
	def tampilkan_grafik(self):
		clear_widgets(self.bawah)
		grafik_batang_penjualan = diagram_batang(["Jumlah transaksi", "Produk terjual"], [self.data["total transaksi"], self.data["total produk terjual"]], f"Perbandingan jumlah transaksi dan jumlah produk terjual")
		self.bawah_layout.addWidget(grafik_batang_penjualan, alignment=rata_atas)	
		grafik_kue = diagram_bolu(["Laba kotor", "Pengeluaran"], [self.data["laba kotor"], self.data["total pengeluaran"]], f"Perbandingan laba kotor dan pengeluaran")
		self.bawah_layout.addWidget(grafik_kue, alignment=rata_atas)	
		for p in [grafik_batang_penjualan, grafik_kue]:
			p.setMinimumSize(300,300)
			munculkan(p)
									
	def filter_tanggal(self):
		self.w["prd"].setCurrentText(tr("Semua periode"))
		start = datetime.strptime(self.w["date_mulai"].text().strip(), "%d/%m/%y")
		end = datetime.strptime(self.w["date_akhir"].text().strip(), "%d/%m/%y")
		opr = self.w["opr"].currentText()
		self.prepare_data(start, end, opr)
		self.tampilkan_data()
		self.tampilkan_grafik()
		
	def filter_periode(self):
		for p in [self.w["date_mulai"], self.w["date_akhir"]]:
			p.setDate(QDate.currentDate())
		list_periode = ["bulan ini", "minggu ini", "hari ini"]
		list_periode_english = ["this month", "this week", "today"]
		list_func = [periode_bulan, periode_minggu, periode_hari]
		pr = self.w["prd"].currentText().lower()
		opr = self.w["opr"].currentText()
		if pr in ["semua periode", "all period"]:
			start, end = None, None
		else:
			idx = list_periode.index(pr) if pr in list_periode else list_periode_english.index(pr)
			start, end = list_func[idx]()
		self.prepare_data(start, end, opr)
		self.tampilkan_data()
		self.tampilkan_grafik()
			
	def prepare_frames(self):
		self.atas, self.atas_layout = frame(QGridLayout, bg="rgba(0,120,100,0.06)", rata=rata_kiri)
		self.tabel, self.model = table_maker(["Aspek", "Value"])
		self.bawah, self.bawah_layout = frame(QHBoxLayout, bg="transparent")
		
		self.tabel.verticalHeader().hide()
		for p in [self.atas, self.tabel, self.bawah]:
			f3_layout.addWidget(p, alignment=rata_atas)
			
	def setup(self):
		self.data = {
			"total transaksi": 0,
			"total produk terjual": 0,
			"penjualan kotor": 0,
			"total diskon": 0,
			"total promo tingkat": 0,
			"total harga pokok penjualan": 0,
			"penjualan bersih": 0,
			"laba kotor": 0,
			"total pengeluaran": 0,
			"total pajak": 0,
			"laba bersih": 0
		}
		clear_widgets(f3)
		self.prepare_frames()
		self.set_atas()
					
class LaporanPenjualanProduk:
	def __init__(self, tengah, tengah_layout, bawah, bawah_layout, period, operator, riwayat=None):
		self.prd = period
		self.opr = operator
		self.riwayat = riwayat or []
		self.tengah = tengah
		self.tengah_layout = tengah_layout
		self.bawah = bawah
		self.bawah_layout = bawah_layout
	
	def filter_data(self):
		self.periode = self.prd.currentText().strip().lower()
		self.operator = self.opr.currentText().strip().lower()
		self.data = filter_data_periode(self.riwayat, self.periode, operator=self.operator)
		
	def olah_data(self):
		try:
			self.terjual, self.masuk, self.untung = 0, 0, 0
			self.data_for_tabel = []
			for p in self.data:
				self.masuk += p["total"]
				self.untung += p["total_laba"]
				keranjang = json.loads(p["data_belanja"])
				for k in keranjang:
					self.terjual += k.get("qty_asli", 0)
					for d in self.data_for_tabel:
						if d.get("id_produk", "") == k.get("id", ""):
							d["terjual"] += k.get("qty_asli", 0)
							d["laba"] += k.get("laba", 0)
							d["total"] += k.get("subtotal_jual", 0)
							d["diskon"] += k.get("potongan_diskon", 0)
							d["tingkat"] += k.get("potongan_tingkat", 0)
							break
					else:
						self.data_for_tabel.append({
							"id_produk": k.get("id", ""),
							"barcode": k.get("barcode", ""),
							"nama": k.get("nama", ""),
							"terjual": k.get("qty_asli", 0),
							"laba": k.get("laba", 0),
							"total": k.get("subtotal_jual", 0),
							"diskon": k.get("potongan_diskon", 0),
							"tingkat": k.get("potongan_tingkat", 0)
						})	
		except Exception as e:
			QMB.critical(None, "", str(e))
			
	def filter_data_sebelumnya(self, tipe):
		if self.periode in [None, "", "semua periode", "all period"]:
			return
		if self.periode in ["hari ini", "today"]:
			start, end = kemarin()
		elif self.periode in ["minggu ini", "this week"]:
			start, end = minggu_lalu()
		else:
			start, end = bulan_lalu()
		data = [p for p in self.riwayat if start <= parse_date(p["waktu"]) <= end]
		aspek = 0
		value = 0
		if tipe == "terjual":
			value = self.terjual
			for p in data:
				krj = json.loads(p["data_belanja"])
				aspek += sum(k.get("qty_asli",0) for k in krj)
		elif tipe == "pemasukan":
			value = self.masuk
			aspek = sum(p["total"] for p in data)
		else:
			value = self.untung
			aspek = sum(p["total_laba"] for p in data)
		
		dg = diagram_batang(
			[tr("Sebelumnya"), tr("Saat ini")],
			[aspek, value],
			tr("Diagram perbandingan") + " " + tr(tipe) + " " + self.periode + " " + tr("dan") + " " + tr("sebelumnya")
		)
		dg.setMinimumSize(300,250)
		clear_widgets(self.bawah)
		self.bawah_layout.addWidget(dg)
						
	def tampilkan_data(self):
		atas, alay = frame(QHBoxLayout, rata=rata_atas)
		tabel, model = table_maker(["Id produk", "Barcode", "Nama", "Jumlah", "Subtotal", "Laba"])
		set_expanding(atas, expand, fix)
		
		for teks, nilai, gambar in [
			("Terjual", format_unit(self.terjual, "unit"), "terjual_hari_ini.jpg"),
			("Pemasukan", pretty_money(self.masuk), "pemasukan_hari_ini.jpg"),
			("Keuntungan", pretty_money(self.untung), "keuntungan_hari_ini.jpg")
		]:
			btn = QToolButton()
			btn.setText(tr(teks) + "\n" + nilai)
			btn.setIcon(QIcon(resource_path("Pictures/" + gambar)))
			btn.setIconSize(QSize(100,100))
			btn.clicked.connect(lambda *args, type=teks.lower(): safe_run(self.filter_data_sebelumnya, type))
			btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
			btn.setStyleSheet(f"""
				QToolButton {{
					font-size: {font_size_normal}px;
					font-weight: 500;
					border: none;
				}}
				QToolButton:hover {{
					border: 1px solid {bg};
					border-radius: 2px;
				}}""")
			set_expanding(btn, expand, expand)
			alay.addWidget(btn, alignment=rata_atas)
		
		for p in self.data_for_tabel:
			model.appendRow([
				QStandardItem(p.get("id_produk","")),
				QStandardItem(p.get("barcode","")),
				QStandardItem(p.get("nama","")),
				QStandardItem(format_unit(p.get("terjual",0),"unit")),
				QStandardItem(pretty_money(p.get("total",0))),
				QStandardItem(pretty_money(p.get("laba",0)))
			])
				
		for p in [atas, tabel]:
			self.tengah_layout.addWidget(p)
	
	def setup(self):
		for p in [self.tengah, self.bawah]:
			clear_widgets(p)
		self.filter_data()
		self.olah_data()
		self.tampilkan_data()
		
class LaporanPenjualanKategori:
	def __init__(self, t, tl, b, bl, prd, opr, riwayat=None):
		self.tgh = t
		self.tgh_lay = tl
		self.bwh = b
		self.bwh_lay = bl
		self.prd = prd
		self.opr = opr
		self.riwayat = riwayat or []
		
	def filter_data(self):
		self.periode = self.prd.currentText().strip().lower()
		self.operator = self.opr.currentText().strip().lower()
		self.data = filter_data_periode(self.riwayat, self.periode, self.operator)
		
	def olah_data(self):
		produk = getData("produk")
		produk_dict = {p["id_produk"]: p["kategori"] for p in produk}
		self.result = []
		result_id = {}
		for p in self.data:
			krj = json.loads(p["data_belanja"])
			for k in krj:
				id = k.get("id","")
				kategori = produk_dict.get(id,"")
					
				if id in result_id:
					result_id[id]["terjual"] += k.get("qty_asli",0)
					result_id[id]["masuk"] += k.get("subtotal_jual",0)
					result_id[id]["untung"] += k.get("laba",0)
				else:
					result_id[id] = {
						"id": id,
						"kategori": kategori,
						"nama": k.get("nama",""),
						"terjual": k.get("qty_asli",0),
						"masuk": k.get("subtotal_jual",0),
						"untung": k.get("laba",0)
					}
		self.result = list(result_id.values())
		for_show = {}
		for p in self.result:
			k = p.get("kategori","")
			if k in for_show:
				for_show[k]["terjual"] += p.get("terjual",0)
				for_show[k]["masuk"] += p.get("masuk",0)
				for_show[k]["untung"] += p.get("untung",0)
			else:
				for_show[k] = {
					"kategori": k,
					"terjual": p.get("terjual",0),
					"masuk": p.get("masuk",0),
					"untung": p.get("untung",0)
				}
		self.for_show = list(for_show.values())						
	
	def show_detail(self, kategori):
		clear_widgets(self.tgh)
		tabel, model = table_maker(["Id produk", "Nama", "Terjual", "Subtotal", "Laba"])
		for p in self.result:
			if p["kategori"].lower() == kategori.lower():
				model.appendRow([
					QStandardItem(p.get("id","")),
					QStandardItem(p.get("nama","")),
					QStandardItem(format_unit(p.get("terjual",0), "unit")),
					QStandardItem(pretty_money(p.get("masuk",0))),
					QStandardItem(pretty_money(p.get("untung",0)))
				])
				
		self.tgh_lay.addWidget(tabel)
		
	def tabel_selected(self):
		row_selected = take_data(self.tabel, self.model)
		self.show_detail(row_selected[0])
		
	def tampilkan_data(self):
		clear_widgets(self.tgh)
		self.tabel, self.model = table_maker(["Kategori", "Terjual", "Pemasukan", "Keuntungan"])
		
		for i, p in enumerate(self.for_show):
			self.model.appendRow([
				QStandardItem(p.get("kategori","")),
				QStandardItem(format_unit(p.get("terjual",0),"unit")),
				QStandardItem(pretty_money(p.get("masuk",0))),
				QStandardItem(pretty_money(p.get("untung",0)))
			])
			
		self.tabel.clicked.connect(self.tabel_selected)
		self.tgh_lay.addWidget(self.tabel)
		
		sorted_terjual = sorted(self.for_show, key=lambda x: x["terjual"], reverse=True)[:5]
		sorted_masuk = sorted(self.for_show, key=lambda x: x["masuk"], reverse=True)[:5]
		sorted_untung = sorted(self.for_show, key=lambda x: x["untung"], reverse=True)[:5]
		
		for data, key, teks in [
			(sorted_terjual, "terjual", "penjualan"),
			(sorted_masuk, "masuk", "pemasukan"),
			(sorted_untung, "untung", "keuntungan")
		]:
			dg = diagram_batang(
				[p["kategori"] for p in data],
				[p[key] for p in data],
				f"Grafik top {len(data)} kategori {teks} terbanyak"
			)
			dg.setMinimumHeight(300)
			self.bwh_lay.addWidget(dg)
			
	def setup(self):
		for p in [self.tgh, self.bwh]:
			clear_widgets(p)
		
		self.filter_data()
		self.olah_data()
		self.tampilkan_data()
		
class LaporanPenjualanOperator:
	def __init__(self, tgh, tgh_lay, bwh, bwh_lay, prd, riwayat=None):
		self.tgh = tgh
		self.tgh_lay = tgh_lay
		self.bwh = bwh
		self.bwh_lay = bwh_lay
		self.prd = prd
		self.riwayat = riwayat or []
		
	def filter_data(self):
		self.periode = self.prd.currentText().strip().lower()
		self.data = filter_data_periode(self.riwayat, self.periode)
		
	def olah_data(self):
		dict_opr = {}
		for item in self.data:
			opr = item["operator"]
			dt = json.loads(item["data_belanja"])
			if opr in dict_opr:
				dict_opr[opr]["terjual"] += sum(p.get("qty_asli",0) for p in dt)
				dict_opr[opr]["masuk"] += sum(p.get("subtotal_jual",0) for p in dt)
				dict_opr[opr]["untung"] += sum(p.get("laba",0) for p in dt)
			else:
				dict_opr[opr] = {
					"operator": opr,
					"terjual": sum(p.get("qty_asli",0) for p in dt),
					"masuk": sum(p.get("subtotal_jual",0) for p in dt),
					"untung": sum(p.get("laba",0) for p in dt)
				}
		self.dict_opr = list(dict_opr.values())
	
	def tampilkan_data(self):
		clear_widgets(self.tgh)
		clear_widgets(self.bwh)
		
		tabel, model = table_maker(["Operator", "Terjual", "Pemasukan", "Keuntungan"])
		for p in self.dict_opr:
			model.appendRow([
				QStandardItem(p.get("operator","")),
				QStandardItem(format_unit(p.get("terjual",0),"unit")),
				QStandardItem(pretty_money(p.get("masuk",0))),
				QStandardItem(pretty_money(p.get("untung",0)))
			])		
		self.tgh_lay.addWidget(tabel)
		
		sorted_terjual = sorted(self.dict_opr, key=lambda x: x["terjual"], reverse=True)
		sorted_masuk = sorted(self.dict_opr, key=lambda x: x["masuk"], reverse=True)
		sorted_untung = sorted(self.dict_opr, key=lambda x: x["untung"], reverse=True)
		
		for data, key, teks in [
			(sorted_terjual, "terjual", "penjualan"),
			(sorted_masuk, "masuk", "pemasukan"),
			(sorted_untung, "untung", "keuntungan")
		]:
			dg = diagram_batang(
				[p["operator"] for p in data],
				[p[key] for p in data],
				f"Grafik kontribusi {teks} setiap operator"
			)
			dg.setMinimumHeight(300)
			self.bwh_lay.addWidget(dg)
				
	def setup(self):
		for p in [self.tgh, self.bwh]:
			clear_widgets(p)
		self.filter_data()
		self.olah_data()
		self.tampilkan_data()
		
class LaporanPenjualan:
	def __init__(self, riwayat=None, user=None):
		self.riwayat = riwayat or []
		self.user = user or []
		self.produk = None
	
	def prepare_frames(self):
		self.atas, self.atas_layout = frame(
			QGridLayout,
			bg="transparent"
		)
		self.tbl, self.mdl = table_maker(["Id produk", "Nama", "Terjual", "Pemasukan", "Laba"])
		self.tengah, self.tengah_layout = frame(QVBoxLayout, bg="rgba(0,120,100,0.06)")
		self.bawah, self.bawah_layout = frame(QVBoxLayout)
		for p in [self.atas, self.tbl, self.tengah, self.bawah]:
			f3_layout.addWidget(p, alignment=rata_atas)
		self.tbl.hide()
	
	def find_out(self, teks=""):
		result = []
		map_id = {p["id_produk"]: p["kategori"] for p in self.produk}
		keranjang = [json.loads(p["data_belanja"]) for p in self.riwayat]
		
		for data in keranjang:
			for k in data:
				id = k.get("id","")
				kategori = map_id.get(id,"")
				if teks.lower() in kategori.lower():
					result.append(k)
					
		if not result:
			map_opr = {}
			for p in self.riwayat:
				opr = p["operator"]
				items = json.loads(p["data_belanja"])
				if opr in map_opr:
					map_opr[opr].extend(items)
				else:
					map_opr[opr] = [k for k in items]
			for opr, value in map_opr.items():
				if teks.lower() in opr.lower():
					result.extend(value)
					break
		self.find_and_show = result
		self.tampilkan_hasil_pencarian()
		
	def tampilkan_hasil_pencarian(self):
		for p in [self.tengah, self.bawah]:
			clear_widgets(p)
		map = {}
		for p in self.find_and_show:
			id = p.get("id","")
			if id in map:
				map[id]["terjual"] += p.get("qty_asli",0)
				map[id]["masuk"] += p.get("subtotal_jual",0)
				map[id]["untung"] += p.get("laba",0)
			else:
				map[id] = {
					"id": id,
					"nama": p.get("nama",""),
					"terjual": p.get("qty_asli",0),
					"masuk": p.get("subtotal_jual",0),
					"untung": p.get("laba",0)
				}
		map_result = list(map.values())
		self.tbl.show()
		self.mdl.removeRows(0, self.mdl.rowCount())
		for p in map_result:
			self.mdl.appendRow([
				QStandardItem(p.get("id","")),
				QStandardItem(p.get("nama","")),
				QStandardItem(format_unit(p.get("terjual",0),"unit")),
				QStandardItem(pretty_money(p.get("masuk",0))),
				QStandardItem(pretty_money(p.get("untung",0)))
			])
					
	def set_atas(self):
		self.w = {
			"prd": combobox(font_size_normal, [tr("Semua periode"), tr("Bulan ini"), tr("Minggu ini"), tr("Hari ini")]),
			"opr": combobox(font_size_normal, [tr("Semua operator")] + list({p["nama"] for p in self.user})),
			"cari": entry(tr("Cari kategori / operator") + "...", font_size_normal),
			"produk": QPushButton(tr("Produk")),
			"kategori": QPushButton(tr("Kategori")),
			"operator": QPushButton(tr("Operator"))
		}
		produk = LaporanPenjualanProduk(
			self.tengah,
			self.tengah_layout,
			self.bawah,
			self.bawah_layout,
			self.w["prd"],
			self.w["opr"],
			riwayat=self.riwayat
		)
		kategori = LaporanPenjualanKategori(
			self.tengah,
			self.tengah_layout,
			self.bawah,
			self.bawah_layout,
			self.w["prd"],
			self.w["opr"],
			riwayat=self.riwayat
		)
		operator = LaporanPenjualanOperator(
			self.tengah,
			self.tengah_layout,
			self.bawah,
			self.bawah_layout,
			self.w["prd"],
			riwayat=self.riwayat
		)
		self.w["produk"].clicked.connect(lambda: safe_run(self.transition_helper, produk.setup))
		self.w["kategori"].clicked.connect(lambda: safe_run(self.transition_helper, kategori.setup))
		self.w["operator"].clicked.connect(lambda: safe_run(self.transition_helper, operator.setup))
		self.w["cari"].textChanged.connect(lambda: safe_run(self.find_out, self.w["cari"].text().strip()))
		
		clear_widgets(self.atas)
		for i, p in enumerate(self.w.values()):
			if i in [0,1,2]:
				self.atas_layout.addWidget(p,0,i)
			else:
				p.setStyleSheet(f"""
					QPushButton {{
						background-color: transparent;
						font-size: {font_size_normal}px;
						font-weight: 500;
						border: none;
						padding: 5px;
						border-radius: 2px;
					}}
					QPushButton:hover {{
						background-color: {bg};
						color: {warna_huruf};
						padding: 5px;
					}}""")
				self.atas_layout.addWidget(p,1,i-3, alignment=rata_kiri)
	
	def transition_helper(self, function):
		self.tbl.hide()
		function()
			
	def setup(self):
		self.produk = getData("produk")
		clear_widgets(f3)
		self.prepare_frames()
		self.set_atas()
		
class LaporanKeuangan:
	def __init__(self, pengeluaran=None, riwayat=None):
		self.pengeluaran = pengeluaran or []
		self.riwayat = riwayat or []
		
	def prepare_frames(self):
		self.atas, self.atas_layout = frame(QHBoxLayout, bg="rgba(0,120,100,0.06)", rata=rata_kiri)
		self.tengah, self.tengah_layout = frame(QGridLayout)
		self.midle, self.midle_layout = frame(QVBoxLayout)
		self.bawah, self.bawah_layout = frame(QVBoxLayout)
		for p in [
			self.atas,
			self.tengah,
			self.midle,
			self.bawah
		]:
			f3_layout.addWidget(p, alignment=rata_atas)
	
	def prepare_atas(self):
		self.wd = {
			"periode": combobox(font_size_normal, [tr("Semua periode"), tr("Hari ini"), tr("Minggu ini"), tr("Bulan ini")]),
			"lihat": button(tr("Lihat data"), font_size_normal, "lavender"),
			"riwayat": button(tr("Riwayat keuangan"), font_size_normal, "lightgreen")
		}
		self.wd["lihat"].clicked.connect(self.see_data)
		self.wd["riwayat"].clicked.connect(self.riwayat_keuangan)
		for p in self.wd.values():
			self.atas_layout.addWidget(p, alignment=rata_kiri)
	
	def see_data(self):
		self.prepare_data()
		self.tampilkan_data()
		
	def riwayat_keuangan(self):
		data = getData("riwayat_keuangan")
		if not data:
			QMB.warning(None, tr("Kosong"), tr("Riwayat keuangan tidak tersedia saat ini"))
			return
		for p in [self.tengah, self.midle, self.bawah]:
			clear_widgets(p)
		tabel, model = table_maker([
			"Waktu",
			"Jumlah",
			"Sumber",
			"Jenis",
			"Saldo awal",
			"Saldo akhir",
			"Pihak terkait",
			"Keterangan"
		])
		for p in data:
			model.appendRow([
				QStandardItem(p.get("waktu","")),
				QStandardItem(pretty_money(p.get("jumlah",0))),
				QStandardItem(p.get("sumber","")),
				QStandardItem(p.get("jenis","")),
				QStandardItem(pretty_money(p.get("saldo_awal",0))),
				QStandardItem(pretty_money(p.get("saldo_akhir",0))),
				QStandardItem(p.get("pihak_terkait","")),
				QStandardItem(p.get("keterangan",""))
			])
		self.tengah_layout.addWidget(tabel)
			
	def prepare_data(self):
		keuangan = getData("keuangan")
		saldo, masuk, untung, keluar = 0, 0, 0, 0
		if keuangan:
			masuk = keuangan[0]["pemasukan"]
			untung = keuangan[0]["keuntungan"]
			keluar = keuangan[0]["total_pengeluaran"]
			saldo = keuangan[0]["saldo"] + untung - keluar
			
		self.uang = {
			"Saldo": pretty_money(saldo),
			"Pemasukan": pretty_money(masuk),
			"Keuntungan": pretty_money(untung),
			"Pengeluaran": pretty_money(keluar)
		}
		
		pemasukan, hpp, diskon, tingkat = 0, 0, 0, 0
		
		self.periode = self.wd["periode"].currentText().strip().lower()
		self.data_olah = filter_data_periode(self.riwayat, self.periode)
		
		for p in self.data_olah:
			krj = json.loads(p["data_belanja"])
			for k in krj:
				pemasukan += k.get("harga_asli",0) * k.get("qty_asli",0)
				hpp += k.get("subtotal_modal",0)
				diskon += k.get("potongan_diskon",0)
				tingkat += k.get("potongan_tingkat",0)
				
		total_keluar = sum(p["total"] for p in self.pengeluaran)
		pemasukan_bersih = pemasukan - diskon - tingkat
		laba_kotor = pemasukan_bersih - hpp
		laba_bersih = laba_kotor - total_keluar
		
		self.info_keuangan = {
			"pemasukan kotor": pretty_money(pemasukan),
			"total harga pokok penjualan (HPP)": pretty_money(hpp),
			"total potongan diskon": pretty_money(diskon),
			"total potongan tingkat": pretty_money(tingkat),
			"total pengeluaran": pretty_money(total_keluar),
			"pemasukan bersih": pretty_money(pemasukan_bersih),
			"keuntungan kotor": pretty_money(laba_kotor),
			"keuntungan bersih": pretty_money(laba_bersih)
		}
		
		self.data_for_grafik = []
		for i in range(datetime.now().month):
			self.data_for_grafik.append(prepare_data_perbulan(i+1, riwayat=self.riwayat, pengeluaran=self.pengeluaran))
			
		self.months = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agust","Sept","Okt","Nov","Des"]
		
	def tampilkan_data(self):
		for p in [self.midle, self.tengah, self.bawah]:
			clear_widgets(p)
			
		for i, (key, value) in enumerate(self.uang.items()):
			if i == 0:
				lbl = label(key.capitalize() + ": " + value, font_size=font_size_normal, padding=10, margin=5, color="darkgreen", border=f"1px solid {bg}", border_radius=2, font_weight=600)
				self.tengah_layout.addWidget(lbl, 0, i, 1, 3)
			else:
				lbl = label(key.capitalize() + ": " + value, font_weight=500, padding=5)
				self.tengah_layout.addWidget(lbl, 1, i-1, alignment=rata_kiri)
		
		tabel, model = table_maker(["Aspek", "Value"])
		for p in [tabel.horizontalHeader(), tabel.verticalHeader()]:
			p.hide()
		for key, value in self.info_keuangan.items():
			model.appendRow([
				QStandardItem(str(key.capitalize())),
				QStandardItem(value)
			])
		self.midle_layout.addWidget(tabel)
		
		map_grafik = {}
		for p in self.data_for_grafik:
			for key, value in p.items():
				if key in map_grafik:
					map_grafik[key].append(value)
				else:
					map_grafik[key] = [value]
		for key, value in map_grafik.items():
			dg = diagram_batang(
				self.months,
				value,
				f"Grafik pertumbuhan {key.lower()} perbulan tahun {datetime.now().year}"
			)
			dg.setMinimumHeight(300)
			self.bawah_layout.addWidget(dg)
											
	def setup(self):
		clear_widgets(f3)
		self.prepare_frames()
		self.prepare_atas()
		self.prepare_data()
		self.tampilkan_data()
		
class Laporan:
	def __init__(self):
		self.pengeluaran = None
		self.riwayat = None
		self.user = None
	
	def setup(self):
		self.pengeluaran = getData("Pengeluaran")
		self.riwayat = getData("riwayat_penjualan_campuran")
		self.user = getData("user")
		
		cepat = LaporanCepat(pengeluaran=self.pengeluaran, riwayat=self.riwayat, user=self.user)
		jual = LaporanPenjualan(riwayat=self.riwayat, user=self.user)
		uang = LaporanKeuangan(pengeluaran=self.pengeluaran, riwayat=self.riwayat)
		
		for p in [f2, f3]:
			clear_widgets(p)
		wd = [
			("Laporan cepat", "buat nota.png", lambda: safe_run(cepat.setup)),
			("Laporan penjualan", "laporan penjualan.png", lambda: safe_run(jual.setup)),
			("Laporan keuangan", "gambar laporan keuangan.png", lambda: safe_run(uang.setup))
		]
		for teks, gambar, command in wd:
			btn = button_photo(tr(teks), resource_path("Pictures/" + gambar), icon_size, command)
			btn.setStyleSheet(f2_btn(font_size_normal))
			f2_layout.addWidget(btn)
		cepat.setup()
				
class Pajak:
	def __init__(self):
		self.pajak = None
		self.data_pajak = None
		
	def prepare_frames(self):
		atas, atas_layout = frame(QHBoxLayout, rata=rata_atas, bg="transparent")
		bawah, bawah_layout = frame(QVBoxLayout, rata=rata_atas, bg="transparent")
		
		kiri, kiri_layout = frame(QGridLayout, rata=rata_kiri, bg="rgba(0,120,100,0.06)")
		kanan, kanan_layout = frame(QVBoxLayout, rata=rata_kiri, bg="rgba(0,120,100,0.06)")
		
		self.info = {
			"total pajak terkumpul": label("", color="darkgreen", font_size=font_size_judul, border=f"1px solid {bg}", padding=7, border_radius=2, font_weight=700),
			"persentase pajak": label("", color="red", font_size=font_size_judul, font_weight=700)
		}
		self.aktifkan = checkbutton(tr("Aktifkan pajak"), font_size_normal)
		self.info["total pajak terkumpul"].setText(pretty_money(self.total_pajak))
		self.info["persentase pajak"].setText(format_persen(self.persen))
		self.aktifkan.setChecked(self.aktif)
		self.aktifkan.toggled.connect(self.set_pajak)
		
		self.input = entry(tr("Masukkan persentase pajak baru"), font_size_normal)
		btn_simpan = button(tr("Simpan"), font_size_normal, bg)
		btn_simpan.clicked.connect(self.simpan_pajak)
		
		judul = label(tr("DAFTAR RIWAYAT PAJAK"), font_size=font_size_judul, font_weight=500, color="darkgreen")
		warn = label(tr("Pajak PPN diperoleh dari: harga jual produk * %PPN"), color="green")
		self.tabel, self.model = table_maker(["Id", "Waktu", "Nama produk", "Subtotal pajak"])
			
		for i, (key, value) in enumerate(self.info.items()):
			label_key = label(key.capitalize(), font_size=font_size_judul, font_weight=700)
			label_titik = label(":", font_size=font_size_judul, font_weight=700)
			for j, item in enumerate([label_key, label_titik, value]):
				kiri_layout.addWidget(item, i, j, alignment=rata_kiri)
		kiri_layout.addWidget(self.aktifkan, 2, 0, alignment=rata_kiri)
		
		for p in [judul, self.tabel, warn]:
			bawah_layout.addWidget(p, alignment=rata_atas)
			
		for p in [self.input, btn_simpan]:
			kanan_layout.addWidget(p, alignment=rata_atas)
					
		for p in [kiri, kanan]:
			set_expanding(p, expand, fix)
			atas_layout.addWidget(p, alignment=rata_atas)
			 
		clear_widgets(f3)
		for p in [atas, bawah]:
			f3_layout.addWidget(p, alignment=rata_atas)
			
	def hitung(self):
		self.total_pajak = sum(p["pajak"] for p in self.pajak)
		self.persen = self.data_pajak[0]["persen"] if self.data_pajak else 0
		self.aktif = self.data_pajak[0]["aktif"] if self.data_pajak else 0
	
	def tambah_data(self):
		for p in sorted(self.pajak, key=lambda x: parse_date(x["waktu"]), reverse=True):
			self.model.appendRow([
				QStandardItem(str(p.get("id",0))),
				QStandardItem(p.get("waktu","")),
				QStandardItem(p.get("nama","")),
				QStandardItem(pretty_money(p.get("pajak",0)))
			])
	
	def simpan_pajak(self):
		if not va("atur pajak"):
			QMB.warning(None, "", tr("Anda tidak diizinkan"))
			return
		ppn = self.input.text().strip()
		try:
			pajak_nilai = int(ppn)
		except ValueError:
			QMB.critical(None, tr("Gagal"), tr("Silahkan input angka dengan benar"))
			return
		if askyesno(tr("Konfirmasi"), tr("Peringatan\n\nPerubahan pada persentase pajak baru akan dipakai setelah restart\n\nKlik yes untuk lanjutkan!")):
			if koneksi["connect"] == 1:
				data = {
					"persen_pajak": pajak_nilai
				}
				upload_data("pajak_persen", data, f"{tr('Pajak telah ditetapkan')} {pajak_nilai} {tr('persen')}")
			else:
				cursor.execute("SELECT persen FROM pajak")
				p = cursor.fetchone()
				if not p:
					cursor.execute("INSERT INTO pajak (persen) VALUES (?)", (pajak_nilai, ))
				else:
					cursor.execute("UPDATE pajak SET persen = ? WHERE id = ?", (pajak_nilai, 1))
				conn.commit()
					
				QMB.information(None, tr("Berhasil"), f"{tr('Pajak telah ditetapkan')} {pajak_nilai} {tr('persen')}")
			self.setup()
			
	def set_pajak(self):
		pajak_aktif = 1 if self.aktifkan.isChecked() else 0
		if koneksi["connect"] == 1:
			upload_data("pajak_selalu_aktif", {"aktif": pajak_aktif}, "Selesai")
		else:
			cursor.execute("UPDATE pajak SET aktif = ? WHERE id = ?", (pajak_aktif, 1))
			conn.commit()	
				
	def setup(self):
		if not va("pajak"):
			QMB.critical(None, "", tr("Anda tidak diizinkan"))
			return
		self.pajak = getData("riwayat_pajak")
		self.data_pajak = getData("pajak")
		self.hitung()
		self.prepare_frames()
		self.tambah_data()

def tambah_produk_baru():
	print()
	
class EditProduk:
	def __init__(self, data=None):
		self.data = data
		self.produk = None
		
	def prepare_frames(self):
		atas, self.atas_layout = frame(QHBoxLayout, rata=rata_kiri, bg="transparent")
		self.tengah, self.tengah_layout = frame(QGridLayout, bg="transparent")
		self.preview = QLabel()
		self.preview.setAlignment(Qt.AlignCenter)
		self.bawah, self.bawah_layout = frame(QHBoxLayout, bg="transparent", rata=rata_kanan)
		for p in [atas, self.tengah, self.preview, self.bawah]:
			f3_layout.addWidget(p, alignment=rata_atas)
	
	def set_atas(self):
		self.ats = {
			"utama": button2(tr("Edit data utama"), bg="lightgreen", fg="black", image=resource_path("Pictures/buat nota.png"), klik=self.setup),
			"diskon": button2(tr("Harga diskon"), bg="lightblue", fg="black", image=resource_path("Pictures/gambar laporan keuangan.png"), klik=lambda: safe_run(self.add_diskon)),
			"tingkat": button2(tr("Harga tingkat"), bg="yellow", fg="black", image=resource_path("Pictures/laporan080102.png"), klik=lambda: safe_run(self.add_tingkat)),
			"barcode": button2(tr("Generate barcode"), bg="green", fg="white", image=resource_path("Pictures/barcode.png"), klik=lambda: safe_run(self.make_barcode)),
			"katalog": button2(tr("Tambahkan gambar katalog"), bg="red", fg="white", image=resource_path("Pictures/katalog ikon.png"))
		}
		for value in self.ats.values():
			self.atas_layout.addWidget(value, alignment=rata_kiri)
	
	def simpan_tingkat(self):
		ent = {key: value.text().strip() for key, value in self.entry_tingkat.items()}
		path = self.path.currentText().strip()
		try:
			hj = float(ent.get("harga",0))
			min = int(ent.get("minimal",0))
		except ValueError as e:
			QMB.critical(None, "Error", tr("Terjadi kesalahan") + "\n" + str(e))
			return
		save_in = path.replace(" ", "_").lower()
		harga_modal = self.data_edit.get("harga_modal",0) * min
		if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
			if koneksi["connect"] == 1:
				data = {
					"id_produk": self.data_edit.get("id_produk",""),
					"barcode": self.data_edit.get("barcode",""),
					"nama": self.data_edit.get("nama",""),
					"harga_modal": harga_modal,
					"harga_jual": hj,
					"min_beli": min,
					"path": save_in
				}
				setData("tambah_tingkat_produk", data)
			else:
				spin = set_spinner(window)
				try:
					cursor.execute(f"""INSERT OR REPLACE INTO {save_in}
						(
							id_produk,
							barcode,
							nama,
							harga_modal,
							harga_jual,
							min_beli
						) VALUES (?, ?, ?, ?, ?, ?)""",
						(
							self.data_edit.get("id_produk",""),
							self.data_edit.get("barcode",""),
							self.data_edit.get("nama",""),
							harga_modal,
							hj,
							min
						)
					)
					conn.commit()
					spin.deleteLater()
					QMB.information(None, tr("Berhasil"), tr("Produk telah disimpan"))
				except Exception as e:
					conn.rollback()
					spin.deleteLater()
					QMB.critical(None, "Error", str(e))
		
	def hitung_harga_tingkat(self, minimal=0):
		if minimal != 0 and not minimal.isdigit():
			return
		min = int(minimal)
		dt = self.data_edit
		hm = dt.get("harga_modal",0) * min
		hj = dt.get("harga_jual",0) * min
		kn = hj - hm
		rkm = 50/100 * kn
		rhjm = hm + rkm
		self.info_tingkat.setText(f"""
{tr('Harga modal normal')}: {pretty_money(hm)}
{tr('Harga jual normal')}: {pretty_money(hj)}
{tr('Keuntungan normal')}: {pretty_money(kn)}
{tr('Rekomendasi keuntungan minimal')}: {pretty_money(rkm)}
{tr('Rekomendasi harga jual minimal')}: {pretty_money(rhjm)}

{tr('Rekomendasi harga jual minimal diperoleh dari')}:
50% {tr('keuntungan normal')} {tr('dan')} {tr('harga jual normal')}
		"""
		)
				
	def add_tingkat(self):
		for p in [self.tengah, self.bawah]:
			clear_widgets(p)
		self.preview.clear()
		
		fr, lay = frame(QHBoxLayout, bg="transparent")
		kiri, kiri_layout = frame(QVBoxLayout, bg="transparent")
		kanan, kanan_layout = frame(QVBoxLayout, bg="rgba(0,120,100,0.06)")
		
		nama = label(
			self.data_edit.get("nama","").upper(),
			font_size=font_size_judul,
			font_weight=500,
			color="green",
			border="1px solid green",
			padding=10
		)
		self.info_tingkat = label("", font_weight=450, color="green")
		
		self.path = combobox(font_size_normal, ["Tingkat A", "Tingkat B"])
		kanan_layout.addWidget(self.path)
		
		info_inp = [
			("minimal", "Minimum pembelian (satuan terkecil)"),
			("harga", "Harga jual")
		]
		self.entry_tingkat = entry_maker(kanan_layout, info_inp)
		self.entry_tingkat["minimal"].textChanged.connect(lambda: safe_run(self.hitung_harga_tingkat, self.entry_tingkat["minimal"].text().strip()))
		
		btn_simpan = button2(tr("Simpan"), klik=lambda: safe_run(self.simpan_tingkat))
		kanan_layout.addWidget(btn_simpan)
		
		for p in [nama, self.info_tingkat]:
			kiri_layout.addWidget(p, alignment=rata_atas)
			
		for p in [kiri, kanan]:
			lay.addWidget(p)
		self.tengah_layout.addWidget(fr,0,0)

	def generate_now(self):
		brc = barcode.get("code128", self.inp.text().strip(), writer=ImageWriter())
		buffer = BytesIO()
		brc.write(buffer)
		buffer.seek(0)
		show_pictures(buffer.read(), self.preview, 300)
		return brc, buffer
		
	def simpan_barcode(self):
		d = self.data_edit
		nama_file = d.get("nama","") + ".png"
		brc = self.inp.text().strip()
		if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
			doc, buffer = self.generate_now()
			if koneksi["connect"] == 1:	
				buffer.seek(0)
				data = {"barcode": brc, "id": d.get("id_produk",0)}
				files = {"file": (nama_file, buffer, "image/png")}
				path = choose_save_path(nama_file)
				doc.save(path)
				try:
					res = requests.post(f"{SERVER_URL}/ganti_barcode", files=files, data=data)
					if res.status_code == 200:
						QMB.information(None, tr("Berhasil"), f"{tr('Barcode produk')} {d.get('nama','')} {tr('telah berhasil diperbarui')}")
					else:
						QMB.warning(None, tr("Gagal"), str(res.status_code))
				except Exception as e:
					QMB.critical(None, "Error", str(e))
			else:
				try:
					cursor.execute("UPDATE produk SET barcode = ? WHERE id_produk = ?", (brc, d.get("id_produk","")))
					conn.commit()
					path = choose_save_path(nama_file)
					doc.save(path)
					QMB.information(None, tr("Berhasil"), f"{tr('Barcode produk')} {d.get('nama','')} {tr('telah berhasil diperbarui')}")
				except Exception as e:
					conn.rollback()
					QMB.critical(None, "Error", tr("Terjadi kesalahan") + "\n" + str(e))
			self.setup()
													
	def cetak_barcode(self):
		brc, _ = self.generate_now()
		try:
			if printer:
				printer_info = next((p for p in printer if p.get("tipe","").lower() == "usb port"), None)
				if printer_info:
					id_vendor = printer_info.get("id_vendor","")
					id_produk = printer_info.get("id_produk","")
					if id_vendor and id_produk:
						if askyesno(tr("Konfirmasi"), tr("Cetak barcode sekarang") + "?"):
							printer_usb = Usb(id_vendor, id_produk)
							printer_usb.image(brc)
							printer_usb.cut()
							QMB.information(None, tr("Berhasil"), f"Barcode {self.inp.text().strip()} telah dicetak")
		except Exception as e:
			QMB.information(None, tr("Gagal"), tr("Terjadi kesalahan") + "\n" + str(e))
						
	def make_barcode(self):
		for p in [self.tengah, self.bawah]:
			clear_widgets(p)
		self.preview.clear()
		nama = self.data_edit.get("nama","")
		now = datetime.now().strftime("%f%S")
		kode_bar = nama.split()[0] + "_" + now
		self.inp = entry(tr("Tuliskan barcode Anda") + "...", font_size_normal)
		self.inp.setText(kode_bar)
		self.inp.textChanged.connect(self.generate_now)
		
		self.tengah_layout.addWidget(self.inp,0,0)
		btn_simpan = button2(tr("Simpan"))
		btn_cetak = button2(tr("Cetak"))
		btn_simpan.clicked.connect(lambda: safe_run(self.simpan_barcode))
		btn_cetak.clicked.connect(lambda: safe_run(self.cetak_barcode))
		
		for p in [btn_simpan, btn_cetak]:
			self.bawah_layout.addWidget(p, alignment=rata_kanan)
		self.generate_now()
		
	def kalkulasi_diskon(self, p=None):
		persen = 0 if not p.isdigit() else int(p)
		
		d = self.data_edit
		hm = d.get("harga_modal")
		hj = d.get("harga_jual")
		hjb = hj * (1 - persen / 100)
		ekn = hj - hm
		ekb = hjb - hm
		teks = f"""
{tr('Harga modal produk')}: {pretty_money(hm)}
{tr('Harga jual normal')}: {pretty_money(hj)}
{tr('Harga jual baru')}: {pretty_money(hjb)}
{tr('Estimasi keuntungan normal')}: {pretty_money(ekn)}
{tr('Estimasi keuntungan baru')}: {pretty_money(ekb)}
{tr('Keuntungan dikurangi')}: {pretty_money(ekn - ekb)}

{tr('Kalkulasi ini ditujukan untuk 1 unit produk dalam satuan jual terkecil')}
(pcs, unit, bungkus, kaleng, dan lain-lain)

		"""
		self.label_prediksi.setText(teks)
		
	def simpan_diskon(self):
		dt = self.data_edit
		try:
			ent = {key: int(value.text().strip()) for key, value in self.entry_diskon.items()}
		except Exception as e:
			QMB.critical(None, "Error", f"{tr('Terjadi kesalahan')}:\n {e}")
			return
		datriw = {
			"waktu": now_str(),
			"aksi": "Tambah produk diskon",
			"nama": dt.get("nama",""),
			"barcode": dt.get("barcode",""),
			"jumlah": 1,
			"operator": nama_operator(),
			"sumber": komputer()
		}
		if askyesno(tr("Konfirmasi"), tr("Simpan sekarang?")):
			if koneksi["connect"] == 1:
				data = {
					"nama": dt.get("nama",""),
					"barcode": dt.get("barcode",""),
					"harga_jual": dt.get("harga_jual",0),
					"persen": ent.get("persen",0),
					"min": ent.get("minimal",0)
				}
				kemasan = {
					"data": data,
					"riwayat": datriw
				}
				setData("tambah_produk_diskon", kemasan)
			else:
				spin = set_spinner(window)
				try:
					cursor.execute("SELECT * FROM produk_diskon WHERE barcode = ? OR nama = ?", (dt.get("barcode",""), dt.get("nama","")))
					disk = cursor.fetchone()
					if disk:
						cursor.execute("UPDATE produk_diskon SET persen = ?, min = ? WHERE id = ?", (ent.get("persen",0), ent.get("minimal",0), disk["id"]))
					else:
						cursor.execute("INSERT INTO produk_diskon (barcode, nama, harga_jual, persen, min) VALUES (?, ?, ?, ?, ?)", (dt.get("barcode",""), dt.get("nama",""), dt.get("harga_jual",0), ent.get("persen",0), ent.get("minimal",0)))
					cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, barcode, jumlah, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?)", (now_str(), "Tambah produk diskon", dt.get("nama",""), dt.get("barcode",""), 1, nama_operator(), komputer()))
					conn.commit()
					spin.deleteLater()			
					QMB.information(None, tr("Berhasil"), f"{dt.get('nama','')} {tr('telah ditambahkan ke produk diskon')}")
				except Exception as e:
					conn.rollback()
					spin.deleteLater()
					QMB.critical(None, "Error", f"{tr('Terjadi kesalahan')}:\n {e}")
										
	def add_diskon(self):
		for p in [self.tengah, self.bawah]:
			clear_widgets(p)
		self.preview.clear()
		fr, lay = frame(QHBoxLayout)
		kiri, kiri_layout = frame(QVBoxLayout)
		kanan, kanan_layout = frame(QVBoxLayout, bg="rgba(0,120,100,0.06)")
		
		nama = label(self.data_edit.get("nama","").upper(), font_size=font_size_judul, font_weight=500, color="green", padding=5, border="1px solid green")
		self.label_prediksi = label("", color="green", font_weight=450)
		
		info_entry = [
			("persen", "Masukan persentase"),
			("minimal", "Masukkan minimum pembelian")
		]
		self.entry_diskon = entry_maker(kanan_layout, info_entry)
		self.entry_diskon["persen"].textChanged.connect(lambda: self.kalkulasi_diskon(self.entry_diskon["persen"].text().strip()))
		
		btn_simpan = button2(tr("Simpan"))
		btn_simpan.clicked.connect(lambda: safe_run(self.simpan_diskon))
		self.bawah_layout.addWidget(btn_simpan, alignment=rata_kiri)
		
		for p in [nama, self.label_prediksi]:
			kiri_layout.addWidget(p)
		for p in [kiri, kanan]:
			lay.addWidget(p)
		self.tengah_layout.addWidget(fr,0,0,alignment=rata_atas)
		
	def set_tengah(self):
		for_entry = []
		for_combobox = []
		for p in [self.tengah, self.bawah]:
			clear_widgets(p)
		
		for key in self.data_edit.keys():
			if key.lower() not in ["supplier", "satuan_beli", "satuan_jual", "kategori"]:
				for_entry.append((key.lower(), tr("Masukkan") + " " + key.replace("_"," ").lower() + " " + tr("baru") + "..."))
			else:
				for_combobox.append(key.lower())
				
		entry_bagi = [for_entry[i:i+4] for i in range(0, len(for_entry), 4)]
		self.dict_result = {}
		for i, list_tup in enumerate(entry_bagi):
			fr, lay = frame(QVBoxLayout, bg="white")
			ent = entry_maker(lay, list_tup)
			for key, value in ent.items():
				self.dict_result[key] = value
			self.tengah_layout.addWidget(fr, i//2, i%2)
			
		fr_combo, lay_combo = frame(QVBoxLayout, bg="white")
		row = len(entry_bagi) // 2
		self.tengah_layout.addWidget(fr_combo, row, 0, 1, 2)
		
		self.result_combo = {}
		self.result_entry = {}
		for key in for_combobox:
			entri = entry(tr(key.replace("_"," ").lower().capitalize()) + "...", font_size_normal)
			cmb = combobox(font_size_normal, list({p[key] for p in self.produk}))
			cmb.setCurrentText(self.data_edit.get(key,""))
			lay_combo.addWidget(cmb)
			lay_combo.addWidget(entri)
			self.result_combo[key] = cmb
			self.result_entry[key] = entri
		
		for key in self.dict_result.keys():
			self.dict_result[key].setText(str(self.data_edit.get(key,"")))
		
		btn = button2(tr("Simpan"))
		btn.clicked.connect(lambda: safe_run(self.simpan_edit))
		self.bawah_layout.addWidget(btn, alignment=rata_kanan)
	
	def simpan_edit(self):
		ent = {key: value.text().strip() for key, value in self.dict_result.items()}
		cmb = {key: value.currentText().strip() for key, value in self.result_combo.items()}
		cmb_ent = {key: value.text().strip() for key, value in self.result_entry.items()}
		kategori = cmb_ent.get("kategori","") if cmb_ent.get("kategori","") != "" else cmb.get("kategori","")
		satuan_jual = cmb_ent.get("satuan_jual","") if cmb_ent.get("satuan_jual","") != "" else cmb.get("satuan_jual","")
		satuan_beli = cmb_ent.get("satuan_beli","") if cmb_ent.get("satuan_beli","") != "" else cmb.get("satuan_beli","")
		supplier = cmb_ent.get("supplier","") if cmb_ent.get("supplier","") != "" else cmb.get("supplier","")
		
		try:
			jumlah = int(ent.get("jumlah", 0))
			harga_beli = float(ent.get("harga_beli", 0))
			isi_satuan = int(ent.get("isi_satuan", 0))
		except ValueError:
			QMB.critical(None, tr("Gagal"), tr("Masukkan angka dengan benar"))
			return
		data = self.data_edit
		stok_tertinggi = jumlah if jumlah > data.get("jumlah_tertinggi",0) else data.get("jumlah_tertinggi",0)
		harga_modal = float(harga_beli / isi_satuan)
		choosen_produk = []
		choosen_produk[:] = [p for p in self.produk if p.get("id_produk","") != data.get("id_produk","")]
		for p in choosen_produk:
			if p["nama"].lower() == ent.get("nama", "").lower() or p["barcode"] == ent.get("barcode", ""):
				QMB.critical(None, tr("Duplikasi produk"), tr("Terdeteksi duplikasi produk"))
				return
		if askyesno(tr("Konfirmasi"), f"{tr('Apakah data produk')} {ent.get('nama', '')} {tr('sudah benar')}?"):
			if koneksi["connect"] == 1:
				data = {
					"nama_lama": data.get("nama",""),
					"barcode_lama": data.get("barcode",""),
					"id": data.get("id",0),
					"barcode": ent.get("barcode", ""),
					"nama": ent.get("nama", ""),
					"catatan": ent.get("catatan", ""),
					"kategori": kategori,
					"kadaluarsa": ent.get("kadaluarsa", ""),
					"satuan_beli": satuan_beli,
					"satuan_jual": satuan_jual,
					"isi_satuan": isi_satuan,
					"harga_beli": harga_beli,
					"harga_jual": float(ent.get("harga_jual", 0)),
					"jumlah": jumlah,
					"stok_minimum": int(ent.get("stok_minimum", 0)),
					"supplier": supplier,
					"jumlah_tertinggi": stok_tertinggi,
					"poin": int(ent.get("poin", 0))
				}
				datriw = {
					"waktu": now_str(),
					"aksi": "Edit produk",
					"nama_lama": data.get("nama",""),
					"nama": ent.get("nama", ""),
					"jumlah_lama": data.get("jumlah",""),
					"jumlah": jumlah,
					"modal_lama": data.get("harga_modal",0),
					"harga_modal": float(ent.get("harga_modal", 0)),
					"jual_lama": data.get("harga_jual",0),
					"harga_jual": float(ent.get("harga_jual", 0)),
					"catatan_lama": data.get("catatan",""),
					"catatan": ent.get("catatan", ""),
					"barcode": ent.get("barcode", ""),
					"operator": nama_operator(),
					"sumber": komputer()
				}
				kemasan = {
					"data": data,
					"riwayat": datriw
				}
				setData("edit_produk", kemasan)
			else:
				spin = set_spinner(window)
				try:
					cursor.execute("""UPDATE produk SET
						barcode = ?,
						nama = ?,
						kategori = ?,
						catatan = ?,
						kadaluarsa = ?,
						satuan_beli = ?,
						satuan_jual = ?,
						isi_satuan = ?,
						supplier = ?,
						harga_beli = ?,
						harga_modal = ?,
						harga_jual = ?,
						jumlah = ?,
						jumlah_tertinggi = ?,
						stok_minimum = ?,
						poin = ?
						WHERE id = ?""",
						(
							ent.get("barcode", ""),
							ent.get("nama", ""),
							kategori,
							ent.get("catatan", ""),
							ent.get("kadaluarsa", ""),
							satuan_beli,
							satuan_jual,
							ent.get("isi_satuan", 0),
							supplier,
							ent.get("harga_beli", 0),
							ent.get("harga_modal", 0),
							ent.get("harga_jual", 0),
							jumlah,
							stok_tertinggi,
							ent.get("stok_minimum", 0),
							ent.get("poin", 0),
							data.get("id",0)
						)
					)		
					cursor.execute("""INSERT INTO riwayat
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
							now_str(),
							"Edit produk",
							data.get("nama",""),
							ent.get("nama", ""),
							data.get("jumlah",0),
							ent.get("jumlah", 0),
							data.get("harga_modal",0),
							ent.get("harga_modal", 0),
							data.get("harga_jual",0),
							ent.get("harga_jual", 0),
							data.get("catatan",""),
							ent.get("catatan", ""),
							ent.get("barcode", ""),
							nama_operator(),
							komputer()
						)
					)
					conn.commit()
					spin.deleteLater()
					QMB.information(None, tr("Berhasil"), f"Data {data.get('id',0)} telah diperbarui!")
				except Exception as e:
					conn.rollback()
					spin.deleteLater()
					QMB.critical(None, "Error", f"Terjadi kesalahan saat update data:\n{e}")
			daftar_produk.setup()
											
	def setup(self):
		self.data_edit = self.data or {}
		self.produk = getData("produk")
		self.path_katalog = None
		clear_widgets(f3)
		self.prepare_frames()
		self.set_atas()
		self.set_tengah()
			
class DaftarProduk:
	def __init__(self):
		self.produk = None
		
	def set_f2(self):
		fr, lay = frame(QVBoxLayout, bg="transparent")
		set_expanding(fr, expand, fix)
		atas, atas_layout = frame(QHBoxLayout, bg="transparent")
		bawah, bawah_layout = frame(QHBoxLayout, bg="transparent", rata=rata_kiri)
		
		self.a = {
			"back": button2(tr("Kembali"), image=resource_path("Pictures/kembali.png"), bg="transparent", fg="black", klik=master),
			"refresh": button2("Refresh", image=resource_path("Pictures/refresh.png"), bg="transparent", fg="black", klik=self.setup),
			"baru": button2(tr("Produk baru"), image=resource_path("Pictures/produk_baru.png"), bg="transparent", fg="black", klik=tambah_produk_baru),
			"cari": entry(tr("Cari produk") + "...", font_size_normal)
		}
		self.b = {
			"menu": button2(tr("Menu"), bg=bg, fg=warna_huruf, image=resource_path("Pictures/other_menu.png")),
			"info": button2(tr("Info"), bg=bg, fg=warna_huruf, image=resource_path("Pictures/eee.png")),
			"katalog": button2(tr("Katalog produk"), bg=bg, fg=warna_huruf, image=resource_path("Pictures/folder_icon.png")),
			"exp": button2(tr("Info kadaluarsa"), bg=bg, fg=warna_huruf, image=resource_path("Pictures/bbb.png"))		
		}
		
		self.a["cari"].textChanged.connect(lambda: self.set_data_in_tabel(self.a["cari"].text().strip()))
		
		for value in self.b.values():
			bawah_layout.addWidget(value, alignment=rata_kiri)
			
		for value in self.a.values():
			atas_layout.addWidget(value)
		
		for p in [atas, bawah]:
			lay.addWidget(p)
		f2_layout.addWidget(fr)
		
	def set_f3(self):
		self.atas, self.atas_layout = frame(QVBoxLayout, bg="transparent", rata=rata_atas)
		bawah, bawah_layout = frame(QHBoxLayout, bg="transparent", rata=rata_kiri)
		self.tabel, self.model = table_maker(["Id produk", "Barcode", "Nama", "Jumlah", "Harga modal", "Harga jual"])
		
		self.c = {
			"detail": button2(tr("Detail produk"), bg="transparent", fg="#131212", image=resource_path("Pictures/detail.png")),
			"stok": button2(tr("Tambah stok"), bg="transparent", fg="#131212", image=resource_path("Pictures/add.png")),
			"edit": button2(tr("Edit produk"), bg="transparent", fg="#131212", image=resource_path("Pictures/edit.png")),
			"hapus": button2(tr("Hapus produk"), bg="transparent", fg="#131212", image=resource_path("Pictures/hapus080102###.png"))
		}
		
		self.c["detail"].clicked.connect(self.lihat_detail)
		self.c["stok"].clicked.connect(self.tambah_stok)
		self.c["edit"].clicked.connect(lambda: safe_run(self.edit_produk))
		
		for value in self.c.values():
			bawah_layout.addWidget(value, alignment=rata_kiri)
			
		for fr in [self.atas, bawah]:
			f3_layout.addWidget(fr, alignment=rata_atas)
		self.atas_layout.addWidget(self.tabel)
		
	def edit_produk(self):
		if not va("edit produk"):
			QMB.warning(None, tr("Ditolak"), tr("Anda tidak diizinkan"))
			return
		data = take_data(self.tabel, self.model)
		id_produk = data[0] if data else None
		if id_produk is not None:
			item = next((p for p in self.produk if p["id_produk"] == id_produk), None)
			if item is not None:
				edit = EditProduk(data=item)
				edit.setup()
		
	def tambah_stok(self):
		if not va("tambah stok"):
			QMB.warning(None, tr("Ditolak"), tr("Anda tidak diizinkan"))
			return
		data = take_data(self.tabel, self.model)
		id_produk = data[0] if data else None
		if id_produk is not None:
			item = next((p for p in self.produk if p["id_produk"] == id_produk), None)
			if item is not None:
				tambahan, _ = input_int(tr("Tambahan stok"), tr("Silahkan masukkan tambahan stok produk") + " " + item.get("nama",""))
				if tambahan > 0:
					total_stok = item.get("jumlah",0) + tambahan
					highest = item.get("jumlah_tertinggi",0)
					stok_tertinggi = total_stok if total_stok > highest else highest
					
					datriw = {
						"waktu": now_str(),
						"aksi": "Tambah stok",
						"nama": item.get("nama", ""),
						"jumlah": tambahan,
						"barcode": item.get("barcode",""),
						"stok_terbaru": int(item.get("jumlah",0)) + tambahan,
						"operator": nama_operator(),
						"sumber": komputer()
					}
					if koneksi["connect"] == 1:
						data = {
							"tambahan": tambahan,
							"jumlah_tertinggi": stok_tertinggi,
							"id_produk": id_produk
						}
						setData("tambah_stok", {"data_tambah": data, "riwayat": datriw})
					else:
						spin = set_spinner(window)
						try:
							cursor.execute("UPDATE produk SET jumlah = ?, jumlah_tertinggi = ? WHERE id_produk = ?",
								(
									total_stok,
									stok_tertinggi,
									id_produk
								)
							)
							cursor.execute("INSERT INTO riwayat (waktu, aksi, nama, jumlah, barcode, stok_terbaru, operator, sumber) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
								(
									now_str(),
									"Tambah stok",
									item.get("nama",""),
									tambahan,
									item.get("barcode",""),
									total_stok,
									nama_operator(),
									komputer()
								)
							)
							conn.commit()
						except Exception as e:
							conn.rollback()
							spin.deleteLater()
							QMB.critical(None, "Error", tr("Terjadi kesalahan saat menambah stok produk") + ":\n\n" + str(e))
						spin.deleteLater()
						QMB.information(None, tr("Berhasil"), f"Stok produk {item.get('nama','')} berhasil ditambahkan sebanyak {tambahan} unit.\n Stok saat ini: {total_stok} unit")
					self.setup()
			
	def lihat_detail(self):
		data = take_data(self.tabel, self.model)
		id = data[0] if data else None
		if id is not None:
			item = next((p for p in self.produk if p["id_produk"] == id), None)
			if item is not None:
				clear_widgets(self.atas)
				tbl, mdl = table_maker(["Aspek","Value"])
				for key, value in item.items():
					if key.lower() in ["harga_modal", "harga_jual", "harga_beli"]:
						val = pretty_money(value)
					else:
						val = str(value)
					mdl.appendRow([
						QStandardItem(key.replace("_"," ").lower().capitalize()),
						QStandardItem(val)
					])
				self.atas_layout.addWidget(tbl)
							
	def set_data_in_tabel(self, teks=""):
		self.model.removeRows(0, self.model.rowCount())
		for p in sorted(self.produk, key=lambda x: x["nama"]):
			if teks.lower() in p.get("nama","").lower() or teks in p.get("id_produk","") or teks in p.get("barcode",""):
				self.model.appendRow([
					QStandardItem(p.get("id_produk","")),
					QStandardItem(p.get("barcode","")),
					QStandardItem(p.get("nama","")),
					QStandardItem(format_unit(p.get("jumlah",0), p.get("satuan_jual",""))),
					QStandardItem(pretty_money(p.get("harga_modal",0))),
					QStandardItem(pretty_money(p.get("harga_jual",0)))
				])
					
	def setup(self):
		self.produk = getData("produk")
		for p in [f2,f3]:
			clear_widgets(p)
		self.set_f2()
		self.set_f3()
		self.set_data_in_tabel()

class Beranda:
	def __init__(self):
		self.riwayat = None
		self.pr = None
		self.pengeluaran = None
		self.diagram = None

	def set_f2_widgets(self):
		kiri, layout_kiri = frame(QVBoxLayout, bg="rgba(0,120,100,0.06)", rata=rata_kiri)
		kanan, layout_kanan = frame(QVBoxLayout, bg="rgba(0,120,100,0.06)", rata=rata_kanan)
		set_expanding(kiri, expand, fix)
		lbl_judul.setText(tr("HALAMAN BERANDA"))
		clear_widgets(f2)

		list_gambar = [
			"Pictures/hihihi.png",
			"Pictures/alamat.png",
			"Pictures/bbb.png"
		]
		self.label_toko = QPushButton()
		self.label_alamat = QPushButton()
		self.label_tanggal = QPushButton(date_translator(datetime.now().strftime("%A, %d %B %Y"), bahasa_aplikasi))
		self.label_waktu = QPushButton(datetime.now().strftime("%H.%M.%S"))
		for i, p in enumerate([self.label_toko, self.label_alamat, self.label_waktu]):
			p.setIcon(QIcon(list_gambar[i]))
			p.setIconSize(QSize(icon_size[0], icon_size[1]))

		self.label_toko.setStyleSheet(f"""
			QPushButton {{
				border: 1px solid {bg};
				font-size: {font_size_judul}px;
				padding: 5px;
				border-radius: 2px;
			}}""")
		for p in [self.label_alamat, self.label_tanggal, self.label_waktu]:
			p.setStyleSheet(f"""
				QPushButton {{
					font-size: {font_size_normal}px;
					font-weight: 500;
					border: none;
					background-color: transparent;
				}}""")

		for i, p in enumerate([self.label_toko, self.label_alamat, self.label_tanggal, self.label_waktu]):
			if i in [0, 1]:
				layout_kiri.addWidget(p, alignment=rata_kiri)
			else:
				layout_kanan.addWidget(p, alignment=rata_kanan)

		for p in [kiri, kanan]:
			f2_layout.addWidget(p)
			munculkan(p)

	def set_f3_widgets(self):
		self.tabel, self.model = table_maker(["Nama", "Terjual", "Subtotal", "Laba"])
		kanan, kanan_layout = frame(QHBoxLayout, rata=rata_atas)
		set_expanding(kanan, expand, fix)

		list_wallpaper = [
			"pemasukan_hari_ini.jpg",
			"terjual_hari_ini.jpg",
			"keuntungan_hari_ini.jpg"
		]
		self.masuk, self.jual, self.untung = QToolButton(), QToolButton(), QToolButton()
		for i, p in enumerate([self.masuk, self.jual, self.untung]):
			path_gambar = resource_path("Pictures/" + list_wallpaper[i])
			p.setIcon(QIcon(path_gambar))
			p.setIconSize(QSize(150, 100))
			p.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
			p.setStyleSheet(f"""
				QToolButton {{
					font-size: {font_size_judul+1}px;
					font-weight: 600;
					background-color: transparent;
					border: none;
					margin-left: 20px;
					margin-right: 20px;
				}}""")

		kanan_layout.addStretch(1)
		for p in [self.jual, self.masuk, self.untung]:
			kanan_layout.addWidget(p, alignment=rata_atas)
		kanan_layout.addStretch(1)
		
		self.bawah, self.bawah_layout = frame(QHBoxLayout, rata=rata_atas)
		clear_widgets(f3)
		for p in [kanan, self.tabel, self.bawah]:
			f3_layout.addWidget(p, alignment=rata_atas)
	
	def make_diagram_batang(self):
		diagram = diagram_batang(
			["Pengeluaran", "Pemasukan", "Keuntungan"],
			[self.total_pengeluaran, self.total_pemasukan, self.total_keuntungan],
			"GRAFIK DATA HARIAN"
		)
		return diagram
	
	def make_diagram_bolu(self):
		diagram = diagram_bolu(
			["Pengeluaran", "Pemasukan", "Keuntungan"],
			[self.total_pengeluaran, self.total_pemasukan, self.total_keuntungan],
			"GRAFIK DATA HARIAN"
		)
		return diagram
		
	def set_profil(self):
		self.pr = getData("profil")
		if not self.pr:
			self.label_toko.setText(tr("Profil toko belum dibuat"))
			self.label_alamat.setText("-|-")
			return
		nama_toko = self.pr[0]["nama"] if self.pr[0]["nama"] else "-"
		alamat = self.pr[0]["alamat"] if self.pr[0]["alamat"] else "-"
		kontak = self.pr[0]["kontak"] if self.pr[0]["kontak"] else "-"
		self.label_toko.setText(nama_toko)
		self.label_alamat.setText(alamat + " | " + kontak)

	def olah_data(self):
		self.riwayat = getData("riwayat_penjualan_campuran")
		start, end = periode_hari()
		self.total_pemasukan = 0
		self.total_penjualan = 0
		self.total_keuntungan = 0

		data_hari_ini = [p for p in self.riwayat if start <= parse_date(p["waktu"]) <= end]
		self.data_produk = []
		for dt in data_hari_ini:
			self.total_pemasukan += dt["total"]
			self.total_keuntungan += dt["total_laba"]
			keranjang = json.loads(dt["data_belanja"])
			for item in keranjang:
				self.total_penjualan += item.get("qty_asli", 0)
				for d in self.data_produk:
					if d.get("id", "") == item.get("id", ""):
						d["terjual"] += item.get("qty_asli", 0)
						d["masuk"] += item.get("subtotal_jual", 0)
						d["untung"] += item.get("laba", 0)
						break
				else:
					self.data_produk.append({
						"id": item.get("id", ""),
						"nama": item.get("nama", ""),
						"terjual": item.get("qty_asli", 0),
						"masuk": item.get("subtotal_jual", 0),
						"untung": item.get("laba", 0)
					})
		self.masuk.setText(tr("Pemasukan hari ini") + ":\n" + pretty_money(self.total_pemasukan))
		self.jual.setText(tr("Produk terjual hari ini") + ":\n" + format_unit(self.total_penjualan, "unit"))
		self.untung.setText(tr("Keuntungan hari ini") + ":\n" + pretty_money(self.total_keuntungan))
		for p in self.data_produk:
			self.model.appendRow([
				QStandardItem(p.get("nama", "")),
				QStandardItem(str(p.get("terjual", 0)) + " unit"),
				QStandardItem(pretty_money(p.get("masuk", 0))),
				QStandardItem(pretty_money(p.get("untung", 0)))
			])

	def hitung_pengeluaran(self):
		self.pengeluaran = getData("Pengeluaran")
		start, end = periode_hari()
		todays = [p for p in self.pengeluaran if start <= parse_date(p["waktu"]) <= end]
		self.total_pengeluaran = sum(p["total"] for p in todays)
		
	def change_dg(self, tipe):
		if tipe == "batang":
			new_dg = self.make_diagram_batang()
		else:
			new_dg = self.make_diagram_bolu()
			
		new_dg.setMinimumHeight(400)			
		clear_widgets(self.frame_dg)
		self.dg_layout.addWidget(new_dg)
	
	def make_bawah(self):
		prev = QPushButton("⟨")
		next = QPushButton("⟩")
		prev.clicked.connect(lambda: self.change_dg("batang"))
		next.clicked.connect(lambda: self.change_dg("bolu"))
		
		self.frame_dg, self.dg_layout = frame(QVBoxLayout, rata=Qt.AlignCenter)
		
		self.dg = self.make_diagram_batang()
		self.dg.setFixedHeight(400)
		self.dg_layout.addWidget(self.dg)
		
		for i, p in enumerate([prev, self.frame_dg, next]):
			if i != 1:
				p.setStyleSheet(f"""
					QPushButton {{
						background-color: transparent;
						font-size: {font_size_judul}px;
						font-weight: 800;
						border: none;
						padding: 15px;
					}}""")
				set_expanding(p, fix, expand)
			else:
				set_expanding(p, expand, expand)
			self.bawah_layout.addWidget(p)
				
	def setup(self):
		self.hitung_pengeluaran()
		self.set_f2_widgets()
		self.set_profil()
		self.set_f3_widgets()
		self.olah_data()
		self.make_bawah()
		
def get_wallpaper():
	path = os.path.join(folder_foto_profil, "walpaper login.png")
	if not os.path.exists(path):
		return resource_path("Pictures/walpaper login.png")
	return path
	
def login():
	global lock_button
	poin_kesalahan = 0
	def set_layout():
		for x in [f2, f3]:
			clear_widgets(x)
		path_gambar = get_wallpaper()
		frame = QFrame()
		frame.setObjectName("gambar")
		frame.setStyleSheet(f"""
			QFrame#gambar {{
				border-image: url({path_gambar});
			}}""")
		set_expanding(frame, expand, expand)
		frame_layout = QVBoxLayout(frame, alignment=rata_atas)
		f3_layout.addWidget(frame)
		return frame_layout, frame
	
	def set_widgets():
		clear_widgets(frame)
		lbl_judul.setText(tr("HALAMAN LOGIN"))
		fr = QFrame()
		fr.setObjectName("login_card")
		fr.setFixedWidth(300)
		
		fr.setStyleSheet(f"""
			QFrame#login_card {{
				background-color: rgba(255,255,255,200);
				border: 1px solid transparent;
				border-radius: 2px;
				padding: 0px;
			}}
		""")
	
		layout_fr = QVBoxLayout(fr)
		layout_fr.setContentsMargins(20, 20, 20, 20)
		layout_fr.setSpacing(14)
	
		label = QPushButton(
			f"{penentu_jam()}...\nSelamat datang kembali di {app_name}".upper()
		)
	
		label.setCursor(Qt.PointingHandCursor)
	
		label.setStyleSheet(f"""
			QPushButton {{
				background-color: rgba(150,180,215,0);
				color: #202020;
				padding: 10px;
				font-size: {font_size_normal};
				border: 1px solid rgba(126, 200, 227, 0);
				border-radius: 2px;
				font-weight: bold;
				text-align: center;
			}}
		""")
	
		widget = {
			"judul": label,
			"username": entry("Username...", font_size_normal),
			"password": entry("Password...", font_size_normal),
			"konfirmasi": red_label(""),
			"btn": button("Login", font_size_normal, bg),
			"login qr": button(
				tr("Login dengan QR"),
				font_size_normal,
				"transparent"
			),
			"lupa": button(
				tr("Lupa kata sandi?"),
				font_size_normal,
				"transparent"
			),
			"signup": button(tr("Daftar akun baru"), font_size_normal, "transparent")
		}
	
		widget["username"].setStyleSheet(f"""
			QLineEdit {{
				background-color: rgba(255,255,255,0);
				border: 1px solid black;
				border-radius: 2px;
				padding: 10px;
				font-size: {font_size_normal};
				color: #202020;
			}}
	
			QLineEdit:focus {{
				border: 2px solid {bg};
				background-color: white;
			}}
		""")
	
		widget["password"].setStyleSheet(f"""
			QLineEdit {{
				background-color: rgba(255,255,255,0);
				border: 1px solid black;
				border-radius: 2px;
				padding: 10px;
				font-size: {font_size_normal};
				color: #202020;
			}}
	
			QLineEdit:focus {{
				border: 2px solid {bg};
				background-color: white;
			}}
		""")
	
		widget["btn"].setStyleSheet(f"""
			QPushButton {{
				background-color: {bg};
				color: white;
				border: none;
				border-radius: 2px;
				padding: 10px;
				font-size: {font_size_normal};
				font-weight: bold;
			}}
	
			QPushButton:hover {{
				background-color: #87d4ef;
			}}
	
			QPushButton:pressed {{
				padding-top: 16px;
				padding-bottom: 12px;
			}}
		""")
	
		for nama in ["login qr", "lupa", "signup"]:
			widget[nama].setStyleSheet(f"""
				QPushButton {{
					background-color: transparent;
					border: none;
					color: black;
					font-size: {font_size_normal};
					font-weight: bold;
					padding: 10px;
					border-radius: 2px;
				}}
	
				QPushButton:hover {{
					background-color: rgba(126, 200, 227, 180);
					color: #202020;
				}}
			""")
	
		widget["konfirmasi"].setStyleSheet("""
			color: #d9534f;
			font-weight: bold;
			padding: 4px;
			background: transparent;
		""")
	
		for p in list(widget.values()):
			layout_fr.addWidget(p)	
		layout.addWidget(fr)	
		return widget
	
	def login_sekarang():
		global lock_button
		nonlocal poin_kesalahan
		us = widgets["username"].text().strip()
		pw = widgets["password"].text().strip()
		user = getData("user")
		pengguna = None
		id = None
		for x in user:
			if x["nama"].lower() == us.lower() or x["inisial_code"] == us:
				if pks.verify(pw, x["password"]):
					pengguna = x["nama"]
					id = x["inisial_code"]
					cursor.execute("DELETE FROM operator")
					cursor.execute("INSERT INTO operator (nama, status, inisial_code) VALUES (?, ?, ?)", (x["nama"], x["status"], x["inisial_code"]))
					conn.commit()		
					break
				else:
					poin_kesalahan += 1
					widgets["konfirmasi"].setText(tr("Kata sandi salah"))
					return
		else:
			poin_kesalahan += 1
			widgets["konfirmasi"].setText(tr("Akun tidak ditemukan\nSilahkan daftar terlebih dahulu"))
			return
		if koneksi["connect"] == 1:
			data = {
				"pengenal": us,
				"waktu": now_str(),
				"device": komputer(),
				"tipe_login": "Manual username/password",
				"poin_kesalahan": poin_kesalahan
			}
			upload_data("tambah_riwayat_login", data, f"{tr('Selamat datang kembali')} {pengguna}")
		else:
			cursor.execute("INSERT INTO riwayat_login (id_pengenal, nama, inisial_code, waktu, device, login_menggunakan, kesalahan_login) VALUES (?, ?, ?, ?, ?, ?, ?)", (us, pengguna, id, now_str(), komputer(), "Manual username/password", poin_kesalahan))
			conn.commit()
			QMB.information(None, tr("Berhasil"), f"{tr('Selamat datang kembali')} {pengguna}")
		lock_button = False
		dashboard()
	
	def sign_up():
		def prepare_layout():
			clear_widgets(frame)
			atas, bawah = QFrame(), QFrame()
			for i, p in enumerate([bawah, atas]):
				p.setFixedWidth(300)
				if i != 1:
					p.setStyleSheet(f"""
						QFrame {{
							background-color: rgba(255,255,255,180);
							border: none;
							border-radius: 2px;
						}}""")
				layout.addWidget(p, alignment=rata_atas)
			return QHBoxLayout(atas, alignment=rata_kiri), QVBoxLayout(bawah, alignment=rata_atas)
		
		def set_signup_widgets():
			gets = {}
			status = QComboBox()
			status.addItems(["Owner", "Admin", "Kasir"])
			status.setStyleSheet(f"""
				QComboBox {{
					background-color: {bg};
					border: none;
					border-radius: 2px;
					padding: 10px;
				}}""")
			list_data = [
				"Status baru",
				"Nama",
				"Password",
				"Konfirmasi Password",
				"Pertanyaan keamanan",
				"Jawaban"
			]
			
			bawah.addWidget(status)
			for i, p in enumerate(list_data):
				baris, kolom = (i+1) // 2, (i+1) % 2
				ent = QLineEdit()
				ent.setPlaceholderText(p)
				ent.setStyleSheet(f"""
					QLineEdit {{
						background-color: transparent;
						font-size: {font_size_normal}px;
						border: 1px solid black;
						border-radius: 2px;
						padding: 10px;
					}}
					QLineEdit:focus {{
						background-color: white;
						border: 2px solid {bg};
					}}""")
				gets[p] = ent
				bawah.addWidget(ent)
			return gets, status
		
		user = getData("user")			
		lbl_judul.setText(tr("PENDAFTARAN PENGGUNA BARU"))		
		atas, bawah = prepare_layout()
		kembali = QPushButton("Login")
		daftar = QPushButton(tr("Daftar"))
		for p in [kembali, daftar]:
			p.setStyleSheet(f"""
				QPushButton {{
					background-color: {bg};
					border: none;
					border-radius: 2px;
					padding-top: 10px;
					padding-bottom: 10px;
					padding-left: 20px;
					padding-right: 20px;
					color: black;
					font-size: {font_size_normal}px;
					font-weight: bold;
				}}
				QPushButton:pressed {{
					background-color: black;
					color: white;
				}}""")
			atas.addWidget(p, alignment=rata_kiri)
			
		def signup_now():
			n = gets.get("Nama", "").text().strip()
			s = gets.get("Status baru", "").text().strip() if gets.get("Status baru", "").text().strip() != "" else status.currentText()
			p = gets.get("Password", "").text().strip()
			kp = gets.get("Konfirmasi Password", "").text().strip()
			q = gets.get("Pertanyaan keamanan", "").text().strip()
			a = gets.get("Jawaban", "").text().strip()
			if not user:
				if s.lower() != "owner":
					QMB.warning(None, tr("Gagal"), tr("Pendaftaran user pertama kali harus berstatus OWNER!"))
					return
			if not all([n, s, p, kp]):
				QMB.warning(None, tr("Gagal"), tr("Beberapa data harus diisi!"))
				return
			if p != kp:
				QMB.warning(None, tr("Gagal"), tr("Password dan konfirmasi password tidak sama!"))
				return
				
			nama_bagi = n.split()
			name = n[0].split()
			inisial = name[0]
			inisial_code = f"{inisial}{datetime.now().strftime('%f')}"
			same = False
			for u in user:
				if u["nama"].lower() == n.lower():
					QMB.warning(None, tr("Gagal"), tr("User telah terdaftar"))
					same = True
					break
			if not same:
				pengguna = {
					"nama": n,
					"status": s,
					"inisial": inisial,
					"inisial_code": inisial_code,
					"password": pks.hash(p),
					"pertanyaan": q,
					"jawaban": pks.hash(a),
					"operator": nama_operator(),
					"sumber": komputer(),
					"pw": p
				}
				if koneksi["connect"] == 1:
					upload_data("tambah_user_baru", pengguna, tr("Pendaftaran akun berhasil. Silahkan hubungi owner atau admin untuk pengaktifan"))
				else:
					cursor.execute("INSERT INTO permintaan (waktu, jenis, data, status) VALUES (?, ?, ?, ?)", (now_str(), "Pendaftaran pengguna baru", json.dumps(pengguna), "Pending"))
					conn.commit()
					QMB.information(None, tr("Berhasil"), tr("Pendaftaran akun berhasil. Silahkan hubungi owner atau admin untuk pengaktifan"))
				
		kembali.clicked.connect(login)
		daftar.clicked.connect(lambda: safe_run(signup_now))
		gets, status = set_signup_widgets()
				
	layout, frame = set_layout()
	widgets = set_widgets()
	widgets["btn"].clicked.connect(login_sekarang)
	widgets["signup"].clicked.connect(lambda: safe_run(sign_up))
		
def konfirmasi_login():
	global lock_button
	pengguna = getData("user")
	if not pengguna:
		dashboard_aplikasi.setup()
	else:
		cursor.execute("SELECT * FROM operator")
		opr = cursor.fetchone()
		if not opr:
			lock_button = True
			login()
		else:
			dashboard_aplikasi.setup()
			
def get_screen_pos():
	screen = app.primaryScreen().availableGeometry()
	return screen.width(), screen.height()

def make_kalkulator():
	def prepare_layouts():
		frames = [QFrame(), QFrame()]
		set_expanding(frames[0], expand, fix)
		set_expanding(frames[1], expand, expand)
		for p in frames:
			kalkulator.addWidget(p, alignment=rata_atas)
		frames[1].setStyleSheet("""
			QFrame {
				border: 1px solid black;
				border-radius: 2px;
				background-color: lightgrey;
			}""")
		frames[0].setStyleSheet("""
			QFrame {
				border: 0px solid transparent;
				border-radius: 2px;
				background-color: grey;
			}""")
		return QVBoxLayout(frames[0], alignment=rata_atas), QGridLayout(frames[1], alignment=rata_atas)
	
	def prepare_widgets():
		edit = QTextEdit()
		edit.setFixedHeight(50)
		edit.setStyleSheet("""
			QTextEdit {
				background-color: white;
				border: 1px solid black;
				border-radius: 2px;
			}
			QTextEdit:focus {
				border: 1px solid green;
			}""")
		atas.addWidget(edit)
		edit.setFocus()
		return edit
	
	def style(bege):
		return f"""
			QPushButton {{
				background-color: {bege};
				border: 0.5px solid black;
				border-radius: 2px;
				color: black;
				font-weight: bold;
				font-size: {font_size_normal}px;
				padding: 5px;
			}}
			QPushButton:hover {{
				border: 1px solid red;
				border-radius: 2px;
			}}
			QPushButton:pressed {{
				background-color: black;
				color: white;
			}}"""
	
	def bersihkan():
		kotak.setPlainText("")
	
	def hapus_last():
		teks = kotak.toPlainText().strip()
		new = teks[0:-1]
		kotak.setPlainText(str(new))
		
	def hasil():
		teks = kotak.toPlainText().strip()
		if not teks:
			kotak.setPlainText("Input kosong")
			return  
		try:
			akhir = teks.replace("x", "*").replace(",", ".")
			hasil = eval(akhir)
			if isinstance(hasil, float):
				spl = str(hasil).split(".")
				blk = spl[-1]
				if blk.endswith("0"):
					tampil = spl[0]
				else:
					tampil = ",".join(spl)
			else:
				tampil = str(hasil)
			kotak.setPlainText(tampil)
		except ZeroDivisionError:
			kotak.setPlainText("Error: Bagi nol")
		except SyntaxError:
			kotak.setPlainText("Error: Input salah")
			
	def give(value):
		command = [bersihkan, hapus_last, hasil]
		simbol = ["C", "[x]", "="]
		if value in simbol:
			idx = simbol.index(value)
			command[idx]()
		else:
			teks = kotak.toPlainText().strip()
			teks_baru = teks + value
			kotak.setPlainText(str(teks_baru))
				
	def prepare_buttons():
		buttons = [
			"C", "(", ")", "[x]",
			"7", "8", "9", "+",
			"4", "5", "6", "-",
			"1", "2", "3", "x",
			",", "0", "/", "="
		]
		for i, p in enumerate(buttons):
			baris = i // 4
			kolom = i % 4
			btn = QPushButton(p)
			btn.setStyleSheet(style("red") if i == 3 else style("lightgreen") if i == 19 else style(bg))
			btn.clicked.connect(lambda *args, x=buttons[i]: give(x))
			bawah.addWidget(btn, baris, kolom)
			
	atas, bawah = prepare_layouts()
	set_margin(atas, 3)
	kotak = prepare_widgets()
	prepare_buttons()
		
cal_open = False	
def open_kalkulator():
	global cal_open
	if not cal_open:
		cal_open = True
		munculkan(kalkulator_frame)		
	else:
		cal_open = False
		kalkulator_frame.hide()

def va(fitur):
	cursor.execute("SELECT status FROM operator")
	stts = cursor.fetchone()
	if not stts:
		return True
	for p in izin_akses:
		if p["status"].lower() == stts["status"].lower():
			iz = json.loads(p["izin"])
			if fitur.lower() in [i.lower() for i in iz]:
				return True
			return False
	else:
		return True
			
def get_izin_akses():
	izin = getData("hak_akses")
	for p in izin:
		izin_akses.append(p)

path_wallpaper = os.path.join(folder_foto_profil, "Wallpaperforrightframeinmyappveryimportantandmostpowerfull.png")
if not os.path.exists(path_wallpaper):
	path_wallpaper = resource_path("Pictures/wall_default.png")
				
app = QApplication(sys.argv)
window = QWidget()
window.setGeometry(100,100,500,400)
window.setObjectName("mainWindow")
window.setStyleSheet(f"""
	QWidget#mainWindow {{
		background-image: url({path_wallpaper});
		background-position: center;
		background-repeat: no-repeat;
		border: none;
	}}""")
window_layout = QHBoxLayout(window)
set_margin(window_layout, 0)

take_owner_validation()
take_all_cache()
get_decimal()
get_theme()
get_format()
get_izin_akses()

dashboard_aplikasi = Beranda()
pajak_aplikasi = Pajak()
laporan_aplikasi = Laporan()
pengeluaran_aplikasi = Pengeluaran()
daftar_produk = DaftarProduk()

left, right_layout, kalkulator, kalkulator_frame = make_main_frame()
right_layout.setContentsMargins(3,0,3,0)
right_layout.setSpacing(5)
kalkulator_frame.hide()
left_layout = left_layout_setting()
state_left = False
lock_button = False
left.setVisible(False)

f1, f2, f3 = set_right_frames()
f1_layout, f2_layout, f3_layout = set_layout_for_right_frame()
lbl_judul, lbl_koneksi = set_f1_widgets()

set_left_widgets()
konfigurasi_koneksi()
make_kalkulator()
simpan_foto_profil_sementara()
konfirmasi_login()
window.show()
sys.exit(app.exec())
conn.close()