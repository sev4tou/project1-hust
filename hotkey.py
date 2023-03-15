import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import exception
from exception import CodeNgu
 
class HotkeyManager(object):
    def __init__(self, win: Gtk.Window):
        win.add_events(Gdk.EventMask.KEY_PRESS_MASK|Gdk.EventMask.KEY_RELEASE_MASK)
        win.connect("key-press-event", self._onKeyPress)
        win.connect("key-release-event", self._onKeyRelease)
        self.mp = dict()
        self.mpr = dict()
        self.mods = Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK

    def registerHook(self, key, mod, hook, press=True):
        if mod & (~self.mods):
            raise CodeNgu
        if press:
            if (key, mod) in self.mp:
                raise CodeNgu
            self.mp[(key,mod)] = hook
        else:
            if (key, mod) in self.mpr:
                raise CodeNgu
            self.mpr[(key,mod)] = hook
         
    def _onKeyPress(self, widget, event : Gdk.EventKey):
        k = event.keyval
        m = event.state & self.mods
        if (k,m) in self.mp:
            self.mp[(k,m)]()

    def _onKeyRelease(self, widget, event : Gdk.EventKey):  
        k = event.keyval
        m = event.state & self.mods
        if (k,m) in self.mpr:
            self.mpr[(k,m)]()          
