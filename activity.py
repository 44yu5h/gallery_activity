import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Rsvg', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gst
import os
import glob
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton


class RoundedImage(Gtk.DrawingArea):
    def __init__(self, pixbuf, radius=15):
        super().__init__()
        self.pixbuf = pixbuf
        self.radius = radius
        self.connect("draw", self.do_draw)

    def do_draw(self, widget, cr=None):
        if cr is None:
            return
        width = self.pixbuf.get_width()
        height = self.pixbuf.get_height()

        # rounded corners
        cr.move_to(self.radius, 0)
        cr.line_to(width - self.radius, 0)
        cr.arc(width - self.radius, self.radius, self.radius, -0.5 * 3.14, 0)
        cr.line_to(width, height - self.radius)
        cr.arc(width - self.radius,
               height - self.radius,
               self.radius,
               0, 0.5 * 3.14)
        cr.line_to(self.radius, height)
        cr.arc(self.radius,
               height - self.radius,
               self.radius,
               0.5 * 3.14, 3.14)
        cr.line_to(0, self.radius)
        cr.arc(self.radius, self.radius, self.radius, 3.14, 1.5 * 3.14)
        cr.close_path()
        cr.clip()

        # paint
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.paint()


class GalleryActivity(activity.Activity):

    #==========================================================================
    #SECTION                           INIT
    #==========================================================================
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        Gst.init(None)
        self.player = Gst.ElementFactory.make("playbin", "player")
        self.is_playing = False
        self.max_participants = 1

        self.current_index = 0
        self.media_files = []

        #=================== Toolbar UI ===================
        self.toolbar_box = ToolbarBox()
        activity_button = ActivityToolbarButton(self)
        self.toolbar_box.padding = 30
        self.toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        def space_widget():
            space1 = Gtk.Box()
            space1.set_size_request(20, -1)
            space1_tool_item = Gtk.ToolItem()
            space1_tool_item.add(space1)
            self.toolbar_box.toolbar.insert(space1_tool_item, -1)
            space1.show()
            space1_tool_item.show()
            return space1_tool_item

        space_widget()

        self.prev_btn = self.create_toolbar_btn('prev', 'Previous File',
                                                self.prev_cb)
        self.next_btn = self.create_toolbar_btn('next', 'Next File',
                                                self.next_cb)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self.toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        self.delete_btn = self.create_toolbar_btn('delete', 'Delete File',
                                                  self.delete_cb)
        space_widget()

        stop_button = StopButton(self)
        self.toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(self.toolbar_box)
        self.show_all()

        self.set_canvas(self.HomeScreen())
        self.home_screen.connect("size-allocate", self.get_pic_size)
        self.load_media()
        GLib.timeout_add(150, self.update_display)

        self.connect("key-press-event", self.on_key_press)

    #================ Keyboard Shortcuts =================
    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Right or event.keyval == Gdk.KEY_Up:
            self.next_cb()
        elif event.keyval == Gdk.KEY_Left or event.keyval == Gdk.KEY_Down:
            self.prev_cb()
        elif event.keyval == Gdk.KEY_Delete:
            self.delete_cb()
        elif event.keyval == Gdk.KEY_p:
            if not self.is_an_image:
                self.play_video()

    #===================== Set up buttons =====================
    def create_toolbar_btn(self, icon, tooltip, callback):
        button = Gtk.ToggleButton()
        button.set_image(self._icon(icon))
        button.set_tooltip_text(tooltip)
        button.connect('toggled', callback)
        tool_item = Gtk.ToolItem()
        tool_item.add(button)
        self.toolbar_box.toolbar.insert(tool_item, -1)
        return button

    def _icon(self, icon_name):
        icon = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            'icons/' + icon_name + '.svg', 50, 50, True)
        icon.set_from_pixbuf(pixbuf)
        return icon

    def next_cb(self, *a):
        if self.current_index < len(self.media_files) - 1:
            self.current_index += 1
            self.update_display()

    def prev_cb(self, *a):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def delete_cb(self, *a):
        if self.media_files:
            media_file = self.media_files[self.current_index]
            print(media_file)
            try:
                # move to trash instead of permanently deleting
                os.system('gio trash "' + media_file + '"')
                del self.media_files[self.current_index]
                self.update_display()
            except Exception as e:
                print(f"Error deleting file {media_file}: {e}")
        #TODO - popup dialog for confirmation

    #===================== Misc. fns. =====================
    def get_pic_size(self, *a):
        HS_width = self.home_screen.get_allocated_width()
        HS_height = self.home_screen.get_allocated_height()
        self.pic_height = HS_height - 120
        self.pic_width = HS_width - 120

    def load_media(self):
        media_dir = os.path.expanduser('~/Pictures')
        self.media_files = glob.glob(os.path.join(media_dir, '**', '*'),
                                     recursive=True)
        self.media_files = [f for f in self.media_files if f.lower().endswith(
            ('png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'webm'
             ))]
        self.media_files.sort(key=os.path.getmtime, reverse=True)

    #===================== Update current media =====================
    def update_display(self):
        for child in self.rounded_pic.get_children():
            self.rounded_pic.remove(child)
            self.flush_player()

        if self.media_files:
            media_file = self.media_files[self.current_index]

            # image
            if media_file.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                self.is_an_image = True
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    media_file, self.pic_width, self.pic_height)
                self.rounded_pic.set_size_request(pixbuf.get_width(),
                                                  pixbuf.get_height())
                rounded_img = RoundedImage(pixbuf)
                self.rounded_pic.pack_start(rounded_img, True, True, 0)

            # Video
            elif media_file.lower().endswith(('mp4', 'avi', 'mov', 'webm')):
                self.is_an_image = False

                self.player.set_property("uri", f"file://{media_file}")
                video_sink = Gst.ElementFactory.make("gtksink", "video_sink")
                self.player.set_property("video-sink", video_sink)
                video_widget = video_sink.props.widget
                self.rounded_pic.set_size_request(self.pic_width,
                                                  self.pic_height)
                self.rounded_pic.pack_start(video_widget, True, True, 0)

                self.progress_bar = Gtk.Scale(
                    orientation=Gtk.Orientation.HORIZONTAL)
                self.progress_bar.set_range(0, 100)
                self.progress_bar.set_draw_value(False)
                self.rounded_pic.pack_start(self.progress_bar, False, False, 0)

            self.rounded_pic.show_all()

    #=============== Extra fns for vid playback =================
    def play_video(self):
        if self.is_playing:
            self.player.set_state(Gst.State.PAUSED)
        else:
            if self.progress_bar.get_value() == 0:
                self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH |
                                        Gst.SeekFlags.KEY_UNIT, 0)
                self.player.set_state(Gst.State.PLAYING)
            else:
                self.player.set_state(Gst.State.PLAYING)
            GLib.timeout_add(50, self.update_progress_bar)
        self.is_playing = not self.is_playing

    def update_progress_bar(self):
        if self.is_playing:
            success, duration = self.player.query_duration(Gst.Format.TIME)
            success, position = self.player.query_position(Gst.Format.TIME)
            if success and duration > 0:
                self.duration = duration
                value = position / duration * 100
                self.progress_bar.set_value(value)
                if position + 10000000 >= duration:
                    print("Video reached the end")
                    self.flush_player()
                    return False
            else:
                self.progress_bar.set_value(0)
                return False
        return True

    def on_seek(self, scale):
        seek_time = int(scale.get_value() / 100 * self.duration)
        print(f"Seeking to: {seek_time}")
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH |
                                Gst.SeekFlags.KEY_UNIT, seek_time)

    def flush_player(self):
        self.player.set_state(Gst.State.NULL)
        self.is_playing = False
        self.progress_bar.set_value(0)
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH |
                                Gst.SeekFlags.KEY_UNIT, 0)

    #=================== Home Screen UI ====================
    def HomeScreen(self):
        self.home_screen = Gtk.ScrolledWindow()
        self.white_bg = Gtk.Box()
        self.rounded_pic = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.white_bg.get_style_context().add_class('white-bg')
        self.home_screen.get_style_context().add_class('home-screen')
        self.white_bg.pack_start(self.rounded_pic, True, True, 0)
        self.rounded_pic.set_halign(Gtk.Align.CENTER)
        self.rounded_pic.set_valign(Gtk.Align.CENTER)
        self.home_screen.add(self.white_bg)
        self.home_screen.show_all()

        css = """
        .white-bg {
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(0, 0, 0, 0.1);
            padding: 20px;
            background-color: white;
        }
        .home-screen {
            background-color: #1C1C1C;
            padding: 20px;
        }
        button {
            background: none;
            border: none;
            box-shadow: none;
        }
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        return self.home_screen
