#!/usr/bin/env python3
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
    gi.require_version('Gio', '2.0')
    gi.require_version('GLib', '2.0')
    gi.require_version('GObject', '2.0')
    gi.require_version('Handy', '0.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Handy
import os
import json
import subprocess
import mimetypes
import urllib
import comun
from comun import _
from sidewidget import SideWidget
from utils import variant_to_value, CSS
from configurator import Configuration
from settings import SettingRow
from configure_connection import ConfigureConnection
from raspberry_memory import RaspberryMemory
from string import Template


class MainWindow(Gtk.ApplicationWindow):
    __gsignals__ = {
        'text-changed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE,
                         (object,)),
        'save-me': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE,
                    (object,)), }

    def on_close(self, *args):
        self.configureConnection.save_configuration()

    def __init__(self, app, files=[]):
        Gtk.ApplicationWindow.__init__(self, application=app)
        self.app = app
        self.set_icon_from_file(comun.ICON)
        self.connect('destroy', self.on_close)

        '''
        max_action = Gio.SimpleAction.new_stateful(
            "maximize", None, GLib.Variant.new_boolean(False))
        max_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(max_action)
        '''

        self.init_headerbar()

        mainbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.add(mainbox)

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC,
                                  Gtk.PolicyType.AUTOMATIC)
        scrolledwindow.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        scrolledwindow.set_visible(True)
        scrolledwindow.set_property('min-content-width', 200)
        mainbox.pack_start(scrolledwindow, False, False, 0)

        sidebar = Gtk.ListBox()
        sidebar.connect('row-activated', self.on_row_activated)
        scrolledwindow.add(sidebar)

        option1 = SideWidget(_('Configure connection'),
                             'preferences-desktop-remote-desktop-symbolic')
        sidebar.add(option1)

        self.option2 = SideWidget(_('Raspberry Memory'),
                                  'drive-harddisk-solidstate-symbolic')
        sidebar.add(self.option2)

        self.stack = Gtk.Stack()
        sw = Gtk.ScrolledWindow(child=self.stack)
        mainbox.pack_start(sw, True, True, 0)

        self.configureConnection = ConfigureConnection(self)
        self.stack.add_named(self.configureConnection, 'configureConnection')
        option1.set_stack('configureConnection')

        self.raspberryMemory = RaspberryMemory(self)
        self.stack.add_named(self.raspberryMemory, 'raspberryMemory')
        self.option2.set_stack('raspberryMemory')

        self.load_css()
        self.set_size_request(800, 900)
        self.connect('realize', self.on_realize)

        self.load_configuration()
        self.option2.set_sensitive(
            self.configuration.get('checked_connection'))

        self.show_all()

    def on_realize(self, *_):
        monitor = Gdk.Display.get_primary_monitor(Gdk.Display.get_default())
        scale = monitor.get_scale_factor()
        monitor_width = monitor.get_geometry().width / scale
        monitor_height = monitor.get_geometry().height / scale
        width = self.get_preferred_width()[0]
        height = self.get_preferred_height()[0]
        self.move((monitor_width - width)/2, (monitor_height - height)/2)

    def on_row_activated(self, lb, sidewidget):
        self.stack.set_visible_child_name(sidewidget.get_stack())

    def on_apply_clicked(self, *args):
        self.raspberryMemory.update()

    def init_headerbar(self):
        self.control = {}
        self.menu_selected = 'suscriptions'

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = comun.APPNAME
        self.set_titlebar(hb)

        self.apply_controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        hb.pack_start(self.apply_controls)

        self.control['apply'] = Gtk.Button()
        self.control['apply'].connect('clicked', self.on_apply_clicked)
        self.control['apply'].set_tooltip_text(_('Update Rasbperry info'))
        self.control['apply'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='preferences-system-symbolic'), Gtk.IconSize.BUTTON))
        self.apply_controls.pack_start(self.control['apply'],
                                       False, False, 0)

        help_model = Gio.Menu()

        help_section1_model = Gio.Menu()
        help_section1_model.append(_('Homepage'), 'app.goto_homepage')
        help_section1 = Gio.MenuItem.new_section(None, help_section1_model)
        help_model.append_item(help_section1)

        help_section2_model = Gio.Menu()
        help_section2_model.append(_('Code'), 'app.goto_code')
        help_section2_model.append(_('Issues'), 'app.goto_bug')
        help_section2 = Gio.MenuItem.new_section(None, help_section2_model)
        help_model.append_item(help_section2)

        help_section3_model = Gio.Menu()
        help_section3_model.append(_('Twitter'), 'app.goto_twitter')
        help_section3_model.append(_('GitHub'), 'app.goto_github')
        help_section3 = Gio.MenuItem.new_section(None, help_section3_model)
        help_model.append_item(help_section3)

        help_section4_model = Gio.Menu()
        help_section4_model.append(_('Donations'), 'app.goto_donate')
        help_section4 = Gio.MenuItem.new_section(None, help_section4_model)
        help_model.append_item(help_section4)

        help_section5_model = Gio.Menu()
        help_section5_model.append(_('About'), 'app.about')
        help_section5 = Gio.MenuItem.new_section(None, help_section5_model)
        help_model.append_item(help_section5)

        help_section6_model = Gio.Menu()
        help_section6_model.append(_('Quit'), 'app.quit')
        help_section6 = Gio.MenuItem.new_section(None, help_section6_model)
        help_model.append_item(help_section6)

        self.control['help'] = Gtk.MenuButton()
        self.control['help'].set_tooltip_text(_('Help'))
        self.control['help'].set_menu_model(help_model)
        self.control['help'].add(Gtk.Image.new_from_gicon(Gio.ThemedIcon(
            name='open-menu-symbolic'), Gtk.IconSize.BUTTON))
        hb.pack_end(self.control['help'])

    def on_toggled(self, widget, arg):
        if widget.get_active() is True:
            if arg == self.menu_selected:
                if self.menu[arg].get_active() is False:
                    self.menu[arg].set_active(True)
            else:
                old = self.menu_selected
                self.menu_selected = arg
                self.menu[old].set_active(False)
        else:
            if self.menu_selected == arg:
                widget.set_active(True)

    def load_css(self):
        settings = Gio.Settings.new('org.gnome.desktop.interface')
        theme = variant_to_value(settings.get_user_value('gtk-theme'))
        if theme and theme.find('dark') > -1:
            background_color = '#373737'
            forecolor = '#d7d7d7'
            border_color = '#282828'
            hover_color = '#3e3e3e'
            caption_color = forecolor
        else:
            background_color = '#ffffff'
            forecolor = '#2d2d34'
            border_color = '#c3c9d0'
            hover_color = '#e0e0e1'
            caption_color = '#403f38'

        css = Template(CSS).substitute(background_color=background_color,
                             border_color=border_color,
                             forecolor=forecolor,
                             hover_color=hover_color,
                             caption_color=caption_color)
        css = str(css).encode()

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def load_configuration(self):
        self.configuration = Configuration()
