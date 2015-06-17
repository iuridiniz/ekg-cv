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
import numpy as np

from gi.repository import Gtk, GdkPixbuf

def get_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
        filename)
    
# Workaround for bug http://stackoverflow.com/a/28236548/1522342 when using
# gobject introspection and gtk < 3.14
# Shared at: http://stackoverflow.com/a/28236548/1522342
def image2pixbuf(im):
    # get image dimensions
    height, width, depth = (im.shape + (1,))[0:3]
    # P5 and P6 are the magic numbers for PGM and PPM formats, respectively 
    if depth == 3:
        # convert image from BRG to RGB (pnm uses RGB)
        im2 = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        format_ = "P6"
    elif depth == 1:
        # GRAY image, do nothing
        im2 = im
        format_ = "P5"
    else:
        return

    pixl = GdkPixbuf.PixbufLoader.new_with_type('pnm')
    # and 255 is the max color allowed, see http://en.wikipedia.org/wiki/Netpbm_format#File_format_description        
    pixl.write("%s %d %d 255 " % (format_, width, height) + im2.tostring())
    pix = pixl.get_pixbuf()
    pixl.close()
    return pix

def imshow(name, im):
    
    window = Gtk.Window()
    
    window.set_title(name)
    pixbuf = image2pixbuf(im)
    
    container = Gtk.Image()
    
    container.set_from_pixbuf(pixbuf)
    
    window.add(container)

    window.show_all()
    

def isolate_grade(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 100, 100])
    upper_red = np.array([15, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red, upper_red)
    
    #mask2 = np.where(mask_red == 255, 1, 255).astype('uint8')
    res = cv2.bitwise_not(mask_red)
    
    return cv2.cvtColor(res, cv2.COLOR_GRAY2BGR)

def grade_get_distances(im, match_val = 0, max_interactions=-1):
    # assume 
    pos = 0
    height, width, depth = im.shape
    prev = -1
    last_pos = -1
    distances = []
    
    for pos, val in enumerate(im.flatten()):
        if pos % depth != 0:
            # use only the first rgb/bgr value (it's a gray image)
            continue
        #print "%6d: %3d | last_pos: %6d | distances: %s" %(pos, val, last_pos, distances)
        if len(distances) == max_interactions:
            # enough
            break
        if pos % (depth * width) == 0:
            # new line, reset prev
            prev = -1
            last_pos = -1
        if val != prev and val == match_val:
            # if found a new match_val, calculate the distance to previous pos
            if last_pos != -1: # has previous pos?
                diff = pos - last_pos
                distances.append(diff)
            last_pos = pos
        prev = val
    
    return distances

def isolate_ekg(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([255, 255, 100])
    mask_black = cv2.inRange(hsv, lower_black, upper_black)
    
    res = cv2.bitwise_not(mask_black)
    return cv2.cvtColor(res, cv2.COLOR_GRAY2BGR)

class MyBuilderHandler(object):
    GLADE_FILE = "main.glade"
    WIDGETS = None  # Must be a dict or None. TODO: support list
    DEFAULT_WIDGET_PREFIX = "_"
    def __init__(self):
        self._builder = Gtk.Builder()
        
        # Load widgets
        if self.WIDGETS is None:
            # load all objects
            self._builder.add_from_file(get_file(self.GLADE_FILE),)
            self.WIDGETS = dict((Gtk.Buildable.get_name(w), None)
                            for w in self._builder.get_objects())
        
        elif len(self.WIDGETS):
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
        print "Open: args=%s, kwargs=%s" % (args, kwargs)
        if callable(self._openAction):
            self._openAction(dialog=self, filename=self.get_filename())
        else:
            self.hide()
    
    def _onCancel(self, *args, **kwargs):
        print "Cancel: args=%s, kwargs=%s" % (args, kwargs)
        
        if callable(self._cancelAction):
            self._cancelAction(*args, **kwargs)
        else:
            self.hide()
        return True
        
    
class MainWindow(MyBuilderHandler):
    WIDGETS = {"main_window": "_window",
               "ekg_image": "_ekg",
               "filter_grade": "_filter_grade",
               "filter_ekg": "_filter_ekg"}
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self._image = None
        # self._usingwebcam = False
        
    def show(self):
        self._window.show_all()
    
    def hide(self):
        self._window.hide()
        
    def openEkg(self, filename):
        # open using cv2
        self._image = cv2.imread(filename)
        self.updateDisplay()
        
    def updateDisplay(self):
        if not self._image is None:
            
            image = self._image.copy()
            if self._filter_grade.get_active():
                image = isolate_grade(image)
                dist = grade_get_distances(image, max_interactions=-1)
                print "Distances"
                print "size: %d| mean: %d | moda: %d | max: %d | min: %d" %(
                    np.size(dist), np.mean(dist), np.bincount(dist).argmax(),
                    np.max(dist), np.min(dist))
            
            if self._filter_ekg.get_active():
                image = isolate_ekg(image)
            # display on UI
            self._ekg.set_from_pixbuf(image2pixbuf(image))
    
    def openWebcam(self):
        pass
        # TODO: get a working webcam in order to implement
        # if self._usingwebcam:
        #    return
        # cameraCapture = cv2.VideoCapture(0)
        # self._usingwebcam = True
    
    def showOpen(self, cancelAction=None):
        OpenDialog().show(self._onFileSelected, cancelAction)
        
    def _onOpen(self, *args, **kwargs):
        print "Open: args=%s, kwargs=%s" % (args, kwargs)
        OpenDialog().show(self._onFileSelected)
        
    def _onQuit(self, *args, **kwargs):
        print "Quit: args=%s, kwargs=%s" % (args, kwargs)
        self.hide()
        Gtk.main_quit()
        return True
        
    def _onWebcam(self, *args, **kwargs):
        print "Webcam: args=%s kwargs=%s" % (args, kwargs)
        self.openWebcam()
        
    def _onFileSelected(self, *args, **kwargs):
        print "FileSelected: args=%s, kwargs=%s" % (args, kwargs)
        filename = kwargs.get("filename")
        dialog = kwargs.get("dialog")
        if dialog:
            dialog.hide()
        if filename:
            self.openEkg(filename)
            
    
    def _onFilterEkgToggled(self, item):
        self.updateDisplay()
        
    def _onFilterGradeToggled(self, item):
        self.updateDisplay()

if __name__ == '__main__':
    window = MainWindow()
    
    if len(sys.argv) > 1:
        window.openEkg(sys.argv[1])
    else:
        window.showOpen(Gtk.main_quit)
    window.show()
    
    Gtk.main()
