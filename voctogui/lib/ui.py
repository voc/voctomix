#!/usr/bin/python3
import gi, logging
from gi.repository import Gtk, Gst, Gdk, GLib

from lib.config import Config
from lib.uibuilder import UiBuilder
from lib.videodisplay import VideoDisplay

class Ui(UiBuilder):
	def __init__(self, uifile):
		self.log = logging.getLogger('Ui')
		super().__init__(uifile)

	def setup(self):
		self.log.info('Initializing Ui')

		# Aquire the Main-Window from the UI-File
		self.win = self.get_check_widget('window')

		# Connect Close-Handler
		self.win.connect('delete-event', Gtk.main_quit)

		self.previews = {}
		self.preview_players = {}


		self.configure_toolbar_accelerators()
		self.configure_video_main()
		self.configure_video_previews()
		self.configure_audio_selector()
		self.configure_streamblank_selector()

	def configure_toolbar_accelerators(self):
		accelerators = Gtk.AccelGroup()
		self.win.add_accel_group(accelerators)

		composites = [
			'composite-fullscreen',
			'composite-picture-in-picture',
			'composite-side-by-side-equal',
			'composite-side-by-side-preview'
		]

		for idx, name in enumerate(composites):
			key, mod = Gtk.accelerator_parse('F%u' % (idx+1))
			btn = self.find_widget_recursive(self.win, name)
			btn.set_name(name)

			# Thanks to http://stackoverflow.com/a/19739855/1659732
			btn.get_child().add_accelerator('clicked', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
			btn.connect('toggled', self.composite_btn_toggled)

	def composite_btn_toggled(self, btn):
		if not btn.get_active():
			return

		self.log.info("composite_btn_toggled: %s", btn.get_name())

	def configure_video_main(self):
		self.log.info('Initializing Main Video and Main Audio-Level View')

		video = self.find_widget_recursive(self.win, 'video_main')
		audiolevel = self.find_widget_recursive(self.win, 'audiolevel_main')
		self.video_main_player = VideoDisplay(11000, video, audiolevel,
			playaudio=Config.getboolean('mainvideo', 'playaudio'),
			allowoverlay=True)

	def configure_video_previews(self):
		self.log.info('Initializing Video Previews')

		sources = ['cam1', 'cam2', 'grabber']
		box = self.find_widget_recursive(self.win, 'box_left')

		try:
			width = Config.getint('previews', 'width')
			self.log.debug('Preview-Width configured to %u', width)
		except:
			width = 320
			self.log.debug('Preview-Width selected as %u', width)

		try:
			height = Config.getint('previews', 'height')
			self.log.debug('Preview-Height configured to %u', width)
		except:
			height = width*9/16
			self.log.debug('Preview-Height calculated to %u', width)


		# Accelerators
		accelerators = Gtk.AccelGroup()
		self.win.add_accel_group(accelerators)

		group_a = None
		group_b = None

		for idx, source in enumerate(sources):
			self.log.info('Initializing Video Preview %s', source)

			preview = self.get_check_widget('widget_preview', clone=True)
			video = self.find_widget_recursive(preview, 'video')

			video.set_size_request(width, height)
			box.pack_start(preview, fill=False, expand=False, padding=0)

			player = VideoDisplay(13000 + idx, video)

			self.find_widget_recursive(preview, 'label').set_label(source)
			btn_a = self.find_widget_recursive(preview, 'btn_a')
			btn_b = self.find_widget_recursive(preview, 'btn_b')

			btn_a.set_name("%c %u" % ('a', idx))
			btn_b.set_name("%c %u" % ('b', idx))

			if not group_a:
				group_a = btn_a
			else:
				btn_a.join_group(group_a)


			if not group_b:
				group_b = btn_b
			else:
				btn_b.join_group(group_b)

			btn_a.connect('toggled', self.preview_btn_toggled)
			btn_b.connect('toggled', self.preview_btn_toggled)

			key, mod = Gtk.accelerator_parse('%u' % (idx+1))
			btn_a.add_accelerator('activate', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

			key, mod = Gtk.accelerator_parse('<Ctrl>%u' % (idx+1))
			btn_b.add_accelerator('activate', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

			self.preview_players[source] = player
			self.previews[source] = preview

	def preview_btn_toggled(self, btn):
		if not btn.get_active():
			return

		self.log.info('preview_btn_toggled: %s', btn.get_name())

	def configure_audio_selector(self):
		self.log.info('Initializing Audio Selector')

		combo = self.find_widget_recursive(self.win, 'combo_audio')
		combo.set_sensitive(True)

		# FIXME access via combo_audio?
		liststore = self.get_check_widget('liststore_audio')
		liststore.clear()

		row = liststore.append()
		liststore.set(row, [0], ['foobar'])

		row = liststore.append('')
		liststore.set(row, [0], ['moofar'])

		combo.set_active_id('moofar')

	def configure_streamblank_selector(self):
		livebtn = self.get_check_widget('stream_live')
		blankbtn = self.get_check_widget('stream_blank')
		toolbar = blankbtn.get_parent()
		pos = toolbar.get_item_index(blankbtn)

		self.blink_btn = None
		self.blink_btn_state = False

		livebtn.connect('toggled', self.streamblank_button_toggled)
		livebtn.set_name('live')

		GLib.timeout_add_seconds(1, self.blink_streamblank_button)

		for idx, name in enumerate(['pause', 'nostream']):
			if idx == 0:
				new_btn = blankbtn
			else:
				new_icon = Gtk.Image.new_from_pixbuf(blankbtn.get_icon_widget().get_pixbuf())
				new_btn = Gtk.RadioToolButton(group=livebtn)
				new_btn.set_icon_widget(new_icon)
				toolbar.insert(new_btn, pos+1)

			new_btn.set_label("Stream %s" % name)
			new_btn.connect('toggled', self.streamblank_button_toggled)
			new_btn.set_name(name)

	def blink_streamblank_button(self):
		self.blink_btn_state = not self.blink_btn_state
		if self.blink_btn:
			self.blink_btn.get_icon_widget().override_background_color(
				Gtk.StateType.NORMAL,
				Gdk.RGBA(1.0, 0.0, 0.0, 1.0 if self.blink_btn_state else 0.0))

		return True

	def streamblank_button_toggled(self, btn):
		btn.get_icon_widget().override_background_color(
			Gtk.StateType.NORMAL,
			Gdk.RGBA(1.0, 0.0, 0.0, 0.0))

		if not btn.get_active():
			return

		if btn.get_name() != 'live':
			self.blink_btn = btn
			self.blink_btn_state = False
			self.streamblank_mode = btn.get_name()
			self.video_main_player.set_overlay_callback(self.draw_streamblank_warning)
		else:
			self.blink_btn = None
			self.video_main_player.set_overlay_callback(None)

	def draw_streamblank_warning(self, cairooverlay, cairo, timestamp, duration):
		cairo.set_source_rgba(1.0, 0.0, 0.0, 0.5)
		cairo.rectangle(0, 0, 1920, 1080)
		cairo.fill()

		cairo.move_to(0, 1080/2)
		cairo.set_font_size(100)
		cairo.set_source_rgba(1.0, 1.0, 1.0, 1.0)
		cairo.show_text("Stream is Blanked: {}".format(self.streamblank_mode))


	def show(self):
		self.log.info('Running Video-Playback Pipelines')

		self.video_main_player.run()
		for name, player in self.preview_players.items():
			player.run()

		self.log.info('Showing Main-Window')
		self.win.show_all()
