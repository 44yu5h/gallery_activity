import gi

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton

from gi.repository import Gtk, Gdk, GdkPixbuf
gi.require_version('Gtk', '3.0')
gi.require_version('Rsvg', '2.0')


class GalleryActivity(activity.Activity):

    #==========================================================================
    #SECTION                           INIT
    #==========================================================================
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self.max_participants = 1

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
        canvas = self.get_canvas()
        bg_color = Gdk.RGBA()
        bg_color.parse("#F1F1F1")
        canvas.override_background_color(Gtk.StateType.NORMAL, bg_color)

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
        print('Next')

    def prev_cb(self, button):
        print('Previous')

    def delete_cb(self, button):
        print('Delete')

    def HomeScreen(self):
        # Create the home screen
        home_screen = Gtk.Grid()
        home_screen.set_column_spacing(10)
        home_screen.set_row_spacing(10)
        home_screen.set_margin_top(10)
        home_screen.set_margin_bottom(10)
        home_screen.set_margin_start(10)
        home_screen.set_margin_end(10)
        home_screen.set_row_homogeneous(True)
        home_screen.set_column_homogeneous(True)

        # Create the camera preview
        self.camera_preview = Gtk.Image()
        self.camera_preview.set_size_request(640, 480)
        home_screen.attach(self.camera_preview, 0, 0, 1, 1)

        return home_screen
