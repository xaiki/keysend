#!/usr/bin/env python

from gi.repository import Gtk

b = Gtk.Builder()
b.add_from_file ('ks.ui')

w = b.get_object ('window1')
w.show_all()
w.connect ('destroy', lambda w: Gtk.main_quit())

Gtk.main()
