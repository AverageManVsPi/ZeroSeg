#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


class Constants(object):
    MAX7219_REG_NOOP = 0x0
    MAX7219_REG_DIGIT0 = 0x1
    MAX7219_REG_DIGIT1 = 0x2
    MAX7219_REG_DIGIT2 = 0x3
    MAX7219_REG_DIGIT3 = 0x4
    MAX7219_REG_DIGIT4 = 0x5
    MAX7219_REG_DIGIT5 = 0x6
    MAX7219_REG_DIGIT6 = 0x7
    MAX7219_REG_DIGIT7 = 0x8
    MAX7219_REG_DECODEMODE = 0x9
    MAX7219_REG_INTENSITY = 0xA
    MAX7219_REG_SCANLIMIT = 0xB
    MAX7219_REG_SHUTDOWN = 0xC
    MAX7219_REG_DISPLAYTEST = 0xF


class Device(object):
    """
    Base class for handling multiple cascaded MAX7219 devices.
    Callers should generally pick the :py:class:`sevensegment` class

    A buffer is maintained which holds the bytes that will be cascaded
    every time :py:func:`flush` is called.
    """
    NUM_DIGITS = 8

    def __init__(self, cascaded=1, spi_bus=0, spi_device=0, vertical=False):
        """
        Constructor: `cascaded` should be the number of cascaded MAX7219
        devices that are connected. `vertical` should be set to True if
        the text should start from the header instead perpendicularly.
        """
        import spidev
        assert cascaded > 0, "Must have at least one device!"

        self._cascaded = cascaded
        self._buffer = [0] * self.NUM_DIGITS * self._cascaded
        self._spi = spidev.SpiDev()
        self._spi.open(spi_bus, spi_device)
        self._vertical = vertical

        self.command(Constants.MAX7219_REG_SCANLIMIT, 7)  # show all 8 digits
        self.command(Constants.MAX7219_REG_DECODEMODE, 0)  # use matrix (not digits)
        self.command(Constants.MAX7219_REG_DISPLAYTEST, 0)  # no display test
        self.command(Constants.MAX7219_REG_SHUTDOWN, 1)  # not shutdown mode
        self.brightness(7)  # intensity: range: 0..15
        self.clear()

    def command(self, register, data):
        """
        Sends a specific register some data, replicated for all cascaded
        devices
        """
        assert Constants.MAX7219_REG_DECODEMODE <= register <= Constants.MAX7219_REG_DISPLAYTEST
        self._write([register, data] * self._cascaded)

    def _write(self, data):
        """
        Send the bytes (which should comprise of alternating command,
        data values) over the SPI device.
        """
        self._spi.xfer2(list(data))

    def _values(self, position, buf):
        """
        A generator which yields the digit/column position and the data
        value from that position for each of the cascaded devices.
        """
        for deviceId in range(self._cascaded):
            yield position + Constants.MAX7219_REG_DIGIT0
            yield buf[(deviceId * self.NUM_DIGITS) + position]

    def clear(self, device_id=None):
        """
        Clears the buffer the given deviceId if specified (else clears all
        devices), and flushes.
        """
        assert not device_id or 0 <= device_id < self._cascaded, "Invalid deviceId: {0}".format(device_id)

        if device_id is None:
            start = 0
            end = self._cascaded
        else:
            start = device_id
            end = device_id + 1

        for device_id in range(start, end):
            for position in range(self.NUM_DIGITS):
                self.set_byte(device_id,
                              position + Constants.MAX7219_REG_DIGIT0,
                              0, redraw=False)

        self.flush()

    def _preprocess_buffer(self, buf):
        """
        Overload in subclass to provide custom behaviour: see
        matrix implementation for example.
        """
        return buf

    def flush(self):
        """
        For each digit/column, cascade out the contents of the buffer
        cells to the SPI device.
        """
        # Allow subclasses to pre-process the buffer: they shouldn't
        # alter it, so make a copy first.
        buf = self._preprocess_buffer(list(self._buffer))
        assert len(buf) == len(self._buffer), "Preprocessed buffer is wrong size"
        if self._vertical:
            tmp_buf = []
            for x in range(0, self._cascaded):
                tmp_buf += rotate(buf[x * 8:x * 8 + 8])
            buf = tmp_buf

        for posn in range(self.NUM_DIGITS):
            self._write(self._values(posn, buf))

    def brightness(self, intensity):
        """
        Sets the brightness level of all cascaded devices to the same
        intensity level, ranging from 0..15. Note that setting the brightness
        to a high level will draw more current, and may cause intermittent
        issues / crashes if the USB power source is insufficient.
        """
        assert 0 <= intensity < 16, "Invalid brightness: {0}".format(intensity)
        self.command(Constants.MAX7219_REG_INTENSITY, intensity)

    def set_byte(self, device_id, position, value, redraw=True):
        """
        Low level mechanism to set a byte value in the buffer array. If redraw
        is not suppled, or set to True, will force a redraw of _all_ buffer
        items: If you are calling this method rapidly/frequently (e.g in a
        loop), it would be more efficient to set to False, and when done,
        call :py:func:`flush`.

        Prefer to use the higher-level method calls in the subclasses below.
        """
        assert 0 <= device_id < self._cascaded, "Invalid deviceId: {0}".format(device_id)
        assert Constants.MAX7219_REG_DIGIT0 <= position <= Constants.MAX7219_REG_DIGIT7, "Invalid digit/column: {0}" \
            .format(position)
        assert 0 <= value < 256, 'Value {0} outside range 0..255'.format(value)

        offset = (device_id * self.NUM_DIGITS) + position - Constants.MAX7219_REG_DIGIT0
        self._buffer[offset] = value

        if redraw:
            self.flush()

    def rotate_left(self, redraw=True):
        """
        Scrolls the buffer one column to the left. The data that scrolls off
        the left side re-appears at the right-most position. If redraw
        is not suppled, or left set to True, will force a redraw of _all_ buffer
        items
        """
        t = self._buffer[-1]
        for i in range((self.NUM_DIGITS * self._cascaded) - 1, 0, -1):
            self._buffer[i] = self._buffer[i - 1]
        self._buffer[0] = t
        if redraw:
            self.flush()

    def rotate_right(self, redraw=True):
        """
        Scrolls the buffer one column to the right. The data that scrolls off
        the right side re-appears at the left-most position. If redraw
        is not suppled, or left set to True, will force a redraw of _all_ buffer
        items
        """
        t = self._buffer[0]
        for i in range(0, (self.NUM_DIGITS * self._cascaded) - 1, 1):
            self._buffer[i] = self._buffer[i + 1]
        self._buffer[-1] = t
        if redraw:
            self.flush()

    def scroll_left(self, redraw=True):
        """
        Scrolls the buffer one column to the left. Any data that scrolls off
        the left side is lost and does not re-appear on the right. An empty
        column is inserted at the right-most position. If redraw
        is not suppled, or set to True, will force a redraw of _all_ buffer
        items
        """
        del self._buffer[0]
        self._buffer.append(0)
        if redraw:
            self.flush()

    def scroll_right(self, redraw=True):
        """
        Scrolls the buffer one column to the right. Any data that scrolls off
        the right side is lost and does not re-appear on the left. An empty
        column is inserted at the left-most position. If redraw
        is not suppled, or set to True, will force a redraw of _all_ buffer
        items
        """
        del self._buffer[-1]
        self._buffer.insert(0, 0)
        if redraw:
            self.flush()


class Sevensegment(Device):
    """
    Implementation of MAX7219 devices cascaded with a series of seven-segment
    LEDs. It provides a convenient method to write a number to a given device
    in octal, decimal or hex, flushed left/right with zero padding. Base 10
    numbers can be either integers or floating point (with the number of
    decimal points configurable).
    """
    _UNDEFINED = 0x08
    _RADIX = {8: 'o', 10: 'f', 16: 'x'}
    # Some letters cannot be represented by 7 segments, so dictionary lookup
    # will default to _UNDEFINED (an underscore) instead.
    _M = ('Μ', 'Ϸ')
    _W = ('Ŵ', 'Ƿ')
    _DIGITS = {
        ' ': 0x00,
        '-': 0x01,
        '_': 0x08,
        '0': 0x7e,
        '1': 0x30,
        '2': 0x6d,
        '3': 0x79,
        '4': 0x33,
        '5': 0x5b,
        '6': 0x5f,
        '7': 0x70,
        '8': 0x7f,
        '9': 0x7b,
        'a': 0x7d,
        'b': 0x1f,
        'c': 0x0d,
        'd': 0x3d,
        'e': 0x6f,
        'f': 0x47,
        'g': 0x7b,
        'h': 0x17,
        'i': 0x10,
        'j': 0x18,
        # 'k': cant represent
        'l': 0x06,
        # < m
        _M[0]: 0x66,
        _M[1]: 0x72,
        # > m
        'n': 0x15,
        'o': 0x1d,
        'p': 0x67,
        'q': 0x73,
        'r': 0x05,
        's': 0x5b,
        't': 0x0f,
        'u': 0x1c,
        'v': 0x1c,
        # < w
        _W[0]: 0x1e,
        _W[1]: 0x3c,
        # > w
        # 'x': cant represent
        'y': 0x3b,
        'z': 0x6d,
        'A': 0x77,
        'B': 0x7f,
        'C': 0x4e,
        'D': 0x7e,
        'E': 0x4f,
        'F': 0x47,
        'G': 0x5e,
        'H': 0x37,
        'I': 0x30,
        'J': 0x38,
        # 'K': cant represent
        'L': 0x0e,
        'N': 0x76,
        'O': 0x7e,
        'P': 0x67,
        'Q': 0x73,
        'R': 0x46,
        'S': 0x5b,
        'T': 0x0f,
        'U': 0x3e,
        'V': 0x3e,
        # 'X': cant represent
        'Y': 0x3b,
        'Z': 0x6d,
        ',': 0x80,
        '.': 0x80,
        '*': 0x63
    }

    def letter(self, device_id, position, char, dot=False, redraw=True):
        """
        Looks up the most appropriate character representation for char
        from the digits table, and writes that bitmap value into the buffer
        at the given deviceId / position.
        """
        assert dot in [0, 1, False, True]
        value = self._DIGITS.get(str(char), self._UNDEFINED) | (dot << 7)
        self.set_byte(device_id, position, value, redraw)

    def write_number(self, device_id, value, base=10, decimal_places=0,
                     zero_pad=False, left_justify=False):
        """
        Formats the value according to the parameters supplied, and displays
        on the specified device. If the formatted number is larger than
        8 digits, then an OverflowError is raised.
        """
        assert 0 <= device_id < self._cascaded, "Invalid deviceId: {0}".format(device_id)
        assert base in self._RADIX, "Invalid base: {0}".format(base)

        # Magic up a printf format string
        size = self.NUM_DIGITS
        format_str = '%'

        if zero_pad:
            format_str += '0'

        if decimal_places > 0:
            size += 1

        if left_justify:
            size *= -1

        format_str = '{fmt}{size}.{dp}{type}'.format(
            fmt=format_str, size=size, dp=decimal_places,
            type=self._RADIX[base])

        position = Constants.MAX7219_REG_DIGIT7
        str_value = format_str % value

        # Go through each digit in the formatted string,
        # updating the buffer accordingly
        for char in str_value:

            if position < Constants.MAX7219_REG_DIGIT0:
                self.clear(device_id)
                raise OverflowError('{0} too large for display'.format(str_value))

            if char == '.':
                continue

            dp = (decimal_places > 0 and position == decimal_places + 1)
            self.letter(device_id, position, char, dot=dp, redraw=False)
            position -= 1

        self.flush()

    def get_replaced_mw(self, text):
        return text.replace('M', "".join(self._M)).replace('W', "".join(self._W))

    def write_text(self, device_id, text, dots=None, mw=False):
        """
        Outputs the text (as near as possible) on the specific device. If
        text is larger than 8 characters, then an OverflowError is raised.
        Puts dots on specific positions entered in dots
        """
        assert 0 <= device_id < self._cascaded, "Invalid deviceId: {0}".format(device_id)
        if mw:
            text = self.get_replaced_mw(text)
        if len(text) > 8:
            raise OverflowError('{0} too large for display'.format(text))
        text_inv = text.ljust(8)[::-1]
        if dots is None:
            for pos, char in enumerate(text_inv):
                self.letter(device_id, Constants.MAX7219_REG_DIGIT0 + pos, char, redraw=False)
        else:
            for pos, char in enumerate(text_inv):
                self.letter(device_id, Constants.MAX7219_REG_DIGIT0 + pos, char, dot=(pos in dots), redraw=False)

        self.flush()

    def show_message(self, text, delay=0.4, mw=False):
        """
        Transitions the text message across the devices from left-to-right
        Puts dots directly on previous character, not as an individual char
        """
        # Add some spaces on (same number as cascaded devices) so that the
        # message scrolls off to the left completely.
        if mw:
            text = self.get_replaced_mw(text)
        text += ' ' * (self._cascaded * 8 + 1)
        for pos, char in enumerate(text[:-1]):
            if char == '.' and (pos > 0 and text[pos - 1] != '.'):
                continue
            time.sleep(delay)
            self.scroll_right(redraw=False)
            self._buffer[0] = self._DIGITS.get(char, self._UNDEFINED) \
                | ((text[pos + 1] == '.' and char != '.') << 7)
            self.flush()
