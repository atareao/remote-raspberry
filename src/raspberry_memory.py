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
import re
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


class RaspberryMemory(Gtk.Overlay):

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

        label0 = Gtk.Label(_('RAM'))
        label0.set_name('special')
        label0.set_halign(Gtk.Align.START)
        box.add(label0)

        listbox0 = Gtk.ListBox()
        box.add(listbox0)

        self.ram_total = Gtk.Label()
        self.ram_total.set_valign(Gtk.Align.CENTER)
        self.ram_total.set_width_chars(20)
        listbox0.add(SettingRow(_('Total'),
                                _('The total amount of RAM installed'),
                                self.ram_total))

        ram_free_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.ram_free = Gtk.Label()
        self.ram_free.set_width_chars(20)
        self.ram_free.set_valign(Gtk.Align.CENTER)
        ram_free_box.add(self.ram_free)
        self.ram_free_progress = Gtk.LevelBar()
        self.ram_free_progress.set_min_value(0)
        self.ram_free_progress.set_max_value(1)
        ram_free_box.add(self.ram_free_progress)
        listbox0.add(SettingRow(_('Free'),
                                _('The amount of unused or free memory'),
                                ram_free_box))

        ram_used_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.ram_used = Gtk.Label()
        self.ram_used.set_width_chars(20)
        self.ram_used.set_valign(Gtk.Align.CENTER)
        ram_used_box.add(self.ram_used)
        self.ram_used_progress = Gtk.LevelBar()
        self.ram_used_progress.set_min_value(0)
        self.ram_used_progress.set_max_value(1)
        ram_used_box.add(self.ram_used_progress)
        listbox0.add(SettingRow(_('Used'),
                                _('The total amount of RAM used'),
                                ram_used_box))

        ram_shared_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.ram_shared = Gtk.Label()
        self.ram_shared.set_width_chars(20)
        self.ram_shared.set_valign(Gtk.Align.CENTER)
        ram_shared_box.add(self.ram_shared)
        self.ram_shared_progress = Gtk.LevelBar()
        self.ram_shared_progress.set_min_value(0)
        self.ram_shared_progress.set_max_value(1)
        ram_shared_box.add(self.ram_shared_progress)
        listbox0.add(SettingRow(_('Shared'),
                                _('Amount of memory mostly used by tmpfs'),
                                ram_shared_box))

        ram_buffcache_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.ram_buffcache = Gtk.Label()
        self.ram_buffcache.set_width_chars(20)
        self.ram_buffcache.set_valign(Gtk.Align.CENTER)
        ram_buffcache_box.add(self.ram_buffcache)
        self.ram_buffcache_progress = Gtk.LevelBar()
        self.ram_buffcache_progress.set_min_value(0)
        self.ram_buffcache_progress.set_max_value(1)
        ram_buffcache_box.add(self.ram_buffcache_progress)
        listbox0.add(SettingRow(_('Buff/cache'),
                                _('Sum of buffers and cache'),
                                ram_buffcache_box))

        ram_available_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.ram_available = Gtk.Label()
        self.ram_available.set_width_chars(20)
        self.ram_available.set_valign(Gtk.Align.CENTER)
        ram_available_box.add(self.ram_available)
        self.ram_available_progress = Gtk.LevelBar()
        self.ram_available_progress.set_min_value(0)
        self.ram_available_progress.set_max_value(1)
        ram_available_box.add(self.ram_available_progress)
        listbox0.add(SettingRow(_('Available'),
                                _('Estimation of memory available'),
                                ram_available_box))

        label1 = Gtk.Label(_('Swap'))
        label1.set_name('special')
        label1.set_halign(Gtk.Align.START)
        box.add(label1)

        listbox1 = Gtk.ListBox()
        box.add(listbox1)

        self.swap_total = Gtk.Label()
        self.swap_total.set_valign(Gtk.Align.CENTER)
        self.swap_total.set_width_chars(20)
        listbox1.add(SettingRow(_('Total'),
                                _('The total amount of swap installed'),
                                self.swap_total))

        swap_free_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.swap_free = Gtk.Label()
        self.swap_free.set_width_chars(20)
        self.swap_free.set_valign(Gtk.Align.CENTER)
        swap_free_box.add(self.swap_free)
        self.swap_free_progress = Gtk.LevelBar()
        self.swap_free_progress.set_min_value(0)
        self.swap_free_progress.set_max_value(1)
        swap_free_box.add(self.swap_free_progress)
        listbox1.add(SettingRow(_('Free'),
                                _('The amount of unused or free swap'),
                                swap_free_box))

        swap_cached_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.swap_cached = Gtk.Label()
        self.swap_cached.set_width_chars(20)
        self.swap_cached.set_valign(Gtk.Align.CENTER)
        swap_cached_box.add(self.swap_cached)
        self.swap_cached_progress = Gtk.LevelBar()
        self.swap_cached_progress.set_min_value(0)
        self.swap_cached_progress.set_max_value(1)
        swap_cached_box.add(self.swap_cached_progress)
        listbox1.add(SettingRow(_('Cached'),
                                _('The amount of swap cached'),
                                swap_cached_box))

        swap_used_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.swap_used = Gtk.Label()
        self.swap_used.set_width_chars(20)
        self.swap_used.set_valign(Gtk.Align.CENTER)
        swap_used_box.add(self.swap_used)
        self.swap_used_progress = Gtk.LevelBar()
        self.swap_used_progress.set_min_value(0)
        self.swap_used_progress.set_max_value(1)
        swap_used_box.add(self.swap_used_progress)
        listbox1.add(SettingRow(_('used'),
                                _('The amount of swap used'),
                                swap_used_box))

        self.raspberryClient = RaspberryClient.fromConfiguration()
        self.load_information()

    def update(self):
        self.load_information()

    def load_information(self):
        self.raspberryClient.connect()
        meminfo = self.raspberryClient.read_file('/proc/meminfo')

        memtotal = re.findall(r'MemTotal:\s*(\d*)', meminfo)
        memtotal = float(memtotal[0])/1024.0 if memtotal else 0.0
        self.ram_total.set_text(str(int(memtotal)) + ' ' + _('MB'))

        memfree = re.findall(r'MemFree:\s*(\d*)', meminfo)
        memfree = float(memfree[0])/1024.0 if memfree else 0.0
        self.ram_free.set_text(str(int(memfree)) + ' ' + _('MB'))
        self.ram_free_progress.set_value(memfree/memtotal)

        buffers = re.findall(r'Buffers:\s*(\d*)', meminfo)
        buffers = float(buffers[0])/1024.0 if buffers else 0.0

        cached = re.findall(r'Cached:\s*(\d*)', meminfo)
        cached = float(cached[0])/1024.0 if cached else 0.0

        memused = memtotal - (memfree + buffers + cached)
        self.ram_used.set_text(str(int(memused)) + ' ' + _('MB'))
        self.ram_used_progress.set_value(memused/memtotal)

        memshared = re.findall(r'Shmem:\s*(\d*)', meminfo)
        memshared = float(memshared[0])/1024.0 if memshared else 0.0
        self.ram_shared.set_text(str(int(memshared)) + ' ' + _('MB'))
        self.ram_shared_progress.set_value(memshared/memtotal)

        buffcache = buffers + cached
        self.ram_buffcache.set_text(str(int(buffcache)) + ' ' + _('MB'))
        self.ram_buffcache_progress.set_value(buffcache/memtotal)

        memavailable = re.findall(r'MemAvailable:\s*(\d*)', meminfo)
        memavailable = float(memavailable[0])/1024.0 if memavailable else 0.0
        self.ram_available.set_text(str(int(memavailable)) + ' ' + _('MB'))
        self.ram_available_progress.set_value(memavailable/memtotal)

        swaptotal = re.findall(r'SwapTotal:\s*(\d*)', meminfo)
        swaptotal = float(swaptotal[0])/1024.0 if swaptotal else 0.0
        self.swap_total.set_text(str(int(swaptotal)) + ' ' + _('MB'))

        swapfree = re.findall(r'SwapFree:\s*(\d*)', meminfo)
        swapfree = float(swapfree[0])/1024.0 if swapfree else 0.0
        self.swap_free.set_text(str(int(swapfree)) + ' ' + _('MB'))
        self.swap_free_progress.set_value(swapfree/swaptotal)

        swapcached = re.findall(r'SwapCached:\s*(\d*)', meminfo)
        swapcached = float(swapcached[0])/1024.0 if swapcached else 0.0
        self.swap_cached.set_text(str(int(swapcached)) + ' ' + _('MB'))
        self.swap_cached_progress.set_value(swapcached/swaptotal)

        swapused = swaptotal - (swapfree + swapcached)
        self.swap_used.set_text(str(int(swapused)) + ' ' + _('MB'))
        self.swap_used_progress.set_value(swapused/swaptotal)

