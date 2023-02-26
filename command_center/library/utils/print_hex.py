#!/usr/bin/env python
# -*- coding: latin-1 -*-

# <-- removing this magic comment breaks Python 3.4 on Windows
"""
1. Dump binary data to the following text format:

00000000: 00 00 00 5B 68 65 78 64  75 6D 70 5D 00 00 00 00  ...[hexdump]....
00000010: 00 11 22 33 44 55 66 77  88 99 AA BB CC DD EE FF  .."3DUfw........

It is similar to the one used by:
Scapy
00 00 00 5B 68 65 78 64 75 6D 70 5D 00 00 00 00  ...[hexdump]....
00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF  .."3DUfw........

Far Manager
000000000: 00 00 00 5B 68 65 78 64 ¦ 75 6D 70 5D 00 00 00 00     [hexdump]
000000010: 00 11 22 33 44 55 66 77 ¦ 88 99 AA BB CC DD EE FF   ?"3DUfw??ª»ÌÝîÿ


2. Restore binary data from the formats above as well
   as from less exotic strings of raw hex

"""

__version__ = '3.4dev'
__author__ = 'anatoly techtonik <techtonik@gmail.com>'
__license__ = 'Public Domain'

import binascii  # binascii is required for Python 3
import codecs
import mmap
import sys

# --- constants


# --- - chunking helpers
def chunks(seq, size):
    '''Generator that cuts sequence (bytes, memoryview, etc.)
       into chunks of given size. If `seq` length is not multiply
       of `size`, the lengh of the last chunk returned will be
       less than requested.

       >>> list( chunks([1,2,3,4,5,6,7], 3) )
       [[1, 2, 3], [4, 5, 6], [7]]
    '''
    d, m = divmod(len(seq), size)
    for i in range(d):
        yield seq[i * size:(i + 1) * size]
    if m:
        yield seq[d * size:]


def chunkread(f, size):
    '''Generator that reads from file like object. May return less
       data than requested on the last read.'''
    c = f.read(size)
    while len(c):
        yield c
        c = f.read(size)


def genchunks(mixed, size):
    '''Generator to chunk binary sequences or file like objects.
       The size of the last chunk returned may be less than
       requested.'''
    if hasattr(mixed, 'read'):
        return chunkread(mixed, size)
    else:
        return chunks(mixed, size)


# --- - /chunking helpers


def dehex(hextext):
    """
    Convert from hex string to binary data stripping
    whitespaces from `hextext` if necessary.
    """
    return bytes.fromhex(hextext)


def dump(binary, size=2, sep=' '):
    '''
    Convert binary data (bytes in Python 3 and str in
    Python 2) to hex string like '00 DE AD BE EF'.
    `size` argument specifies length of text chunks
    and `sep` sets chunk separator.
    '''
    hexstr = binascii.hexlify(binary).decode('ascii')
    return sep.join(chunks(hexstr.upper(), size))


def dumpgen(data):
    '''
    Generator that produces strings:

    '00000000: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................'
    '''
    generator = genchunks(data, 16)
    for addr, d in enumerate(generator):
        # 00000000:
        line = '%08X: ' % (addr * 16)
        # 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
        dumpstr = dump(d)
        line += dumpstr[:8 * 3]
        if len(d) > 8:  # insert separator if needed
            line += ' ' + dumpstr[8 * 3:]
        # ................
        # calculate indentation, which may be different for the last line
        pad = 2
        if len(d) < 16:
            pad += 3 * (16 - len(d))
        if len(d) <= 8:
            pad += 1
        line += ' ' * pad

        for byte in d:
            # printable ASCII range 0x20 to 0x7E
            if 0x20 <= byte <= 0x7E:
                line += chr(byte)
            else:
                line += '.'
        yield line


def hexdump(data, result='print', output=None):
    '''
    Transform binary data to the hex dump text format:

    00000000: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................

      [x] data argument as a binary string
      [x] data argument as a file like object

    Returns result depending on the `result` argument:
      'print'     - prints line by line
      'return'    - returns single string
      'generator' - returns generator that produces lines
      'file' - save file
    '''
    if type(data) == str:
        raise TypeError('Abstract unicode data (expected bytes sequence)')

    gen = dumpgen(data)
    if result == 'generator':
        return gen
    elif result == 'return':
        return '\n'.join(gen)
    elif result == 'print':
        for line in gen:
            print(line)
    elif result == 'file':
        with open(output, 'w', encoding='utf-8') as fd:
            for line in gen:
                fd.writelines(line)
    else:
        raise ValueError('Unknown value of `result` argument')


def restore(dump):
    '''
    Restore binary data from a hex dump.
      [x] dump argument as a string
      [ ] dump argument as a line iterator

    Supported formats:
      [x] hexdump.hexdump
      [x] Scapy
      [x] Far Manager
    '''
    minhexwidth = 2 * 16  # minimal width of the hex part - 00000... style
    bytehexwidth = 3 * 16 - 1  # min width for a bytewise dump - 00 00 ... style

    result = bytes()
    if type(dump) != str:
        raise TypeError('Invalid data for restore')

    text = dump.strip()  # ignore surrounding empty lines
    dumptype = None
    for line in text.split('\n'):
        # strip address part
        addrend = line.find(':')
        if 0 < addrend < minhexwidth:  # : is not in ascii part
            line = line[addrend + 1:]
        line = line.lstrip()
        # check dump type
        if line[2] == ' ':  # 00 00 00 ...  type of dump
            # calculate separator position
            sepstart = (2 + 1) * 8  # ('00'+' ')*8
            sep = line[sepstart:sepstart + 3]
            if sep[0] == ' ' and sep[1] != ' ':
                # ...00 00  00 00...
                dumptype = "doublespaced"
                hexdata = line[:bytehexwidth + 1]
            elif sep[1] == ' ':
                # ...00 00 | 00 00...  - Far Manager
                dumptype = "singlebytesep"
                hexdata = line[:sepstart - 1] + line[sepstart + 2:bytehexwidth + 3]
            elif sep == '\xe2\x94\x82':
                # ...00 00 \xe2\x94\x82 00 00...  - Far Manager (utf-8)
                dumptype = "unicodesep"
                hexdata = line[:sepstart - 1] + line[sepstart + 4:bytehexwidth + 5]
            else:
                # ...00 00 00 00... - Scapy, no separator
                dumptype = "nosep"
                hexdata = line[:bytehexwidth]
            line = hexdata
        result += dehex(line)
    return result


def file_hex_search(filename, hex_str):
    offsets = []
    with codecs.open(filename, encoding="utf-8", errors='ignore') as fd:
        needle = b"{0}".format(hex_str)
        needle_len = len(needle)

        haystack = mmap.mmap(fd.fileno(), length=0, access=mmap.ACCESS_READ)
        offset = haystack.find(needle)

        while offset >= 0:
            hex_string = ''.join(r'%02X' % (b) for b in haystack[offset: offset+needle_len])
            print('offset: {}, needle: "{}"'.format(offset, hex_string))
            offsets.append(offset)
            #yield offset

            offset += needle_len
            offset = haystack.find(needle, offset)

    return offsets
#
# def file_check_hex(fd, hex, hex_size, offset):
#     """
#     'FF D8 FF E1 2C')
#     """
#     check_bytes = dehex(hex)
#
#     fd.seek(offset)
#
#     r_byers = fd.read(hex_size)
#
#
# def main():
#     o_file = "test.jpg"
#
#     file_check_hex(open(o_file, 'rb'), '69 66 00 00 4D 4D', 6, 8)
#
#
# if __name__ == '__main__':
#     main()

