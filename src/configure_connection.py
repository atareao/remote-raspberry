#/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# This file is part of remote-raspberry
#
# Copyright (c) 2020 Lorenzo Carbonell Cerezo <a.k.a. atareao>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

import gi
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('GLib', '2.0')
    gi.require_version('Gio', '2.0')
    gi.require_version('Handy', '0.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Handy
import time
import os
import json
import mimetypes
import urllib
import comun
from comun import _
from sidewidget import SideWidget
from configurator import Configuration
from utils import get_desktop_environment
from settings import SettingRow
from utils import variant_to_value, select_value_in_combo
from utils import get_selected_value_in_combo
from raspberry_client import RaspberryClient


class ConfigureConnection(Gtk.Overlay):

    def __init__(self, parent):
        Gtk.Overlay.__init__(self)
        self._parent = parent
        self.__set_ui()

    def __set_ui(self):
        handycolumn = Handy.Column()
        handycolumn.set_maximum_width(700)
        handycolumn.set_margin_top(24)
        self.add(handycolumn)

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        handycolumn.add(box)

        label0 = Gtk.Label(_('Configure connection'))
        label0.set_name('special')
        label0.set_halign(Gtk.Align.START)
        box.add(label0)

        listbox0 = Gtk.ListBox()
        box.add(listbox0)

        self.hostname = Gtk.Entry()
        self.hostname.set_valign(Gtk.Align.CENTER)
        listbox0.add(SettingRow(_('Hostname'),
                                _('Set the hostname or IP'),
                                self.hostname))

        self.port = Gtk.Entry()
        self.port.set_valign(Gtk.Align.CENTER)
        listbox0.add(SettingRow(_('Port'),
                                _('Set the port'),
                                self.port))

        self.username = Gtk.Entry()
        self.username.set_valign(Gtk.Align.CENTER)
        listbox0.add(SettingRow(_('User name'),
                                _('Set the user name.'),
                                self.username))

        label1 = Gtk.Label(_('Credentials'))
        label1.set_name('special')
        label1.set_halign(Gtk.Align.START)
        box.add(label1)

        listbox1 = Gtk.ListBox()
        box.add(listbox1)

        self.connection_option = Gtk.Switch()
        self.connection_option.set_state(True)
        self.connection_option.connect('state-set',
                                       self.on_connection_option_activate)
        self.connection_option.set_valign(Gtk.Align.CENTER)
        listbox1.add(SettingRow(_('Select credentials by password or key file'),
                                _('If switch is on credentials by password'),
                                self.connection_option))

        self.listbox2 = Gtk.ListBox()
        box.add(self.listbox2)

        self.password = Gtk.Entry()
        self.password.set_valign(Gtk.Align.CENTER)
        self.listbox2.add(SettingRow(_('Password'),
                                    _('Set the user password'),
                                    self.password))

        self.listbox3 = Gtk.ListBox()
        self.listbox3.set_sensitive(False)
        box.add(self.listbox3)

        self.keyfile = Gtk.FileChooserButton.new(_('Select keyfile'),
                                                 Gtk.FileChooserAction.OPEN)
        self.keyfile.set_current_folder(os.path.expanduser('~/.ssh'))
        file_filter = Gtk.FileFilter.new()
        file_filter.set_name(_('*.pub files'))
        file_filter.add_pattern('*.pub')
        self.keyfile.add_filter(file_filter)
        self.keyfile.set_valign(Gtk.Align.CENTER)
        self.listbox3.add(SettingRow(_('keyfile'),
                                    _('Set the keyfile'),
                                    self.keyfile))

        label2 = Gtk.Label(_('Test connection'))
        label2.set_name('special')
        label2.set_halign(Gtk.Align.START)
        box.add(label2)

        self.listbox4 = Gtk.ListBox()
        box.add(self.listbox4)

        self.test_connection = Gtk.Button.new_with_label(_('Unknown'))
        self.test_connection.set_valign(Gtk.Align.CENTER)
        self.test_connection.connect('clicked', self.on_test_connection_clicked)
        self.listbox4.add(SettingRow(_('Test connection'),
                                     _('Results can be: Unknown, OK or KO'),
                                    self.test_connection))

        self.load_configuration()

    def on_test_connection_clicked(self, widget):
        hostname = self.hostname.get_text()
        port = self.port.get_text()
        username = self.username.get_text()
        if self.connection_option.get_state():
            password = self.password.get_text()
            raspberryClient = RaspberryClient(hostname, port, username,
                                              password)
        else:
            keyfile = self.keyfile.get_filename()
            raspberryClient = RaspberryClient(hostname, port, username,
                                              keyfile=keyfile)
        watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self._parent.get_window().set_cursor(watch_cursor)
        GLib.idle_add(self.try_connection, raspberryClient, widget)

    def try_connection(self, client, widget):
        try:
            client.connect()
            self._parent.get_window().set_cursor(None)
            dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO)
            dialog.set_title(_('Raspberry Connection'))
            dialog.add_button(_('Ok'), Gtk.ResponseType.YES)
            if client.is_connected():
                widget.set_label(_('OK'))
                dialog.set_markup('Connection OK')
            else:
                widget.set_label(_('KO'))
                dialog.set_markup('Connection KO')
            dialog.run()
            dialog.destroy()
        except Exception as e:
            widget.set_label(_('KO'))
            self._parent.get_window().set_cursor(None)
            dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR)
            dialog.set_title(_('Raspberry Connection'))
            dialog.add_button(_('Ok'), Gtk.ResponseType.YES)
            dialog.set_markup(str(e))
            dialog.run()
            dialog.destroy()
        client.disconnect()

    def on_connection_option_activate(self, widget, status):
        self.listbox2.set_sensitive(status)
        self.listbox3.set_sensitive(not status)

    def load_configuration(self):
        configuration = Configuration()
        self.hostname.set_text(configuration.get('hostname'))
        self.port.set_text(configuration.get('port'))
        self.username.set_text(configuration.get('username'))
        self.password.set_text(configuration.get('password'))
        self.keyfile.set_filename(configuration.get('keyfilename'))
        self.connection_option.set_state(
            configuration.get('credentials_by_password'))
        if configuration.get('checked_connection'):
            self.test_connection.set_label(_('OK'))
        else:
            self.test_connection.set_label(_('Unknown'))

    def save_configuration(self):
        configuration = Configuration()
        configuration.set('hostname', self.hostname.get_text())
        configuration.set('port', self.port.get_text())
        configuration.set('username', self.username.get_text())
        configuration.set('password', self.password.get_text())
        configuration.set('keyfilename', self.keyfile.get_filename())
        configuration.set('credentials_by_password',
            self.connection_option.get_state())
        if self.test_connection.get_label() == _('OK'):
            configuration.set('checked_connection', True)
        else:
            configuration.set('checked_connection', False)
        configuration.save()

    def __del__(self):
        self.save_configuration()
