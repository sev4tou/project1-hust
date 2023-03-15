import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import cairo
import vector_store
from logic_frame import LogicFrame
import exception
from exception import CodeNgu
import hotkey
from hotkey import HotkeyManager
import ocr
from ocr import Test
import os

langs = ['eng', 'vie', 'chi_sim']

class Board(object):
    def __init__(self, drawArea: Gtk.Widget):
        self.logic = LogicFrame(None, None)
        self.window = drawArea

        drawArea.connect("draw", self.onDraw)
        drawArea.set_events(
                Gdk.EventMask.BUTTON_PRESS_MASK
                |Gdk.EventMask.POINTER_MOTION_MASK
                |Gdk.EventMask.BUTTON1_MOTION_MASK
                |Gdk.EventMask.BUTTON_RELEASE_MASK
                |Gdk.EventMask.STRUCTURE_MASK
                |Gdk.EventMask.KEY_PRESS_MASK
                |Gdk.EventMask.KEY_RELEASE_MASK)
        drawArea.connect("button-press-event", self.onClick)
        drawArea.connect("button-release-event", self.onUnClick)
        drawArea.connect("motion-notify-event", self.onMove)
        drawArea.connect("configure-event", self.onConfig)
        self.dx, self.dy = None, None

    def onScale(self, widget : Gtk.Scale, data : Gtk.Adjustment):
        self.logic.setZoom(data.get_value())
        self.window.queue_draw()

    def onConfig(self, widget, event : Gdk.EventConfigure):
        self.logic.setWidthHeight(event.width, event.height)

    def onMove(self, widget, event : Gdk.EventMotion):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if self.dx != None and self.dy != None:
                self.logic.move(self.dx-event.x, self.dy-event.y)
            self.window.queue_draw()
            self.dx, self.dy = event.x, event.y
            return

        self.dx, self.dy = event.x, event.y
        if event.state & Gdk.ModifierType.BUTTON1_MASK:
            self.logic.addPoint(event.x, event.y)
            self.window.queue_draw()

    def onUnClick(self, widget, event : Gdk.EventButton):
        if event.button == 1:
            self.logic.endSegment()

    def onClick(self, widget, event):
        if event.button == 1 and event.type == 4:
            self.logic.beginSegment(event.x, event.y)

    def onDraw(self, area, context : cairo.Context):
        if self.logic.surface != None:
            context.set_source_surface(self.logic.surface)
            context.paint()

    def onUndo(self):
        self.logic.undo()
        self.window.queue_draw()

    def onRedo(self):
        self.logic.redo()
        self.window.queue_draw()

class Main(object):
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file('ui.glade')
        self.topWindow = builder.get_object("top")
        self.topWindow.connect("destroy", Gtk.main_quit, None)
        self.board = Board(builder.get_object("board"))
        self.textWindow = builder.get_object("translate")
        self.text = builder.get_object("text")
        self.zoomWidget = builder.get_object("optZoom")
        self.zoomValue = builder.get_object("zoom")
        self.lang = builder.get_object("optLang")
        self.fontButton = builder.get_object("optFont")
        self.fontButton.connect('font-set', self.onFontChange)
        self.zoomWidget.connect("value-changed", self.board.onScale, self.zoomValue)
        self.topWindow.show_all()
        self.tabs = builder.get_object("tabs")
        self.tabs.connect("changed", self.onTabChange)

        builder.get_object("menuQuit").connect("activate", Gtk.main_quit)
        builder.get_object("menuNew").connect("activate", self.onNew)
        builder.get_object("menuOpen").connect("activate", self.onOpen)
        builder.get_object("menuSave").connect("activate", self.onSave)
        builder.get_object("menuSaveAs").connect("activate", self.onSaveAs)
        
        self.hotkey = HotkeyManager(self.topWindow)
        self.hotkey.registerHook(Gdk.KEY_z, Gdk.ModifierType.CONTROL_MASK, self.board.onUndo)
        self.hotkey.registerHook(Gdk.KEY_Z, Gdk.ModifierType.SHIFT_MASK|Gdk.ModifierType.CONTROL_MASK, self.board.onRedo)
        self.hotkey.registerHook(Gdk.KEY_p, Gdk.ModifierType.CONTROL_MASK, self.toText)
        self.hotkey.registerHook(Gdk.KEY_n, Gdk.ModifierType.CONTROL_MASK, self.onNew)
        self.hotkey.registerHook(Gdk.KEY_s, Gdk.ModifierType.CONTROL_MASK, self.onSave)
        self.hotkey.registerHook(Gdk.KEY_S, Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK, self.onSaveAs)
        self.hotkey.registerHook(Gdk.KEY_o, Gdk.ModifierType.CONTROL_MASK, self.onOpen)

        self.syncTabs()
        self.tabs.set_active_id("0")

    def _createConfirmDialog(message):
        dialog=Gtk.Dialog("File not on the disk! Save the file ?", self.topWindow,
                          (Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
                           Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.topWindow.add_filters(dialog)
        return dialog.run()

    def onSaveAs(self, widget = None):
        dialog=Gtk.FileChooserDialog(
                title = "Please choose a file", 
                parent = self.topWindow,
                action = Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        response=dialog.run()
        if response==Gtk.ResponseType.OK:
            fullpath = dialog.get_filename()
            dialog.destroy()
            path, name = os.path.split(fullpath)
            idd = self.tabs.get_active_id()
            if type(idd) == str:
                idd = int(idd)
                store = self.board.logic.manager.list[idd]
                store.saveAs(name, path)
        else:
            dialog.destroy()
        self.syncTabs()

    def onSave(self, widget = None):
        idd = self.tabs.get_active_id()
        if type(idd) == str:
            idd = int(idd)
            store = self.board.logic.manager.list[idd]
            res = store.check()
            if res == "Ok":
                store._save()
            elif res == "Deleted":
                if self._createConfirmDialog("File Deleted Since Last Save! Overwrite ?")==Gtk.ResponseType.OK:
                    res._save()
            elif res == "Changed":
                if self._createConfirmDialog("File Changed Since Last Save! Overwrite ?")==Gtk.ResponseType.OK:
                    res._save()
            elif res == "Temp":
                self.onSaveAs()
            else:
                raise BadCode

    def onOpen(self, widget = None):
        dialog=Gtk.FileChooserDialog(
                title = "Please choose a file", 
                parent = self.topWindow,
                action = Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        response=dialog.run()
        if response==Gtk.ResponseType.OK:
            fullpath = dialog.get_filename()
            dialog.destroy()
            path, name = os.path.split(fullpath)
            idd = self.board.logic.openStore(name, path)
            self.syncTabs()
            self.tabs.set_active_id(str(idd))
            self.onTabChange(self.tabs)
        else:
            dialog.destroy()
        
        
    def toText(self):
        surface = self.board.logic.surface
        idd = self.lang.get_active_id()
        if idd != None:
            idd = 0
        lang = langs[int(idd)]
        res = Test.testImg(surface.get_data(), surface.get_width(), surface.get_height(), lang)
        if res == None:
            res = '(null)'
        elif res.isspace():
            res = '(space)'
        print("debug", res)
        self.text.set_text(res)
        self.textWindow.queue_draw()

    def onFontChange(self, widget):
        font_description = self.fontButton.get_font_desc()
        self.textWindow.override_font(font_description)

    def syncTabs(self):
        self.tabs.remove_all()
        for i,v in enumerate(self.board.logic.manager.list):
            self.tabs.append(str(i), v.fileName)

    def onTabChange(self, widget):
        idd = self.tabs.get_active_id()
        if type(idd) == str:
            self.board.logic.switch(int(idd))
            self.board.window.queue_draw()

    def onNew(self, widget = None):
        idd = self.board.logic.newStore()
        self.syncTabs()
        self.tabs.set_active_id(str(idd))
        self.onTabChange(self.tabs)

main = Main()
Gtk.main();
