#!/usr/bin/env python3

import argparse
import base64

from pathlib import Path

import libzim
from libzim.writer import Creator, StringProvider, Hint

# blank 48x48 transparent PNG
DEFAULT_ILLUSTRATION = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwAQMAAABtzGvEAAAAGXRFWHRTb2Z0d2FyZQBB"
        "ZG9iZSBJbWFnZVJlYWR5ccllPAAAAANQTFRFR3BMgvrS0gAAAAF0Uk5TAEDm2GYAAAAN"
        "SURBVBjTY2AYBdQEAAFQAAGn4toWAAAAAElFTkSuQmCC"
    )

DEFAULT_DEV_ZIM_METADATA = {
    "Name": "Test Name",
    "Title": "Test Title",
    "Creator": "Test Creator",
    "Publisher": "Test Publisher",
    "Date": "2023-01-01",
    "Description": "Test Description",
    "Language": "fra",
}

class StaticItem(libzim.writer.Item):
    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_path(self) -> str:
        return getattr(self, "path", "")

    def get_title(self) -> str:
        return getattr(self, "title", "")

    def get_mimetype(self) -> str:
        return getattr(self, "mimetype", "")

    def get_contentprovider(self) -> libzim.writer.ContentProvider:
        return StringProvider(content=getattr(self, "content", ""))

    def get_hints(self) -> dict[Hint, int]:
        return getattr(self, "hints", {Hint.FRONT_ARTICLE: False})

parser = argparse.ArgumentParser()
parser.add_argument('output_file_path')
parser.add_argument('--redirect-count', default=0, type=int)
parser.add_argument('--efficiently', action='store_true', default=False)

args = parser.parse_args()

def bytes2int(b):
    return int.from_bytes(b, 'little')

def format_int(n, digits):
    fmt = f'{{n:0{digits}d}}'
    return fmt.format(n=n)

def generate_zim_file(filepath, redirect_count):
    digits = len(str(redirect_count-1))
    creator = Creator(filepath)
    creator.config_indexing(False, "eng")
    with creator:
        creator.add_illustration(48, DEFAULT_ILLUSTRATION)
        for name, value in DEFAULT_DEV_ZIM_METADATA.items():
            creator.add_metadata(name, value)
        creator.add_item(StaticItem(path="home", title="Home", content="Hello world", mimetype="text/plain"))
        creator.set_mainpath("home")

        for num in range(redirect_count):
            if num % 1000000 == 0:
                print(num)
            formatted_num = format_int(num, digits)
            creator.add_redirection(f"r_{formatted_num}", f"Redirect {formatted_num}", "home", {Hint.FRONT_ARTICLE : False})

def redirect_dirent_bytes(k):
    k = bytes(k, 'ascii')
    path = b'r_' + k + b'\x00'
    title = b'Redirect ' + k + b'\x00'
    return b'\xff\xff\x00C' + 8*b'\x00' +  path + title

def generate_zim_file_efficiently(filepath, redirect_count):
    generate_zim_file(filepath, 0)
    with open(filepath, "rb") as f:
        z = f.read()

    dirent_count = bytes2int(z[24:28])
    dirent_ptr_table_offset = bytes2int(z[32:40])
    dirent_offsets = []
    OFFSET_SIZE = 8
    for i in range(dirent_count):
        o = dirent_ptr_table_offset + OFFSET_SIZE*i
        dirent_offset = bytes2int(z[o:o+OFFSET_SIZE])
        dirent_offsets.append(dirent_offset)

    digits = len(str(redirect_count-1))
    redirect_record_size = len(redirect_dirent_bytes(format_int(0, digits)))
    size_of_injected_dirents = redirect_count * redirect_record_size
    size_of_injected_offsets = redirect_count * OFFSET_SIZE

    def adjusted_offset(o, a):
        o = bytes2int(o) + a
        return o.to_bytes(OFFSET_SIZE, 'little')

    with open(filepath, "wb") as f:
        # XXX need to fix the dirent count and table offset fields
        f.write(z[0:24])
        f.write((dirent_count + redirect_count).to_bytes(4, 'little'))
        f.write(z[28:32])
        f.write(adjusted_offset(z[32:40], size_of_injected_dirents))
        f.write(z[40:48])
        f.write(adjusted_offset(z[48:56], size_of_injected_dirents + size_of_injected_offsets))
        f.write(z[56:64])
        f.write((bytes2int(z[64:68]) + redirect_count).to_bytes(4, 'little'))
        f.write(z[68:72])
        f.write(adjusted_offset(z[72:80], size_of_injected_dirents + size_of_injected_offsets))
        f.write(z[80:dirent_offsets[1]])
        for i in range(redirect_count):
            f.write(redirect_dirent_bytes(format_int(i, digits)))
        f.write(z[dirent_offsets[1]:dirent_ptr_table_offset])

        f.write(dirent_offsets[0].to_bytes(OFFSET_SIZE, 'little'))

        redirect_dirent_offset = dirent_offsets[1]
        for i in range(redirect_count):
            f.write(redirect_dirent_offset.to_bytes(OFFSET_SIZE, 'little'))
            redirect_dirent_offset += redirect_record_size

        for do in dirent_offsets[1:]:
            adjusted_dirent_offset = do + size_of_injected_dirents
            f.write(adjusted_dirent_offset.to_bytes(OFFSET_SIZE, 'little'))

        # copy cluster ptr table and checksum
        f.write(z[dirent_ptr_table_offset + OFFSET_SIZE * dirent_count:])


if not args.efficiently:
    generate_zim_file(args.output_file_path, args.redirect_count)
else:
    generate_zim_file_efficiently(args.output_file_path, args.redirect_count)
