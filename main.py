from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.config import Config
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior		
import os, sys, json, sqlite3, calendar, socket, threading, time
from flask import Flask, request, jsonify
from werkzeug.serving import make_server
from datetime import datetime, timedelta

Config.set('graphics', 'fullscreen', 'auto')
Window.softinput_mode = "below_target"
universal_background = "#D6EDF7"
default_bg_btn = "#5587B7"
format_uang_app = ["Rp", "kiri", ".", ",", "2"]
use_decimal = True
main_folder = "DATABASE UTAMA ANDROID KIVY APP"
PORT = 8080

def app_get_data_folder():
	if sys.platform == "win32":
		base = os.path.join(os.environ["LOCALAPPDATA"], main_folder)
	elif sys.platform == "darwin":
		base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", main_folder)
	else:
		base = os.path.join(os.path.expanduser("~"), ".local", "share", main_folder)
	return base

basedir = app_get_data_folder()
folder_sqlite = os.path.join(basedir, "DATABASE UTAMA")
os.makedirs(folder_sqlite, exist_ok=True)

def path_database():
	path = os.path.join(folder_sqlite, "pos.db")
	return path
	
conn = sqlite3.connect(path_database())
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def create_table(name, table_header):
	cursor.execute(f"""
	CREATE TABLE IF NOT EXISTS {name} (
		id INTEGER PRIMARY KEY AUTOINCREMENT, {table_header})""")

create_table("produk", "id_produk TEXT, barcode TEXT, nama TEXT, kategori TEXT, catatan TEXT, kadaluarsa TEXT, satuan_beli TEXT, satuan_jual TEXT, isi_satuan INTEGER, supplier TEXT, harga_beli INTEGER, harga_modal INTEGER, harga_jual INTEGER, jumlah INTEGER, jumlah_tertinggi INTEGER, stok_minimum INTEGER, poin INTEGER")
create_table("riwayat", "waktu TEXT, aksi TEXT, data TEXT")
create_table("info_host", "SSID TEXT, password TEXT")

def get_data(tabel):
	cursor.execute(f"SELECT * FROM {tabel}")
	dt = cursor.fetchall()
	data = [dict(row) for row in dt]
	return data
	
def now():
	return datetime.now().strftime("%d/%m/%Y")

def get_local_ip():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ip = s.getsockname()[0]
		s.close()
		return ip
	except Exception:
		return "192.168.43.1/url_default"
			
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
			
def resource_path(filename):
	return filename
	"""
	try:
		base_path = sys._MEIPASS
	except AttributeError:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, filename)
	"""
def rentang(bulan, tahun):
	awal = datetime(tahun, bulan, 1)
	akhir = datetime(tahun, bulan + 1, 1) - timedelta(days=1) if bulan < 12 else datetime(tahun + 1, 1, 1) - timedelta(days=1)
	return awal, akhir



app_flask = Flask(__name__)

@app_flask.route("/tes", methods=["GET"])
def tes():
	return jsonify({"status": "Berhasil"})

server = None
server_thread = None
server_running = False

def start_server():
	global server, server_thread, server_running
	if not server_running:
		server = make_server("0.0.0.0", PORT, app_flask)
		server_thread = threading.Thread(target=server.serve_forever, daemon=True)
		server_thread.start()
		server_running = True
		
def stop_server():
	global server, server_running
	if server_running and server:
		server.shutdown()
		server = None
		server_running = False



class ImageButton(ButtonBehavior, Image):
    pass
    				
class WidgetHelper:
	def add_color(self,frame,color,radius = (0,0,0,0)):
		warna = get_color_from_hex(color)
		with frame.canvas.before:
			Color(*warna)
			frame.bg_rect = RoundedRectangle(size=frame.size, pos=frame.pos, radius=[radius[0], radius[1], radius[2], radius[3]])
		frame.bind(size=self._update_rect, pos=self._update_rect)
	
	def _update_rect(self, instance, value):
		instance.bg_rect.size = instance.size
		instance.bg_rect.pos = instance.pos
    	
	def frame(
		self,
		orientation = "vertical",
		padding = 10,
		spacing = 10,
		size_hint_y = 1,
		bg = "#FFFFFF",
		radius = (0,0,0,0)
	):
		box = BoxLayout(
			orientation = orientation,
			padding = padding,
			spacing = spacing,
			size_hint_y = size_hint_y
		)
		self.add_color(box, bg, radius)
		return box
		
	def frame_grid(
		self,
		kolom = 1,
		spacing = 10,
		size_hint_y = 1,
		size_hint_x = 1,
		bg = "#FFFFFF",
		radius = (0,0,0,0),
		padding = 10
	):
		grid = GridLayout(
			cols = kolom,
			spacing = spacing,
			size_hint_y = size_hint_y,
			size_hint_x = size_hint_x,
			padding = padding
		)
		self.add_color(grid, bg, radius)
		return grid
	
	def label(
		self,
		teks="",
		padding=10,
		halign="center",
		valign="center",
		font_size=18,
		warna="#000000",
		size_hint_y=1,
		size_hint_x=1,
		bold=False
	):
		lbl = Label(
			text = teks,
			font_size = font_size,
			color = get_color_from_hex(warna),
			size_hint_y = size_hint_y,
			size_hint_x = size_hint_x,
			bold = bold,
			halign = halign,
			valign = valign,
			padding = padding
		)
		lbl.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
		return lbl
		
	def button(
		self,
		teks="",
		font_size=18,
		warna="#ffffff",
		size_hint_y=1,
		size_hint_x=1,
		bold=False,
		halign="center",
		valign="center",
		padding=10,
		bg=default_bg_btn,
		radius=(10,10,10,10)
	):
		btn = Button(
			text=teks,
			font_size=font_size,
			color=get_color_from_hex(warna),
			size_hint_y=size_hint_y,
			size_hint_x=size_hint_x,
			bold=bold,
			halign=halign,
			valign=valign,
			padding=padding,
			background_normal="",
			background_color=(0,0,0,0)
		)
		self.add_color(btn, bg, radius)
		btn.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
		return btn
		
	def input(self, placeholder="", teks="", multiline=False, size_hint=(1,None), height=70, input_filter="text", padding=10):
		inp = TextInput(
			hint_text = placeholder,
			text = teks,
			multiline = multiline,
			size_hint = size_hint,
			height = height,
			padding = padding
		)
		if input_filter.lower() != "text":
			inp.input_filter = input_filter
		return inp
	
	def spinner(self, value=(), text="", size_hint=(1,None), height=70):
		spin = Spinner(
			text=text,
			values=value,
			size_hint=size_hint,
			height=height
		)
		return spin
		
class HelperUtama:
	def __init__(self, widget_maker, **kwargs):
		super().__init__(**kwargs)
		self.maker = widget_maker
	
	def add_background_image(self, frame, image_path, radius=(0,0,0,0)):
		with frame.canvas.before:
			frame.bg_image = RoundedRectangle(
				source=resource_path(image_path),
				size=frame.size,
				pos=frame.pos,
				radius=[radius[0], radius[1], radius[2], radius[3]]
			)
		frame.bind(size=self._update_image_rect, pos=self._update_image_rect)
		
	def _update_image_rect(self, instance, value):
		instance.bg_image.size = instance.size
		instance.bg_image.pos = instance.pos
	
	def make_scrolled(self, parent, frame, x=False):
		frame.bind(minimum_height=frame.setter('height'))
		frame.bind(minimum_width=frame.setter('width'))	
		scroll = ScrollView(do_scroll_x=x)
		scroll.add_widget(frame)
		parent.add_widget(scroll)
		
	def table_maker(self, parent, header, x=False):
		frame = self.maker.frame_grid(len(header), bg="#CFCBCB", padding=0, radius=(20,20,20,20), size_hint_y=None, size_hint_x=None, spacing=2)
		self.make_scrolled(parent, frame, x)
		
		for i, teks in enumerate(header):
			label = self.maker.label(
				teks,
				font_size=22,
				padding=2,
				bold=True,
				warna="#ffffff",
				size_hint_x=None,
				size_hint_y=None
			)
			radius = (0,0,0,0)
			panjang = 250
			if i == 0:
				radius = (20,0,0,0)
				panjang = 100
			elif i == len(header) - 1:
				radius = (0,20,0,0)
			self.maker.add_color(label, default_bg_btn, radius)
			label.width = panjang
			label.height = 75
			frame.add_widget(label)
		return frame
		
	def input_maker(self, parent, items):
		elements = {}
		for key, placeholder, teks, tipe in items:
			lbl = self.maker.label(key.replace("_"," ").upper(), font_size=24, bold=True, halign="left")
			input = self.maker.input(placeholder, teks=teks, input_filter=tipe)
			elements[key] = input
			for a in [lbl, input]:
				parent.add_widget(a)
		
		values = list(elements.values())
		if values:
			values[0].focus = True
			for i in range(len(values) - 1):
				values[i].bind(on_text_validate=lambda x, idx=i: setattr(values[idx + 1], "focus", True))
				
		return elements
	
	def spin_maker(self, parent, data):
		spinners = {}
		for key, teks, values in data:
			spin = self.maker.spinner(
				value=values,
				text=teks
			)
			spinners[key] = spin
			parent.add_widget(spin)
		return spinners
		
	def tampilkan_tanggal(self, parent=None, days=None):
		if parent is None:
			parent = self.tengah_kalender
		if days is None:
			days = self.days
		parent.clear_widgets()
		start, end = rentang(self.month, self.year)
		day_start = start.strftime("%A").lower()
		idx = days.index(day_start)
		hari_pertama = start.day
		hari_terakhir = end.day
		
		for _ in range(idx):
			empty = self.maker.label("")
			parent.add_widget(empty)
			
		for tanggal in range(hari_pertama, hari_terakhir + 1):
			sekarang = datetime(self.year, self.month, tanggal).date()
			
			bg = universal_background
			if sekarang == datetime.now().date():
				bg = "#67F05B"
				
			btn = self.maker.button(str(tanggal), bg=bg, font_size=20, bold=True, radius=(5,5,5,5))
			btn.bind(on_press=lambda instance, tgl=tanggal: self.pilih_tanggal(instance, tgl))
			parent.add_widget(btn)
			
	def pilih_tanggal(self, instance, tgl):
		hasil = datetime(self.year, self.month, tgl)
		if self.on_pilih:
			self.on_pilih(hasil)
		self.pop.dismiss()
	
	def ganti_tahun(self, instance, angka):
		self.year += angka
		self.label_year.text = str(self.year)
		self.tampilkan_tanggal()
	
	def ganti_bulan(self, instance, angka):
		if self.month + angka > 12:
			self.year += 1
			self.month = 1
		elif self.month + angka < 1:
			self.year -= 1
			self.month = 12
		else:
			self.month += angka
			
		self.label_year.text = str(self.year)
		self.label_month.text = calendar.month_name[self.month]
		self.tampilkan_tanggal()
		
	def kalender(self, on_pilih=None):
		self.on_pilih = on_pilih
		self.tanggal_sekarang = datetime.now().date()
		box = self.maker.frame("vertical", padding=5, spacing=0)
		atas = self.maker.frame("horizontal", size_hint_y=None)
		atas.height = 100
		bawah = self.maker.frame("horizontal", size_hint_y=None)
		bawah.height = 100
	
		self.tengah_kalender = self.maker.frame_grid(7, 2, bg="#474C41")
		for fr in [atas, bawah, self.tengah_kalender]:
			box.add_widget(fr)
		
		self.year = datetime.now().year
		self.month = datetime.now().month
		self.day = datetime.now().day
		
		self.label_year = self.maker.label(str(self.year), font_size=20, bold=True, padding=10)
		self.prevy = self.maker.button("<", font_size=20, bold=True, radius=(5,5,5,5))
		self.nexty = self.maker.button(">", font_size=20, bold=True, radius=(5,5,5,5))
		self.prevy.bind(on_press=lambda instance: self.ganti_tahun(instance, -1))
		self.nexty.bind(on_press=lambda instance: self.ganti_tahun(instance, 1))
		
		for item in [self.prevy, self.label_year, self.nexty]:
			atas.add_widget(item)
			
		self.label_month = self.maker.label(str(calendar.month_name[self.month]), font_size=20, bold=True, padding=10)
		self.prevm = self.maker.button("<", font_size=20, bold=True, radius=(5,5,5,5))
		self.nextm = self.maker.button(">", font_size=20, bold=True, radius=(5,5,5,5))
		self.prevm.bind(on_press=lambda instance: self.ganti_bulan(instance, -1))
		self.nextm.bind(on_press=lambda instance: self.ganti_bulan(instance, 1))
		
		for item in [self.prevm, self.label_month, self.nextm]:
			atas.add_widget(item)
		
		self.days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
		for day in self.days:
			lbl_day = self.maker.label(day[:3].capitalize(), padding=5)
			bawah.add_widget(lbl_day)
		
		self.tampilkan_tanggal()	
		self.pop = Popup(
			title="Calendar",
			content=box,
			size_hint=(0.9,0.5),
			overlay_color=(0,0,0,0)
		)
		self.pop.open()
		
	def popup_informasi(self, judul, pesan):
		warna = "#1DAF4B"
		if judul.lower() in ["gagal", "error"]:
			warna = "#AF1D1D"
			
		box = self.maker.frame("vertical")
		label = self.maker.label(pesan, font_size=24, warna=warna, padding=20)
		yes = self.maker.button("Ok", bg="#6FB755", warna="#ffffff", size_hint_y=None)
		yes.height = 70
		
		for item in [label, yes]:
			box.add_widget(item)
		pop = Popup(title=judul, overlay_color=(0,0,0,0), content=box, size_hint=(0.7,0.3))
		pop.open()
		yes.bind(on_press=pop.dismiss)
		
	def popup_konfirmasi(self, judul, pesan, on_ya=None, on_tidak=None):
		box = self.maker.frame("vertical")
		label = self.maker.label(pesan, font_size=24, padding=20)
		
		tombol_box = self.maker.frame("horizontal")
		ya = self.maker.button("Oke", bg="#6FB755", warna="#ffffff", size_hint_y=None)
		batal = self.maker.button("Batal", bg="#B75556", warna="#ffffff", size_hint_y=None)
		ya.height = 70
		batal.height = 70
		
		for item in [ya, batal]:
			tombol_box.add_widget(item)
		for item in [label, tombol_box]:
			box.add_widget(item)
		
		pop = Popup(title=judul, overlay_color=(0,0,0,0), content=box, size_hint=(0.7,0.35))
		
		def pilih_ya(instance):
			pop.dismiss()
			if on_ya:
				on_ya()
		
		def pilih_tidak(instance):
			pop.dismiss()
			if on_tidak:
				on_tidak()
		
		ya.bind(on_press=pilih_ya)
		batal.bind(on_press=pilih_tidak)
		pop.open()
		
	def hapus_row(self, tabel, kata_kunci, key):
		judul = ""
		pesan = ""
		try:
			cursor.execute(f"DELETE FROM {tabel} WHERE {kata_kunci} = ?", (key, ))
			conn.commit()
			judul = "Berhasil"
			pesan = f"Data {kata_kunci} {key} telah dihapus dari {tabel}"
		except Exception as e:
			conn.rollback()
			judul = "Error"
			pesan = f"Gagal: {e}"
		self.popup_informasi(judul, pesan)
		
class TambahProduk:
	def __init__(self, produk, parent, setup, table, **kwargs):
		super().__init__(**kwargs)
		self.produk = produk
		self.parent = parent
		self.setup = setup
		self.table = table
		
	def reset(self):
		self.produk = get_data("produk")
		self.open_form()
		
	def open_form(self):
		self.parent.clear_widgets()
		frame = self.setup.frame("vertical", bg="#ffffff70", size_hint_y=None, spacing=30, padding=25)
		frame.size_hint_x = 1
		self.table.make_scrolled(self.parent, frame)
		
		info_inputs = [
			("barcode", "Masukkan barcode...", "", "text"),
			("nama", "Masukkan nama produk...", "", "text"),
			("jumlah", "Masukkan jumlah stok...", "0", "int"),
			("harga_beli", "Masukkan harga beli...", "0", "float"),
			("isi_satuan", "Masukkan isi satuan...", "0", "int"),
			("harga_jual", "Masukkan harga jual...", "0", "float"),
			("poin", "Masukkan poin...", "0", "int"),
			("stok_minimum", "Masukkan stok minimum...", "0", "int"),
			("kategori", "Masukkan kategori...", "", "text"),
			("satuan_beli", "Masukkan satuan beli...", "", "text"),
			("satuan_jual", "Masukkan satuan jual...", "", "text"),
			("supplier", "Masukkan supplier...", "", "text")
		]
		self.inputs = self.table.input_maker(frame, info_inputs)
		combo = [
			("kategori", "Pilih kategori", list({p["kategori"] for p in self.produk})),
			("satuan_beli", "Pilih satuan beli", list({p["satuan_beli"] for p in self.produk})),
			("satuan_jual", "Pilih satuan jual", list({p["satuan_jual"] for p in self.produk})),
			("supplier", "Pilih supplier", list({p["supplier"] for p in self.produk}))
		]
		self.combos = self.table.spin_maker(frame, combo)
		
		self.catatan = self.setup.input(placeholder="Masukkan catatan...", multiline=True, height=200)
		frame.add_widget(self.catatan)
		
		frame_tanggal = self.setup.frame("horizontal", bg="#ffffff70", padding=10, size_hint_y=None)
		frame_tanggal.height = 100
		self.parent.add_widget(frame_tanggal)
		self.input_tanggal = self.setup.input(teks=datetime.now().strftime("%m/%d/%y"))
		btn_kalender = self.setup.button("Pilih tanggal kadaluarsa", warna="#ffffff")
		btn_kalender.bind(on_press=lambda instance: self.open_kalender(instance))
		
		for item in [self.input_tanggal, btn_kalender]:
			frame_tanggal.add_widget(item)
				
		fr = self.setup.frame("horizontal", bg="#ffffff70", spacing=10, size_hint_y=None)
		fr.height = 100
		for teks, warna, command in [
			("Lihat info harga", "#B75556", self.lihat_info_harga),
			("Simpan", "#6FB755", self.simpan_produk_baru)
		]:
			btn = self.setup.button(teks, bg=warna, font_size=20)
			btn.bind(on_press=command)
			fr.add_widget(btn)
		self.parent.add_widget(fr)
		
	def open_kalender(self, instance):
		self.table.kalender(on_pilih=self.terima_tanggal)
	
	def terima_tanggal(self, tgl):
		self.input_tanggal.text = tgl.strftime("%m/%d/%y")
			
	def lihat_info_harga(self, instance):
		teks_info = ""
		try:
			harga_beli = int(self.inputs["harga_beli"].text.strip())
			isi = int(self.inputs["isi_satuan"].text.strip())
			harga_modal = harga_beli / isi
			teks_info = f"Harga beli produk: {pretty_money(harga_beli)}\nIsi per satuan: {isi} unit\nHarga modal produk: {pretty_money(round(harga_modal))}"		
		except (ValueError, ZeroDivisionError) as e:
			teks_info = str(e)
		pop = Popup(
			title="INFORMASI HARGA",
			content=self.setup.label(teks_info, warna="#ffffff", bold=True, font_size=22),
			size_hint=(0.8,0.3),
			overlay_color=(0,0,0,0)
		)
		pop.open()
		
	def simpan_produk_sekarang(self, data):
		keys = list(data.keys())
		rows = ", ".join(keys)
		placeholder = ", ".join(["?"] * len(keys))
		try:
			cursor.execute(f"INSERT INTO produk ({rows}) VALUES ({placeholder})", (list(data.values())))
			cursor.execute("INSERT INTO riwayat (waktu, aksi, data) VALUES (?, ?, ?)", (now(), "Tambah produk baru", json.dumps(data)))
			conn.commit()
			self.table.popup_informasi("Berhasil", f"Produk {data.get('nama','')} telah disimpan")
			self.reset()
		except Exception as e:
			conn.rollback()
			self.table.popup_informasi("Gagal", "Produk gagal disimpan: " + str(e))
			
	def simpan_produk_baru(self, instance):
		result = {key: value.text.strip() for key, value in self.inputs.items()}
		combos = {key: value.text.strip() for key, value in self.combos.items()}
		exp = self.input_tanggal.text.strip()
		note = self.catatan.text.strip()
		try:
			ktgr = combos.get("kategori","")
			ktgr_inp = result.get("kategori","")
			sb = combos.get("satuan_beli","")
			sb_inp = result.get("satuan_beli","")
			sj = combos.get("satuan_jual","")
			sj_inp = result.get("satuan_jual","")
			sup = combos.get("supplier","")
			sup_inp = result.get("supplier","")
			
			kategori = ktgr if ktgr.lower() not in ["", "pilih kategori"] else ktgr_inp
			satuan_beli = sb if sb.lower() not in ["", "pilih satuan beli"] else sb_inp
			satuan_jual = sj if sj.lower() not in ["", "pilih satuan jual"] else sj_inp
			supplier = sup if sup.lower() not in ["", "pilih supplier"] else sup_inp
			
			jumlah = int(result.get("jumlah",0))
			harga_beli = float(result.get("harga_beli",0))
			isi_satuan = int(result.get("isi_satuan",0))
			harga_modal = harga_beli / isi_satuan if isi_satuan > 0 else harga_beli
			harga_jual = float(result.get("harga_jual",0))
			jumlah = int(result.get("jumlah",0))
			stok_minimum = int(result.get("stok_minimum",0))
			poin = int(result.get("poin",0))
			
			if not all([
				result.get("barcode",""),
				result.get("nama",""),
				jumlah,
				harga_modal,
				harga_jual
			]):
				self.table.popup_informasi("Gagal", "Barcode, nama, jumlah stok, harga jual, harga beli, dan isi satuan wajib diisi")
				return
			
			sudah_ada = next((p for p in self.produk if p["nama"].lower() == result.get("nama","").lower() or p["barcode"] == result.get("barcode","")), None)
			if sudah_ada:
				self.table.popup_informasi("Gagal", "Produk dengan nama atau barcode tersebut sudah ada. Silahkan pilih tambah stok atau berikan nama atau barcode yang lain")
				return
			data_akhir = {
				"id_produk": datetime.now().strftime("%f"),
				"barcode": result.get("barcode",""),
				"nama": result.get("nama",""),
				"kategori": kategori,
				"catatan": note,
				"kadaluarsa": exp,
				"satuan_beli": satuan_beli,
				"satuan_jual": satuan_jual,
				"isi_satuan": isi_satuan,
				"supplier": supplier,
				"harga_beli": harga_beli,
				"harga_modal": harga_modal,
				"harga_jual": harga_jual,
				"jumlah": jumlah,
				"jumlah_tertinggi": jumlah,
				"stok_minimum": stok_minimum,
				"poin": poin
			}
			self.table.popup_konfirmasi(
				"Konfirmasi",
				"Data produk sudah siap. Simpan sekarang?",
				on_ya = lambda: self.simpan_produk_sekarang(data_akhir)
			)
				
		except Exception as e:
			self.table.popup_informasi("Error", str(e))

class RiwayatAktivitas:
	def __init__(self, parent, setup, table, **kwargs):
		super().__init__(**kwargs)
		self.parent = parent
		self.setup = setup
		self.table = table
		
	def lihat_detail(self, instance, id):
		data = next((json.loads(p["data"]) for p in self.data if p["id"] == id), None)
		if data is not None:
			box = self.setup.frame_grid(3, spacing=2)
			for key, value in data.items():
				val = str(value)
				if key.lower() in [
					"harga_beli",
					"harga_jual",
					"harga_modal"
				]:
					val = pretty_money(value)
				a = self.setup.label(key.replace("_", " ").capitalize())
				b = self.setup.label(":")
				c = self.setup.label(val)
				for var in [a,b,c]:
					var.halign = "left"
					var.font_size = 20
					box.add_widget(var)
			pop = Popup(title=f"Detail {data.get('nama','')}", content=box, size_hint=(0.95,0.80), overlay_color=(0,0,0,0))
			pop.open()
			
	def hapus_riwayat(self, instance, id):
		self.table.popup_konfirmasi(
			"Konfirmasi",
			"Apa anda yakin ingin menghapus riwayat ini?",
			on_ya = lambda: self.table.hapus_row("riwayat", "id", id)
		)
					
	def tampilkan(self, instance=None, teks_cari=""):
		self.frame_utama.clear_widgets()
		for item in reversed(self.data):
			if teks_cari.lower() in item["waktu"].lower():
				for_show = [("Waktu", item["waktu"]), ("Aksi", item.get("aksi", "-"))]
				for key, value in json.loads(item["data"]).items():
					if key.lower() in ["barcode", "nama", "jumlah", "harga_modal", "harga_jual"]:
						for_show.append((key.replace("_", " ").lower().capitalize(), pretty_money(value) if key.lower() in ["harga_modal", "harga_jual"] else str(value)))
				
				fr = self.setup.frame_grid(3, bg="#DFF3FF99", padding=20, radius=(10,10,10,10), size_hint_y=None)
				fr.height = len(for_show) * 80
				self.frame_utama.add_widget(fr)
				
				for teks, val in for_show:
					a = self.setup.label(teks, font_size=22, halign="left")
					b = self.setup.label(":", font_size=22)
					c = self.setup.label(val, font_size=22, halign="left")
					for label in [a,b,c]:
						fr.add_widget(label)
						
				detail = self.setup.button("Detail", font_size=22, size_hint_y=None)
				hapus = self.setup.button("Hapus", font_size=22, size_hint_y=None)
				detail.bind(on_press=lambda instance, id=item["id"]: self.lihat_detail(instance, id))
				hapus.bind(on_press=lambda instance, id=item["id"]: self.hapus_riwayat(instance, id))
				for item in [detail, hapus]:
					item.height = 70
					fr.add_widget(item)
	
	def hapus_semua_sekarang(self):
		try:
			cursor.execute("DELETE FROM riwayat")
			conn.commit()
			self.table.popup_informasi("Berhasil", "Seluruh data riwayat telah dihapus")
		except Exception as e:
			conn.rollback()
			self.table.popup_informasi("Error", str(e))
			
	def hapus_semua(self, instance):
		if not self.data:
			self.table.popup_informasi("Gagal", "Data riwayat kosong")
			return
		self.table.popup_konfirmasi(
			"Konfirmasi",
			"Apa Anda yakin ingin menghapus seluruh data riwayat?",
			on_ya = lambda: self.hapus_semua_sekarang()
		)
					
	def open_function(self):
		self.parent.clear_widgets()
		self.data = get_data("riwayat")
		
		self.atas = self.setup.frame("horizontal", bg="#ffffff00", size_hint_y=None)
		self.atas.height = 80
		self.parent.add_widget(self.atas)
		
		self.cari = self.setup.input(placeholder="Masukkan waktu aktivitas")
		btn_hapus_semua = self.setup.button("Hapus semua", bg="#B75556", font_size=22, size_hint_y=None)
		btn_hapus_semua.size_hint_x = 0.4
		btn_hapus_semua.height = 70
		
		for item in [self.cari, btn_hapus_semua]:
			self.atas.add_widget(item)
			
		self.frame_utama = self.setup.frame("vertical", bg="#ffffff00", size_hint_y=None)
		self.table.make_scrolled(self.parent, self.frame_utama)
		self.tampilkan()
		self.cari.bind(text=self.tampilkan)
		btn_hapus_semua.bind(on_press=self.hapus_semua)


#NANTI DILANJUTKAN

class LaporanStok:
	def __init__(self, parent, setup, table, **kwargs):
		super().__init__(**kwargs)
		self.parent = parent
		self.setup = setup
		self.table = table
		self.produk = sorted(get_data("produk"), key=lambda x: x["jumlah"])
		self.data = self.produk
	
	def halaman_berikutnya(self, instance):
		if (self.page + 1) * self.per_page < len(self.produk):
			self.page += 1
			start = self.page * self.per_page
			end = start + self.per_page
			self.data = self.produk[start:end]
			self.tampilkan_produk()
	
	def halaman_sebelumnya(self, instance):
		if self.page > 0:
			self.page -= 1
			start = self.page * self.per_page
			end = start + self.per_page
			self.data = self.produk[start:end]	
			self.tampilkan_produk()
				
	def open_function(self):
		self.parent.clear_widgets()
		self.page = 0
		self.per_page = 20
		self.daftar_produk()
		
	def lihat_detail(self, instance, id):
		produk = next((p for p in self.produk if p["id_produk"] == id), None)
		if produk is not None:
			box = self.setup.frame_grid(3, 2)
			for key, value in produk.items():
				val = str(value)
				if key.lower() in ["harga_modal", "harga_beli", "harga_jual"]:
					val = pretty_money(value)
				a = self.setup.label(key.replace("_"," ").capitalize(), font_size=22, halign="left")
				b = self.setup.label(":", font_size=22, halign="left")
				c = self.setup.label(val, font_size=22, halign="left")
				for item in [a,b,c]:
					box.add_widget(item)
			pop = Popup(title=f"Detail {produk['nama']}", content=box, size_hint=(0.98,0.9), overlay_color=(0,0,0,0))
			pop.open()
	
	def tambah_stok_sekarang(self, item):
		result = int(self.tambahan["Tambahan stok"].text.strip())
		stok_tertinggi = item["jumlah_tertinggi"]
		stok_terbaru = result + item["jumlah"]
		if stok_terbaru > stok_tertinggi:
			stok_tertinggi = stok_terbaru
		info_tambah = {
			"nama": item["nama"],
			"barcode": item["barcode"],
			"jumlah_tertinggi": stok_tertinggi,
			"jumlah": stok_terbaru,
			"tambahan": result
		}
		try:
			cursor.execute("UPDATE produk SET jumlah = ?, jumlah_tertinggi = ? WHERE id_produk = ?", (stok_terbaru, stok_tertinggi, item["id_produk"]))
			cursor.execute("INSERT INTO riwayat (waktu, aksi, data) VALUES (?, ?, ?)", (now(), "Tambah stok produk", json.dumps(info_tambah)))
			conn.commit()
			self.p.dismiss()
			self.table.popup_informasi("Berhasil", f"Stok produk {item['nama']} telah diperbarui")
		except Exception as e:
			self.p.dismiss()
			self.table.popup_informasi("Gagal", str(e))
	
	def konfirmasi_simpan(self, instance, item):
		self.table.popup_konfirmasi(
			"Konfirmasi",
			"Apakah data sudah benar?",
			on_ya = lambda: self.tambah_stok_sekarang(item)
		)
			
	def tambah_stok(self, instance, id):
		item = next((p for p in self.produk if p["id_produk"] == id), None)
		if item is not None:
			box = self.setup.frame("vertical")
			self.tambahan = self.table.input_maker(box, [("Tambahan stok", "Masukkan tambahan stok", "0", "int")])
			btn = self.setup.button("Simpan", font_size=22)
			btn.bind(on_press=lambda instance: self.konfirmasi_simpan(instance, item))
			box.add_widget(btn)
			self.p = Popup(title="Tambah stok " + item["nama"], content=box, size_hint=(0.8,0.3), overlay_color=(0,0,0,0))
			self.p.open()
		
	def tampilkan_produk(self, instance=None, t=""):
		self.frame_table.clear_widgets()
		header = ["No", "Nama", "Jumlah stok", "Status"]
		tabel = self.table.table_maker(self.frame_table, header, True)
		for i, item in enumerate(self.data):
			if t.lower() in item["nama"].lower() or t in item["barcode"]:
				status = "Cukup"
				warna = "#000000"
				if 0 < item["jumlah"] < item["stok_minimum"]:
					status = "Kurang"
					warna = "#D0A61D"
				elif item["jumlah"] <= 0:
					status = "Habis"
					warna = "#D01D1D"
					
				arguments = [
					str(i),
					item.get("nama",""),
					str(item.get("jumlah",0)) + " " + item.get("satuan_jual",""),
					status
				]
				for j, teks in enumerate(arguments):
					lbl = self.setup.button(
						teks,
						font_size=22,
						padding=10,
						size_hint_x=None,
						size_hint_y=None,
						halign = "left",
						warna = warna,
						bg="#ffffff00"
					)
					if j == 1:
						lbl.bind(on_press=lambda instance, id=item["id_produk"]: self.lihat_detail(instance, id))
					elif j == 2:
						lbl.bind(on_press=lambda instance, id=item["id_produk"]: self.tambah_stok(instance, id))
					panjang = 250
					radius = (0,0,0,0)
					if j == 0:
						panjang = 100
					if i == len(self.data):
						if j == 0:
							radius = (0,0,0,20)
						elif j == len(arguments) - 1:
							radius = (0,0,20,0)
					self.setup.add_color(lbl, "#F6FFFF", radius)
					lbl.width = panjang
					lbl.height = 75
					tabel.add_widget(lbl)
				
	def daftar_produk(self):
		self.cari = self.setup.input(placeholder="Masukkan nama atau barcode")
		prev = self.setup.button("<", font_size=22)
		next = self.setup.button(">", font_size=22)
		fr = self.setup.frame("horizontal", size_hint_y=None)
		fr.height = 90
		for i, item in enumerate([self.cari, prev, next]):
			if i != 0:
				item.size_hint_x = None
				item.width = 50
			fr.add_widget(item)
		self.frame_table = self.setup.frame("vertical")
		for item in [fr, self.frame_table]:
			self.parent.add_widget(item)
		self.cari.bind(text=self.tampilkan_produk)
		self.tampilkan_produk()
		
class DaftarProdukDiskon:
	def __init__(self, parent, setup, table, **kwargs):
		super().__init__(**kwargs)
		self.parent = parent
		self.setup = setup
		self.table = table
		
	def open_function(self):
		self.parent.clear_widgets()
				
class Dashboard:
	def __init__(self, parent, setup, table, **kwargs):
		super().__init__(**kwargs)
		self.parent = parent
		self.setup = setup
		self.table = table
		
	def kalkulasi_data(self):
		total_stok = 0
		total_modal = 0
		total_jual = 0
		for p in self.produk:
			stok = p["jumlah"]
			total_stok += stok
			total_modal += p["harga_modal"] * stok
			total_jual += p["harga_jual"] * stok
		
		total_untung = total_jual - total_modal
		
		info = {
			"jumlah produk": str(len(self.produk)) + " unit",
			"total jumlah stok": str(total_stok) + " pcs",
			"total harga pokok penjualan tersisa": pretty_money(total_modal),
			"total estimasi penjualan tersisa": pretty_money(total_jual),
			"total perkiraan keuntungan tersisa": pretty_money(total_untung)
		}
		self.atas.height = len(list(info.keys())) * 100
		for key, value in info.items():
			a = self.setup.label(key.capitalize(), font_size=22, halign="left")
			b = self.setup.label(":", font_size=22, halign="left")
			c = self.setup.label(value, font_size=22, halign="left")
			for item in [a,b,c]:
				self.atas.add_widget(item)
	
	def lihat_laporan_stok(self, instance):
		self.laporan_stok.open_function()
		
	def daftar_produk_diskon(self, instance):
		self.produk_diskon.open_function()
		
	def plate_buttons(self):
		buttons = [
			("features.png", self.lihat_laporan_stok, "Laporan stok"),
			("box.png", self.daftar_produk_diskon, "Daftar produk diskon")
		]
		self.bawah.height = 150
		
		for gambar, command, teks in buttons:
			fr = self.setup.frame("vertical", bg="#ffffff00")
			self.bawah.add_widget(fr)
			label = self.setup.label(teks, font_size=22)
			pict = ImageButton(
				source=resource_path(f"Pictures/{gambar}"),
				size_hint=(1,1),
				size=(70,70),
				pos_hint={"center_x": 0.5}
			)
			pict.bind(on_press=command)
			for item in [pict, label]:
				fr.add_widget(item)
				
	def open_function(self):
		self.parent.clear_widgets()
		self.utama = self.setup.frame("vertical", size_hint_y=None)
		self.table.make_scrolled(self.parent, self.utama)
		
		self.atas = self.setup.frame_grid(3, 2, bg=universal_background + "50", size_hint_y=None, radius=(20,20,20,20))
		self.bawah = self.setup.frame_grid(3, 2, size_hint_y=None)
		for item in [self.atas, self.bawah]:
			self.utama.add_widget(item)
		self.produk = get_data("produk")
		self.laporan_stok = LaporanStok(self.parent, self.setup, self.table)
		self.produk_diskon = DaftarProdukDiskon(self.parent, self.setup, self.table)
		self.kalkulasi_data()
		self.plate_buttons()	

class Lainnya:
	def __init__(self, parent, setup, table, **kwargs):
		super().__init__(**kwargs)
		self.parent = parent
		self.setup = setup
		self.table = table
	
	def dapatkan_info(self):
		self.info_server["Status server"] = "ONLINE" if server_running else "OFFLINE"
		ip = get_local_ip()
		self.info_server["URL utama"] = f"http://{ip}:{PORT}"
		self.info_server["URL alternatif"] = f"http://127.0.0.1:{PORT}"
		self.info_server["Alamat IP"] = ip
		self.info_server["PORT"] = PORT
	
	def tampilkan_info_server(self):
		info_host = get_data("info_host")
		nama = ""
		pw = ""
		if info_host:
			nama = info_host[0]["SSID"]
			pw = info_host[0]["password"]
			
		self.info_server["WIFI SSID"] = nama
		self.info_server["WIFI password"] = pw
		
		self.atas.clear_widgets()
		gambar_status = ImageButton(
			source=resource_path("Pictures/server-off.png") if not server_running else resource_path("Pictures/server-on.png"),
			size_hint=(1,1),
			size=(100,100),
			pos_hint={"center_x": 0.5}	
		)
		
		fr = self.setup.frame_grid(3,2,bg="#ffffff00")
		for item in [gambar_status, fr]:
			self.atas.add_widget(item)
			
		for key, value in self.info_server.items():
			a = self.setup.label(key, font_size=22, halign="left")
			b = self.setup.label(":", font_size=22, halign="left")
			c = self.setup.label(str(value), font_size=22, halign="left")
			for i, item in enumerate([a,b,c]):
				if i != 2:
					item.size_hint_x = 0.5
				fr.add_widget(item)
					
	def aktifkan_server(self, instance):
		start_server()
		self.dapatkan_info()
		self.tampilkan_info_server()
	
	def matikan_server(self, instance):
		stop_server()
		self.dapatkan_info()
		self.tampilkan_info_server()
			
	def open_connector(self, instance):
		self.fr_utama.clear_widgets()
		self.atas = self.setup.frame("vertical", bg="#ffffff99", radius=(20,20,20,20), size_hint_y=None)
		bawah = self.setup.frame("horizontal", bg="#ffffff00", size_hint_y=None)
		bawah.height = 100
		for item in [self.atas, bawah]:
			self.fr_utama.add_widget(item)
			
		aktif = self.setup.button("Aktifkan server", bg="#6FB755")
		mati = self.setup.button("Matikan server", bg="#B75556")
		edit = self.setup.button("Pengaturan SSID")
		for item in [mati, aktif, edit]:
			bawah.add_widget(item)
		
		ip = get_local_ip()	
		self.info_server = {
			"Status server": "ONLINE" if server_running else "OFFLINE",
			"URL utama": f"http://{ip}:{PORT}",
			"URL alternatif": f"http://127.0.0.1:{PORT}",
			"Alamat IP": ip,
			"PORT": PORT,
			"WIFI SSID": "",
			"WIFI password": ""
		}
		self.atas.height = len(list(self.info_server.keys())) * 100 + 150
		aktif.bind(on_press=self.aktifkan_server)
		mati.bind(on_press=self.matikan_server)
		edit.bind(on_press=self.edit_ssid)
		self.tampilkan_info_server()
	
	def simpan_ssid(self, instance):
		result = {key: value.text.strip() for key, value in self.info.items()}
		try:
			cursor.execute("DELETE FROM info_host")
			cursor.execute("INSERT INTO info_host (SSID, password) VALUES (?, ?)", (result["nama"], result["password"]))
			conn.commit()
			self.pop.dismiss()
			self.tampilkan_info_server()
		except Exception as e:
			self.table.popup_informasi("Error", str(e))
				
	def edit_ssid(self, instance):
		host = get_data("info_host")
		nama = ""
		pw = ""
		if host:
			nama = host[0]["SSID"]
			pw = host[0]["password"]
			
		box = self.setup.frame("vertical")
		info = [
			("nama", "Masukkan nama hotspot", nama, "text"),
			("password", "Masukkan password", pw, "text")
		]
		self.info = self.table.input_maker(box, info)
		btn = self.setup.button("Simpan", bg="#6FB755", size_hint_y=None)
		btn.height = 70
		box.add_widget(btn)
		btn.bind(on_press=self.simpan_ssid)
		
		self.pop = Popup(
			title = "Pengaturan SSID",
			content = box,
			size_hint = (0.7, 0.35),
			overlay_color = (0,0,0,0)
		)
		self.pop.open()
		
	def open_function(self):
		self.parent.clear_widgets()
		self.parent.padding = 20
		self.fr_utama = self.setup.frame("vertical", bg="#DFF3FF50", size_hint_y=None, radius=(10,10,10,10))
		self.table.make_scrolled(self.parent, self.fr_utama)
		
		info_button = [
			("network-cloud-computer.png", "Koneksi ke device lain", self.open_connector)
		]
		for gambar, teks, command in info_button:
			frame = self.setup.frame("horizontal", size_hint_y=None, bg="#DFF3FF00")
			frame.height = 100
			self.fr_utama.add_widget(frame)
			gambar = ImageButton(
				source=resource_path(f"Pictures/{gambar}"),
				size_hint=(None,1),
				size=(40,40),
				pos_hint={"x": 0}
			)
			btn = self.setup.button(teks, bg="#DFF3FF00", warna="#000000", halign="left", font_size=24)
			btn.bind(on_press=command)
			for item in [gambar, btn]:
				frame.add_widget(item)
													
class MainApp(App):
	def __init__(self, helper, table_helper, **kwargs):
		super().__init__(**kwargs)
		self.setup = helper
		self.table = table_helper
	
	def tampil_popup(self, pesan):
		popup = Popup(
			overlay_color=(0,0,0,0),
			title="Debug Info",
			content=Label(text=pesan),
			size_hint=(0.8, 0.4)
		)
		popup.open()
			
	def build(self):
		self.title = "Aplikasi manajemen produk pos"
		Window.clearcolor = (1,1,1,1)
		self.main_layout = self.setup.frame("vertical", padding=0, spacing=10)
		self.main_frames()
		self.halaman = 0
		self.per_halaman = 20
		
		self.produk = get_data("produk")
		self.set_bawah()
		self.tambah_produk = TambahProduk(self.produk, self.tengah, self.setup, self.table)
		self.riwayat_aktivitas = RiwayatAktivitas(self.tengah, self.setup, self.table)
		self.dashboard = Dashboard(self.tengah, self.setup, self.table)
		self.lainnya = Lainnya(self.tengah, self.setup, self.table)
		
		self.dashboard.open_function()
		return self.main_layout
				
	def tambah_produk_baru(self, instance):
		self.tambah_produk.open_form()
		
	def riwayat_aktivitas_produk(self, instance):
		self.riwayat_aktivitas.open_function()
	
	def menu_lainnya(self, instance):
		self.lainnya.open_function()
	
	def beranda(self, instance):
		self.dashboard.open_function()
				
	def set_bawah(self):
		info = [
			("home.png", self.beranda, "Beranda"),
			("add.png", self.tambah_produk_baru, "Tambah produk"),
			("list-check.png", self.riwayat_aktivitas_produk, "Riwayat"),
			("menu-burger.png", self.menu_lainnya, "Lainnya")
		]
		for gambar, command, teks in info:
			fr = self.setup.frame("vertical", spacing=5, bg="#ffffff00")
			self.bawah.add_widget(fr)
			label = self.setup.button(teks, bg="#ffffff00", warna="#000000")
			btn = ImageButton(
				source = resource_path(f"Pictures/{gambar}"),
				size_hint = (0.8,0.8),
				size = (50,50),
				pos_hint = {"center_x": 0.5}
			)
			btn.bind(on_press=command)
			label.bind(on_press=command)
			for item in [btn, label]:
				fr.add_widget(item)
	
	def main_frames(self):
		self.tengah = self.setup.frame("vertical", spacing=10)
		self.bawah = self.setup.frame("horizontal", padding=30, bg=universal_background, size_hint_y=None, radius=(50,50,0,0), spacing=15)
		self.atas = BoxLayout(
			orientation="horizontal",
			size_hint_y=None,
			padding=20
		)
		self.table.add_background_image(self.atas, "Pictures/header-wallpaper.png", radius=(0,0,50,50))
		self.bawah.height = 180
		self.atas.height = 180
		
		for x in [self.atas, self.tengah, self.bawah]:
			self.main_layout.add_widget(x)
		
if __name__ == "__main__":
	helper = WidgetHelper()
	helper_table = HelperUtama(helper)
	myApp = MainApp(helper, helper_table)
	myApp.run()
	conn.close()