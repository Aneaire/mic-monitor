#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess

module_id = None
echo_cancel_id = None
SOURCE = "alsa_input.usb-MaiYueTech_K18_202505241106-00.analog-stereo"
SINK = "alsa_output.pci-0000_06_00.6.analog-stereo"

# Clean up any leftover loopback/echo modules on startup
def cleanup_existing_loopbacks():
    result = subprocess.run(['pactl', 'list', 'modules', 'short'], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if 'module-loopback' in line or 'module-echo-cancel' in line:
            mod_id = line.split()[0]
            subprocess.run(['pactl', 'unload-module', mod_id])

cleanup_existing_loopbacks()

def get_echo_cancelled_source():
    global echo_cancel_id
    result = subprocess.run(
        ['pactl', 'load-module', 'module-echo-cancel',
         f'source_master={SOURCE}',
         f'sink_master={SINK}',
         'aec_method=webrtc',
         'source_name=ec_source'],
        capture_output=True, text=True
    )
    echo_cancel_id = result.stdout.strip() or None
    return "ec_source" if echo_cancel_id else SOURCE

def load_loopback(volume):
    source = get_echo_cancelled_source()
    result = subprocess.run(
        ['pactl', 'load-module', 'module-loopback',
         f'source={source}',
         f'sink={SINK}',
         'latency_msec=50',
         'source_dont_move=true',
         'sink_dont_move=true'],
        capture_output=True, text=True
    )
    mod_id = result.stdout.strip()
    if mod_id:
        set_loopback_volume(mod_id, volume)
    return mod_id or None

def set_loopback_volume(mod_id, volume):
    result = subprocess.run(
        ['pactl', 'list', 'sink-inputs', 'short'],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        parts = line.split()
        if parts:
            sink_input_id = parts[0]
            subprocess.run(
                ['pactl', 'set-sink-input-volume', sink_input_id, f'{int(volume * 100)}%'],
                capture_output=True
            )

def toggle_mic(button):
    global module_id
    if module_id is None:
        volume = slider.get_value()
        module_id = load_loopback(volume)
        if module_id:
            button.set_label("🎤 Mic ON")
            button.get_style_context().add_class("on")
            button.get_style_context().remove_class("off")
    else:
        subprocess.run(['pactl', 'unload-module', module_id])
        if echo_cancel_id:
            subprocess.run(['pactl', 'unload-module', echo_cancel_id])
        module_id = None
        button.set_label("🎤 Mic OFF")
        button.get_style_context().add_class("off")
        button.get_style_context().remove_class("on")

def on_volume_change(s):
    global module_id
    if module_id:
        set_loopback_volume(module_id, s.get_value())

def on_destroy(win):
    global module_id, echo_cancel_id
    if module_id:
        subprocess.run(['pactl', 'unload-module', module_id])
    if echo_cancel_id:
        subprocess.run(['pactl', 'unload-module', echo_cancel_id])
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

slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50, 200, 10)
slider.set_value(100)
slider.set_draw_value(False)
slider.set_tooltip_text("Volume")
slider.connect("value-changed", on_volume_change)

box.pack_start(btn, True, True, 0)
box.pack_start(slider, False, False, 0)

win.add(box)
win.show_all()
Gtk.main()
