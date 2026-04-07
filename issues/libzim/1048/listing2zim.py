#!/usr/bin/env python3

import argparse
import sys
import libzim
from libzim.writer import Creator, StringProvider, Hint


def removePrefix(s, prefix):
    assert s.startswith(prefix)
    return s[len(prefix):]

def loadListing():
    entries = []
    curEntry = None
    for line in sys.stdin:
        line = line.strip('\n')
        if line.startswith('path:'):
            if curEntry is not None:
                entries.append(curEntry)
            path = removePrefix(line, 'path: ')
            curEntry = (path, )
        elif line.startswith('* title:          '):
            title = removePrefix(line, '* title:          ')
            curEntry += (title, )
        elif line.startswith('* redirect index: '):
            redirect = int(removePrefix(line, '* redirect index: '))
            curEntry += (redirect, )
        else:
            pass

    return entries

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
        return getattr(self, "hints", {Hint.FRONT_ARTICLE: True})

class DirentPrinter:
    def __init__(self):
        self.items = []
        self.redirections = []

    def add_item(self, item):
        self.items.append(item)
        print(f'{item.get_path()}: "{item.get_title()}"');

    def add_redirection(self, path, title, targetPath, hints):
        self.redirections.append((path, title, targetPath))
        print(f'{path}: "{title}" -> {targetPath}');


def processDirents(entries, c):
    for e in entries:
        if len(e) == 2:
            path, title = e
            c.add_item(StaticItem(path=path, title=title, content='', mimetype="text/html"))
        elif len(e) == 3:
            path, title, redirect = e
            targetPath = entries[redirect][0]
            c.add_redirection(path, title, targetPath, {})

def createZimFile(entries, zimfilepath):
    with Creator(zimfilepath) as c:
        processDirents(entries, c)

def printDirents(entries):
    processDirents(entries, DirentPrinter())

parser = argparse.ArgumentParser()
parser.add_argument('--create-zim', dest='zimfilepath', default=None, type=str)
parser.add_argument('--print-entries', action='store_true', default=False)
args = parser.parse_args()

entries = loadListing()

if args.print_entries:
    printDirents(entries)
elif args.zimfilepath is not None:
    createZimFile(entries, args.zimfilepath)
