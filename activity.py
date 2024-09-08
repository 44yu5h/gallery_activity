import gi
import os
import glob
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
gi.require_version('Gtk', '3.0')
gi.require_version('Rsvg', '2.0')


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
        self.max_participants = 1

        self.current_index = 0
        self.media_files = []

        #=================== Toolbar UI ===================
        self.toolbar_box = ToolbarBox()
        activity_button = ActivityToolbarButton(self)
        self.toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        # next button
        self.prev_btn = self.create_toolbar_btn('prev', 'Previous File',
                                                self.prev_cb)
        self.next_btn = self.create_toolbar_btn('next', 'Next File',
                                                self.next_cb)
        self.delete_btn = self.create_toolbar_btn('delete', 'Delete File',
                                                  self.delete_cb)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self.toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        self.toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(self.toolbar_box)
        self.show_all()

        self.set_canvas(self.HomeScreen())
        self.home_screen.connect("size-allocate", self.get_pic_size)
        self.load_media()
        GLib.timeout_add(150, self.update_display)

    #===================== Misc fns. =====================
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

    def next_cb(self, button):
        if self.current_index < len(self.media_files) - 1:
            self.current_index += 1
            self.update_display()

    def prev_cb(self, button):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def delete_cb(self, button):
        print('Delete')

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
            ('png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'
             ))]
        self.media_files.sort(key=os.path.getmtime, reverse=True)

    def update_display(self):
        for child in self.rounded_pic.get_children():
            self.rounded_pic.remove(child)

        if self.media_files:
            media_file = self.media_files[self.current_index]

            # image
            if media_file.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    media_file, self.pic_width, self.pic_height)
                self.rounded_pic.set_size_request(pixbuf.get_width(),
                                                  pixbuf.get_height())
                rounded_img = RoundedImage(pixbuf)
                self.rounded_pic.pack_start(rounded_img, True, True, 0)

            # video
            elif media_file.lower().endswith(('mp4', 'avi', 'mov')):
                video_label = Gtk.Label(label="Video: "
                                        + os.path.basename(media_file))
                self.rounded_pic.pack_start(video_label, True, True, 0)

        self.rounded_pic.show_all()

    #=================== Home Screen UI ====================
    def HomeScreen(self):
        self.home_screen = Gtk.ScrolledWindow()
        self.white_bg = Gtk.Box()
        self.rounded_pic = Gtk.Box()
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
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        return self.home_screen
