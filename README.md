# MIDI LFO

MIDI LFO includes several waveforms, maximum and minimum values and allows more than 7-bit values through MSB and LSB controllers.

## Installation

MIDI LFO is a Python package that is installed the standard way with `python3 setup.py install`. However, as it contains desktop application related resources, it is installed with `make`.

The package dependencies for Debian based distributions are:
- make
- python3
- python3-setuptools
- python3-mido
- python3-rtmidi

You can easily install them by running `sudo apt-get install make python3 python3-setuptools python3-mido python3-rtmidi`.

To install MIDI LFO symply run `make && sudo make install`.
