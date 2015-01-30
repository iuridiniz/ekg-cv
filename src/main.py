'''
Created on 28/01/2015

@author: Iuri Gomes Diniz

The MIT License (MIT)

Copyright (c) 2015 Iuri Gomes Diniz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Except as contained in this notice, the name(s) of the above copyright
holders shall not be used in advertising or otherwise to promote the sale,
use or other dealings in this Software without prior written authorization.
'''
import os
import sys

import cv2

from gi.repository import Gtk, GdkPixbuf

def get_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 
        filename)
    
# Workaround for bug http://stackoverflow.com/a/28236548/1522342 when using
# gobject introspection and gtk < 3.14
# Shared at: http://stackoverflow.com/a/28236548/1522342
def image2pixbuf(im):
    # convert image from BRG to RGB (pnm uses RGB)
    im2 = cv2.cvtColor(im, cv2.cv.CV_BGR2RGB)
    # get image dimensions
    height, width = im2.shape[0:2]
    pixl = GdkPixbuf.PixbufLoader.new_with_type('pnm')
    # P6 is the magic number of PNM format,
    # and 255 is the max color allowed, see [2]
    pixl.write("P6 %d %d 255 " % (width, height) + im2.tostring())
    pix = pixl.get_pixbuf()
    pixl.close()
    return pix

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
        
        self._image = None
    def show(self):
        self._window.show_all()
        
    def openEkg(self, filename):
        # open using cv2
        self._image = cv2.imread(filename)
        self.updateDisplay()
        
    def updateDisplay(self):
        if not self._image is None:
            #display on UI
            self._ekg.set_from_pixbuf(image2pixbuf(self._image))
    
    def showOpen(self, cancelAction=None):
        OpenDialog().show(self._onFileSelected, cancelAction)
        
    def _onOpen(self, *args, **kwargs):
        print "Open: args=%s, kwargs=%s" %(args, kwargs)
        OpenDialog().show(self._onFileSelected)
        
    def _onQuit(self, *args, **kwargs):
        print "Quit: args=%s, kwargs=%s" %(args, kwargs)
        Gtk.main_quit()
        
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
        window.showOpen(Gtk.main_quit)
    window.show()
    
    Gtk.main()

    