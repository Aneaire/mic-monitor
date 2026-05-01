#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess

loopback_pid = None
volume = 2.0  # default boost (200%)

def toggle_mic(button):
    global loopback_pid
    if loopback_pid is None:
        proc = subprocess.Popen(
            ['pw-loopback', '-m', '[ FL FR ]',
             '--capture-props=media.class=Audio/Source',
             f'--playback-props=node.volume={volume}'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        loopback_pid = proc.pid
        button.set_label("🎤 Mic ON")
        button.get_style_context().add_class("on")
        button.get_style_context().remove_class("off")
    else:
        subprocess.run(['kill', str(loopback_pid)])
        loopback_pid = None
        button.set_label("🎤 Mic OFF")
        button.get_style_context().add_class("off")
        button.get_style_context().remove_class("on")

def on_volume_change(slider):
    global volume, loopback_pid
    volume = slider.get_value()
    if loopback_pid:
        subprocess.run(['kill', str(loopback_pid)])
        loopback_pid = None
        proc = subprocess.Popen(
            ['pw-loopback', '-m', '[ FL FR ]',
             '--capture-props=media.class=Audio/Source',
             f'--playback-props=node.volume={volume}'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        loopback_pid = proc.pid

def on_destroy(win):
    global loopback_pid
    if loopback_pid:
        subprocess.run(['kill', str(loopback_pid)])
    Gtk.main_quit()

css = b"""
button.on {
    background: #2ecc71;
    color: white;
    font-weight: bold;
    font-size: 14px;
    border-radius: 8px;
    padding: 8px 16px;
}
button.off {
    background: #e74c3c;
    color: white;
    font-weight: bold;
    font-size: 14px;
    border-radius: 8px;
    padding: 8px 16px;
}
window {
    background: #1a1a2e;
}
scale trough {
    background: #333;
}
"""

provider = Gtk.CssProvider()
provider.load_from_data(css)
Gtk.StyleContext.add_provider_for_screen(
    __import__('gi.repository', fromlist=['Gdk']).Gdk.Screen.get_default(),
    provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

win = Gtk.Window(title="Mic Monitor")
win.set_default_size(220, 100)
win.set_resizable(False)
win.set_keep_above(True)
win.connect("destroy", on_destroy)

box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
box.set_margin_top(8)
box.set_margin_bottom(8)
box.set_margin_start(10)
box.set_margin_end(10)

btn = Gtk.Button(label="🎤 Mic OFF")
btn.get_style_context().add_class("off")
btn.connect("clicked", toggle_mic)

slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 5.0, 0.5)
slider.set_value(volume)
slider.set_draw_value(False)
slider.set_tooltip_text("Volume boost")
slider.connect("value-changed", on_volume_change)

box.pack_start(btn, True, True, 0)
box.pack_start(slider, False, False, 0)

win.add(box)
win.show_all()
Gtk.main()
