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

"""MIDI LFO backend"""

import mido
import time
import logging
from threading import Thread
import math
import random

logger = logging.getLogger(__name__)

mido.set_backend('mido.backends.rtmidi')
logger.debug('Mido backend: {:s}'.format(str(mido.backend)))

MAX_PHASE = 1000000


class Backend(object):

    def __init__(self):
        logger.debug('Initializing...')
        self.thread = None
        self.port = None
        self.channel = 0
        self.control = 19
        self.min = 0
        self.max = 127
        self.f = 0.125
        self.set_sampling_period(0.03)
        self.set_frequency(0.125)
        self.shaper = self.get_sine_value
        self.get_s_n_h_value(0, True)
        self.change_value_callback = None

    def set_sampling_period(self, sampling_period):
        self.sampling_period = sampling_period
        self.max_f = 1.0 / (self.sampling_period * 2)
        return self.set_frequency(self.f)

    def set_frequency(self, f):
        if f > self.max_f:
            f = self.max_f
        self.f = f
        self.inc = MAX_PHASE * f * self.sampling_period
        return f

    def disconnect(self):
        if self.port:
            logger.debug('Disconnecting...')
            try:
                self.port.close()
            except IOError:
                logger.error('IOError while disconnecting')
            self.port = None

    def connect(self, device):
        logger.debug('Connecting...')
        try:
            self.disconnect()
            self.port = mido.open_ioport(device)
        except IOError as e:
            logger.error('IOError while connecting: "{:s}"'.format(str(e)))

    def start(self):
        self.phase = 0.0
        self.running = True
        self.thread = Thread(target=self.lfo_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def get_next_value(self):
        self.phase += self.inc
        if self.phase > MAX_PHASE:
            self.phase -= MAX_PHASE
            reset = True
        else:
            reset = False
        fraction = float(self.phase) / MAX_PHASE
        value = self.shaper(fraction, reset)
        return int((value * (self.max - self.min)) + self.min)

    def lfo_loop(self):
        last_value = -1
        while self.running:
            value = self.get_next_value()
            if value != last_value:
                self.change_value_callback(value / 127.0)
                last_value = value
                msg = mido.Message('control_change', channel=self.channel,
                                   control=self.control, value=value)
                if self.port:
                    self.port.send(msg)
            time.sleep(self.sampling_period)

    def get_sine_value(self, value, reset):
        return (math.sin(value * math.pi * 2) * 0.5) + 0.5

    def get_triangle_value(self, value, reset):
        if value < 0.25:
            return 0.5 + 2 * value
        if value >= 0.25 and value < 0.75:
            return 1.0 - (value - 0.25) * 2
        else:
            return (value - 0.75) * 2

    def get_saw_up_value(self, value, reset):
        return value

    def get_saw_down_value(self, value, reset):
        return 1.0 - self.get_saw_up_value(value, reset)

    def get_square_value(self, value, reset):
        if value < 0.5:
            return 0
        else:
            return 1

    def get_s_n_h_value(self, value, reset):
        if reset:
            self.snh = random.random()
        return self.snh

    def get_noise_value(self, value, reset):
        return random.random()
