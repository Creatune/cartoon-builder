# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import gtk
from zipfile import ZipFile

try:
    import json
    json.dumps
except (ImportError, AttributeError):
    import simplejson as json

import theme
from sound import *
from ground import *
from utils import *
from char import *

class Document:
    tape = []
    ground = None
    sound = None

    for i in range(theme.TAPE_COUNT):
        tape.append(EmptyFrame())

def clean(index):
    from char import Frame
    Document.tape[index] = EmptyFrame()

def save(filepath):
    zip = ZipFile(filepath, 'w')

    cfg = { 'ground': {},
            'sound' : {},
            'frames': {},
            'tape'  : [] }

    def _save(node, arcname, value):
        if value.custom():
            node['custom'] = True
            node['filename'] = arcname
            zip.writestr(arcname, value.serialize())
        else:
            node['custom'] = False
        node['name'] = unicode(value.name)
        node['id'] = value.id

    _save(cfg['ground'], 'ground.png', Document.ground)
    _save(cfg['sound'], 'sound', Document.sound)

    for i, frame in enumerate(
            [i for i in set(Document.tape) if not i.empty() and i.custom()]):
        arcname = 'frame%03d.png' % i
        cfg['frames'][frame.id] = arcname
        zip.writestr(arcname, frame.serialize())

    for i, frame in enumerate(Document.tape):
        if not frame.empty():
            node = {}
            node['custom'] = frame.custom()
            node['id'] = frame.id
            node['index'] = i
            cfg['tape'].append(node)

    zip.writestr('MANIFEST', json.dumps(cfg))
    zip.close()

def load(filepath):
    zip = ZipFile(filepath, 'r')
    cfg = json.loads(zip.read('MANIFEST'))

    def _load(node, restored_class, preinstalled_class):
        if node['custom']:
            return restored_class(node['name'], node['id'],
                    zip.read(node['filename']))
        else:
            return preinstalled_class(node['name'], node['id'])

    Document.ground = _load(cfg['ground'], RestoredGround, PreinstalledGround)
    Document.sound = _load(cfg['sound'], RestoredSound, PreinstalledSound)

    frames = {}

    for id, arcname in cfg['frames'].items():
        frames[id] = RestoredFrame(id, zip.read(arcname))

    for node in cfg['tape']:
        i = node['index']
        if i < theme.TAPE_COUNT:
            if node['custom']:
                Document.tape[i] = frames[node['id']]
            else:
                Document.tape[i] = PreinstalledFrame(node['id'])

    zip.close()
