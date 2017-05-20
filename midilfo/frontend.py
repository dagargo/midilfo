# -*- coding: utf-8 -*-
#
# Copyright 2017 David García Goñi
#
# This file is part of MIDI LFO.
#
# MIDI LFO is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MIDI LFO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MIDI LFO. If not, see <http://www.gnu.org/licenses/>.

"""MIDI LFO user interface"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
import logging
import pkg_resources
from midilfo.backend import Backend
import sys
import getopt
import mido

PKG_NAME = 'midilfo'

GLib.threads_init()

glade_file = pkg_resources.resource_filename(__name__, 'resources/gui.glade')
version = pkg_resources.get_distribution(PKG_NAME).version

log_level = logging.ERROR


def print_help():
    print('Usage: {:s} [-v]'.format(PKG_NAME))

try:
    opts, args = getopt.getopt(sys.argv[1:], "hv")
except getopt.GetoptError:
    print_help()
    sys.exit(1)
for opt, arg in opts:
    if opt == '-h':
        print_help()
        sys.exit()
    elif opt == '-v':
        log_level = logging.DEBUG

logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

builder = Gtk.Builder()
builder.add_from_file(glade_file)


class Frontend(object):
    """MIDI LFO user interface"""

    def __init__(self):
        self.backend = Backend()
        self.backend.change_value_callback = self.set_lfo_value
        self.main_window = None

    def init_ui(self):
        self.main_window = builder.get_object('main_window')
        self.main_window.connect(
            'delete-event', lambda widget, event: self.quit())
        self.main_window.set_position(Gtk.WindowPosition.CENTER)
        self.about_dialog = builder.get_object('about_dialog')
        self.about_dialog.set_position(Gtk.WindowPosition.CENTER)
        self.about_dialog.set_transient_for(self.main_window)
        self.about_dialog.set_version(version)
        self.refresh_button = builder.get_object('refresh_button')
        self.refresh_button.connect(
            'clicked', lambda widget: self.load_devices())
        self.about_button = builder.get_object('about_button')
        self.about_button.connect('clicked', lambda widget: self.show_about())
        self.value = builder.get_object('value')
        self.device = builder.get_object('device')
        self.device_liststore = builder.get_object('device_liststore')
        self.run = builder.get_object('run')
        self.frequency = builder.get_object('frequency')
        self.wave = builder.get_object('wave')
        self.control = builder.get_object('control')
        self.channel = builder.get_object('channel')
        self.minimum = builder.get_object('minimum')
        self.maximum = builder.get_object('maximum')

        self.device.connect('changed', lambda widget: self.set_device(widget))
        self.run.connect(
            'state-set', lambda widget, state: self.set_run(state, widget))
        self.frequency.connect(
            'value-changed', lambda widget: self.set_frequency(widget))
        self.wave.connect('changed', lambda widget: self.set_wave(widget))
        self.control.connect(
            'value-changed', lambda widget: self.set_control(widget))
        self.channel.connect(
            'value-changed', lambda widget: self.set_channel(widget))
        self.minimum.connect(
            'value-changed', lambda widget: self.set_minimum(widget))
        self.maximum.connect(
            'value-changed', lambda widget: self.set_maximum(widget))

        self.load_devices()
        self.set_device(self.device)
        self.set_frequency(self.frequency)
        self.set_wave(self.wave)
        self.set_control(self.control)
        self.set_channel(self.channel)
        self.set_minimum(self.minimum)
        self.set_maximum(self.maximum)
        self.main_window.present()

    def set_lfo_value(self, value):
        GLib.idle_add(self.value.set_fraction, value)

    def load_devices(self):
        self.device_liststore.clear()
        i = 0
        for port in mido.get_ioport_names():
            logger.debug('Adding port {:s}...'.format(port))
            self.device_liststore.append([port])
            if i == 0:
                logger.debug('Port {:s} is active'.format(port))
                self.device.set_active(i)
            i += 1

    def set_device(self, combo):
        if combo.get_active() != -1:
            value = combo.get_model()[combo.get_active()][0]
            self.backend.connect(value)

    def set_run(self, value, switch):
        switch.set_state(value)
        switch.set_active(value)
        if value:
            self.backend.start()
        else:
            self.backend.stop()

    def set_frequency(self, scale):
        self.backend.set_frequency(scale.get_value())

    def set_wave(self, combo):
        wave = combo.get_active()
        if wave == 0:
            self.backend.shaper = self.backend.get_noise_value
        elif wave == 1:
            self.backend.shaper = self.backend.get_s_n_h_value
        elif wave == 2:
            self.backend.shaper = self.backend.get_saw_down_value
        elif wave == 3:
            self.backend.shaper = self.backend.get_saw_up_value
        elif wave == 4:
            self.backend.shaper = self.backend.get_sine_value
        elif wave == 5:
            self.backend.shaper = self.backend.get_square_value
        elif wave == 6:
            self.backend.shaper = self.backend.get_triangle_value

    def set_control(self, spin):
        self.backend.control = spin.get_value_as_int()

    def set_channel(self, spin):
        self.backend.channel = spin.get_value_as_int()

    def set_minimum(self, scale):
        self.backend.min = scale.get_value()

    def set_maximum(self, scale):
        self.backend.max = scale.get_value()

    def show_about(self):
        self.about_dialog.run()
        self.about_dialog.hide()

    def quit(self):
        logger.debug('Quitting...')
        self.backend.stop()
        self.backend.disconnect()
        self.main_window.hide()
        Gtk.main_quit()

    def main(self):
        self.init_ui()
        Gtk.main()
