#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
import gi

import os
from subprocess import Popen, PIPE

DEFAULT_KEY_PATH = '~/.ssh/id_rsa.pub'
DEFAULT_WARN_INSECURE_MESSAGE = 'ESTE MECANISMO ES INSEGURO, SI PUEDE, USE LA TERMINAL'
DEFAULT_READ_SIZE = 1024
DEFAULT_PORT = 5000

class KeySend ():
    def __init__(self):
        self.b = b = Gtk.Builder()

        b.add_from_file ('ks.ui')
#broken        b.connect_signals(None)
        self.b.get_object ('entry_host')   .connect ("changed", self.host_changed_cb)
        self.b.get_object ('button_upload').connect ("clicked", self.upload_clicked_cb)

        self.win   = win   = b.get_object ('window1')
        self.entry = entry = b.get_object ('entry1')
        self.img   = img   = b.get_object ('image_status')
        self.si = None
        self.se = []

        win.show_all()
        win.connect ('destroy', lambda w: Gtk.main_quit())

        self.i = i = Gtk.InfoBar()
        i.set_no_show_all(True)
        self.l = l = Gtk.Label("")
        l.show()

        ca = i.get_content_area()
        ca.add (l)

        i.add_button (Gtk.STOCK_NEW,  Gtk.ResponseType.YES)
        i.connect ("response", self.handle_response_cb)

        i.add_button (Gtk.STOCK_DISCARD, Gtk.ResponseType.CANCEL)
        i.connect ("response", self.handle_response_cb)

        box = b.get_object ('box_info')
        box.add (i)

        entry.connect ("changed", self.entry_changed_cb)
        entry.set_text (DEFAULT_KEY_PATH)

        self.entry_changed_cb (entry)

    def handle_response_cb (self, w, r, d = None):
        if (r == Gtk.ResponseType.YES):
            return self.create_ssh_key()
        if (r == Gtk.ResponseType.CANCEL):
            return w.hide()

        print 'unhandled response:', r

    def host_changed_cb (self, e):
        self.b.get_object ('host_label').set_markup ('<b>' + e.get_text() + '</b>')

    def entry_changed_cb (self, w, d=None):
        p = os.path.expanduser (w.get_text())
        k = self.b.get_object ('key')
        try:
            f = open (p)
        except IOError:
            self.img.set_from_stock (Gtk.STOCK_DIALOG_ERROR, Gtk.IconSize.DIALOG)
            self._show_error ('No pude encontrar ninguna llave valida en ' + w.get_text())
            k.hide()
            return

        self.img.set_from_stock (Gtk.STOCK_APPLY, Gtk.IconSize.DIALOG)
        self.i.hide()
        t = f.read(DEFAULT_READ_SIZE)
        if f.read(DEFAULT_READ_SIZE):
            t += '[…truncated]'
        k.set_text (t)

        k.show()
        try:
            t.index('PRIVATE')
            return self._show_error ('Esto se parece mucho a una llave privada, estas seguro ?')
        except ValueError:
            pass

        if t.startswith ('ssh-dsa'):
            return self._show_error ('Esto se parece mucho a una llave dsa, RSA es mas seguro',
                                     Gtk.MessageType.WARNING)

        if not t.startswith('ssh-rsa'):
            return self._show_error ('Esto no se parece para nada a una llave ssh, estas seguro ?')

    def _show_error (self, msg, t = Gtk.MessageType.ERROR):
        self.l.set_text (msg)
        self.i.set_message_type (t)
        self.i.show()

    def mostrar_clave_cb (self, w):
        self.b.get_object ('entry_ssh_pass').set_visibility (w.get_active())

    def create_ssh_key (self):
        w = self.b.get_object ('window_keygen')

        #buggy, ugly, but signals don't autoconnect…
        self.b.get_object ('checkbutton1')      .connect ("toggled", self.mostrar_clave_cb)
        self.b.get_object ('button_ssh_ok')     .connect ("clicked", self.do_gen_key, w)
        self.b.get_object ('button_ssh_cancel') .connect ("clicked", lambda b: w.hide())
        self.b.get_object ('entry_ssh_pass')    .connect ("changed", self.pass_changed_cb)
        self.b.get_object ('entry_ssh_key_path').connect ("changed", self.key_path_changed_cb)

        if self.si == None:
            self.si = Gtk.InfoBar()
            self.si.set_no_show_all(True)
            self.sl = Gtk.Label("")
            self.sl.show()

            ca = self.si.get_content_area()
            ca.add (self.sl)

            box = self.b.get_object ('box_sinfo')
            box.add (self.si)

            self.show_default_error_msg()

            e = self.b.get_object ('entry_ssh_key_path')
        e.set_text (self.entry.get_text().rstrip('.pub'))
        w.show_all()

    def show_default_error_msg (self):
        self._show_serror (DEFAULT_WARN_INSECURE_MESSAGE,
                           Gtk.MessageType.INFO)


    def is_pass_ok (self, e):
        l = e.get_text().__len__()
        return l == 0 or l > 8

    def is_path_ok (self, e):
        p = os.path.expanduser (e.get_text())
        try:
            os.stat (p)
        except OSError:
            return True
        return False

    def key_path_changed_cb (self, e):
        if (self.is_path_ok (e)):
            pe = self.b.get_object ('entry_ssh_pass')
            if (not self.is_pass_ok (pe)):
                return self.pass_changed_cb (pe)
            return self.show_default_error_msg ()

        self._show_serror ('El archivo:' + e.get_text() + ' ya existe',
                           Gtk.MessageType.ERROR)

    def pass_changed_cb (self, e):
        l = e.get_text().__len__()
        if l == 0:
            return
        if l < 4:
            self._show_serror ('La clave tiene que ser mas larga que 4', Gtk.MessageType.ERROR)
            return
        if l < 8:
            self._show_serror ('Es recomendable que la clave sea mas larga que 8')
            return

        pe = self.b.get_object ('entry_ssh_key_path')
        if (not self.is_path_ok (pe)):
            return self.key_path_changed_cb (pe)

        self.show_default_error_msg()

    def _show_serror (self, msg, t = Gtk.MessageType.WARNING):
        if msg != DEFAULT_WARN_INSECURE_MESSAGE:
            self.b.get_object ('button_ssh_ok').set_sensitive (False)
        else:
            self.b.get_object ('button_ssh_ok').set_sensitive (True)
        self.sl.set_text (msg)
        self.si.set_message_type (t)
        self.si.show()

    def do_gen_key (self, b, w):
        p = self.b.get_object ('entry_ssh_pass').get_text()
        d = os.path.expanduser( self.b.get_object ('entry_ssh_key_path').get_text())
        cmd = "running:", "ssh-keygen -q -N '" + p + "' -f '" + d + "'"
        print cmd

        p = Popen(['ssh-keygen', '-q', '-N', p, '-f', d], stdin=PIPE, stdout=PIPE, stderr=PIPE)

        p.stdin.close()
        if p.wait() != 0:
            return self._show_serror (p.stderr.read(DEFAULT_READ_SIZE), Gtk.MessageType.ERROR)

        w = self.b.get_object ('window_keygen')
        w.hide()
        self.entry_changed_cb (self.entry)

    def upload_clicked_cb (self, w):
        self.i.hide()
        h = self.b.get_object ('entry_host').get_text()
        p = self.b.get_object ('spin_port') .get_value_as_int()
        a = self.b.get_object ('progressbar1')

        a.set_fraction (0)

        s = Gio.SocketClient()
        s.connect_to_host_async (h, p, None, self.socket_ready_cb, a)

    def socket_ready_cb (self, s, r, a):
        print "Ready", s, r, a
        a.set_fraction (0.2)
        f = os.path.expanduser(self.entry.get_text())

        self.buf = []

        try:
            con = s.connect_to_host_finish(r)
            ostr = con.get_output_stream()
            istr = con.get_input_stream()

            a.set_fraction (0.3)
            ostr.write_async (open(f).read(DEFAULT_READ_SIZE),
                              0, None, self.socket_write_cb, a)
            istr.read_async (self.buf, DEFAULT_READ_SIZE, 0, None, self.socket_read_cb, a)

        except gi._glib.GError, e:
            return self._show_error (str(e))

    def socket_write_cb (self, s, r, a):
        a.set_fraction (0.8)

    def socket_read_cb (self, s, r, a):
        if s.read_finish(r) != 3: # 'OK' we have nothing better…
            self._show_error ('Something May have gone wrong, but I\'m really not sure.',
                              Gtk.MessageType.WARNING)

        a.set_fraction (1)

    # def with_python_sockets (non-async) ():
    #     try:
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     except socket.error, msg:
    #         return self._show_error ("Could not connect: " + msg[1])
    #     try:
    #         sock.connect((h, p))
    #     except socket.error, msg:
    #         return self._show_error ("Could not connect: " + msg[1])

    #     a.set_fraction (0.2)

    #     sock.send(open(f).read(1024))
    #     a.set_fraction (0.8)
    #     r = sock.recv(1024)
    #     sock.close()
    #     if r != 'OK':
    #         return self._show_error("Error while chit chating: " + r)

    #     a.set_fraction (1)
    #     a.set_text('suceso !')


if __name__ == "__main__":
    app = KeySend ()

    Gtk.main()
