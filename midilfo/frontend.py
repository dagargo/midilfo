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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
import mido
import getopt
import sys
from midilfo.lfo import LFO
import pkg_resources
import logging
"""MIDI LFO user interface"""

gi.require_version('Gtk', '3.0')

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
        self.lfo = LFO()
        self.lfo.change_value_callback = self.set_lfo_value
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
        self.msb_control = builder.get_object('msb_control')
        self.lsb_control = builder.get_object('lsb_control')
        self.channel = builder.get_object('channel')
        self.minimum = builder.get_object('minimum')
        self.maximum = builder.get_object('maximum')
        self.lsb = builder.get_object('lsb')
        self.total_bits = builder.get_object('total_bits')
        self.lsb_bits = builder.get_object('lsb_bits')

        self.device.connect('changed', lambda widget: self.set_device(widget))
        self.run.connect(
            'state-set', lambda widget, state: self.set_run(state, widget))
        self.frequency.connect(
            'value-changed', lambda widget: self.set_frequency(widget))
        self.wave.connect('changed', lambda widget: self.set_wave(widget))
        self.msb_control.connect(
            'value-changed', lambda widget: self.set_msb_control(widget))
        self.lsb_control.connect(
            'value-changed', lambda widget: self.set_lsb_control(widget))
        self.channel.connect(
            'value-changed', lambda widget: self.set_channel(widget))
        self.minimum.connect(
            'value-changed', lambda widget: self.set_minimum(widget))
        self.maximum.connect(
            'value-changed', lambda widget: self.set_maximum(widget))
        self.lsb.connect(
            'state-set', lambda widget, state: self.switch_lsb(state, widget))
        self.total_bits.connect(
            'value-changed', lambda widget: self.set_total_bits(widget))
        self.lsb_bits.connect(
            'value-changed', lambda widget: self.set_lsb_bits(widget))

        self.load_devices()
        self.set_device(self.device)
        self.set_frequency(self.frequency)
        self.set_wave(self.wave)
        self.set_msb_control(self.msb_control)
        self.set_lsb_control(self.lsb_control)
        self.set_channel(self.channel)
        self.set_minimum(self.minimum)
        self.set_maximum(self.maximum)
        self.switch_lsb(False, self.lsb)
        self.main_window.present()

    def switch_lsb(self, value, switch):
        switch.set_state(value)
        switch.set_active(value)
        if value:
            self.lfo.total_bits = self.total_bits.get_value_as_int()
            self.lfo.lsb_bits = self.lsb_bits.get_value_as_int()
        else:
            self.lfo.total_bits = 7
            self.lfo.lsb_bits = 0
        self.lsb_control.set_sensitive(value)
        self.total_bits.set_sensitive(value)
        self.lsb_bits.set_sensitive(value)

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
            self.lfo.connect(value)

    def set_run(self, value, switch):
        switch.set_state(value)
        switch.set_active(value)
        if value:
            self.lfo.start()
        else:
            self.lfo.stop()

    def set_frequency(self, scale):
        self.lfo.set_frequency(scale.get_value())

    def set_wave(self, combo):
        wave = combo.get_active()
        if wave == 0:
            self.lfo.shaper = self.lfo.get_noise_value
        elif wave == 1:
            self.lfo.shaper = self.lfo.get_s_n_h_value
        elif wave == 2:
            self.lfo.shaper = self.lfo.get_saw_down_value
        elif wave == 3:
            self.lfo.shaper = self.lfo.get_saw_up_value
        elif wave == 4:
            self.lfo.shaper = self.lfo.get_sine_value
        elif wave == 5:
            self.lfo.shaper = self.lfo.get_square_value
        elif wave == 6:
            self.lfo.shaper = self.lfo.get_triangle_value

    def set_total_bits(self, spin):
        total_bits = self.total_bits.get_value_as_int()
        lsb_bits = self.lsb_bits.get_value_as_int()
        lsb_bits = total_bits - 7 if total_bits - lsb_bits > 7 else lsb_bits
        self.lsb_bits.set_value(lsb_bits)
        self.lfo.total_bits = total_bits

    def set_lsb_bits(self, spin):
        total_bits = self.total_bits.get_value_as_int()
        lsb_bits = self.lsb_bits.get_value_as_int()
        total_bits = lsb_bits + 7 if total_bits - lsb_bits > 7 else total_bits
        self.total_bits.set_value(total_bits)
        self.lfo.lsb_bits = lsb_bits

    def set_msb_control(self, spin):
        self.lfo.msb_control = spin.get_value_as_int()

    def set_lsb_control(self, spin):
        self.lfo.lsb_control = spin.get_value_as_int()

    def set_channel(self, spin):
        self.lfo.channel = spin.get_value_as_int()

    def set_minimum(self, scale):
        self.lfo.min = scale.get_value()

    def set_maximum(self, scale):
        self.lfo.max = scale.get_value()

    def show_about(self):
        self.about_dialog.run()
        self.about_dialog.hide()

    def quit(self):
        logger.debug('Quitting...')
        self.lfo.stop()
        self.lfo.disconnect()
        self.main_window.hide()
        Gtk.main_quit()

    def main(self):
        self.init_ui()
        Gtk.main()
