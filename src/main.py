'''
Created on 28/01/2015

@author: iuri
'''
from gi.repository import Gtk
import os
import sys

def get_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 
        filename)

class MyBuilderHandler(object):
    GLADE_FILE = "main.glade"
    WIDGETS = {}
    DEFAULT_WIDGET_PREFIX = "_" 
    def __init__(self):
        self._builder = Gtk.Builder()
        if len(self.WIDGETS):
            self._builder.add_objects_from_file(get_file(self.GLADE_FILE), 
                                                self.WIDGETS.keys())

        for from_name, to_name in self.WIDGETS.iteritems():
            attr_name = to_name if to_name else self.DEFAULT_WIDGET_PREFIX + from_name
            if (hasattr(self, attr_name)):
                # TODO: raise exception
                pass
            widget = self._builder.get_object(from_name)
            if widget: 
                setattr(self, attr_name, widget)
            else:
                # TODO: raise exception
                pass
            
        self._builder.connect_signals(self)

class OpenDialog(MyBuilderHandler):
    WIDGETS = {"opendialog": "dialog"}
    
    def show(self, openAction=None, cancelAction=None):
        self._openAction = openAction
        self._cancelAction = cancelAction
        self.dialog.show_all()
        
    def hide(self):
        self.dialog.hide()
    
    def get_filename(self):
        return self.dialog.get_filename()
        
    def _onOpen(self, *args, **kwargs):
        print "Open: args=%s, kwargs=%s" %(args, kwargs)
        if callable(self._openAction):
            self._openAction(dialog=self, filename=self.get_filename())
        else:
            self.hide()
    
    
    def _onCancel(self, *args, **kwargs):
        print "Cancel: args=%s, kwargs=%s" %(args, kwargs)
        
        if callable(self._cancelAction):
            self._cancelAction(*args, **kwargs)
        else:
            self.hide()
        return True
        
    
class MainWindow(MyBuilderHandler):
    WIDGETS = {"main_window": "_window", 
               "ekg_image": "_ekg"}
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
    def show(self):
        self._window.show_all()
        
    def show_open(self, cancelAction=None):
        OpenDialog().show(self._onFileSelected, cancelAction)
        
    def _onOpen(self, *args, **kwargs):
        print "Open: args=%s, kwargs=%s" %(args, kwargs)
        OpenDialog().show(self._onFileSelected)
        
    def _onQuit(self, *args, **kwargs):
        print "Quit: args=%s, kwargs=%s" %(args, kwargs)
        Gtk.main_quit()
        
    def openEkg(self, filename):
        self._ekg.set_from_file(filename)
    
    def _onFileSelected(self, *args, **kwargs):
        print "FileSelected: args=%s, kwargs=%s" %(args, kwargs)
        filename = kwargs.get("filename")
        dialog = kwargs.get("dialog")
        if dialog:
            dialog.hide()
        if filename:
            self.openEkg(filename)
            

if __name__ == '__main__':
    window = MainWindow()
    
    if len(sys.argv) > 1:
        window.openEkg(sys.argv[1])
    else:
        window.show_open(Gtk.main_quit)
    window.show()
    
    Gtk.main()

    