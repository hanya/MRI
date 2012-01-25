#  Copyright 2011 Tsutomu Uchino
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

def create_popupmenu(ctx, items):
    """ create popup menu from items
        [ [id, pos, type, 'label', "command", acc_key], [] ]
    """
    try:
        menu = ctx.getServiceManager().createInstanceWithContext(
            "com.sun.star.awt.PopupMenu", ctx)
        for i in items:
            if i[0] is None or i[0] == -1:
                menu.insertSeparator(i[1])
            else:
                menu.insertItem(i[0], i[3], i[2], i[1])
                menu.setCommand(i[0], i[4])
                if i[5] is not None:
                    try:
                        menu.setAcceleratorKeyEvent(i[0], i[5])
                    except:
                        pass
    except Exception, e:
        print(e)
    return menu

def get_current_sentence(target, mini):
    """ (\n|  )... min ...  """
    lfstart = target.rfind("\n", 0, mini)
    lfend = target.find("\n", mini)
    if lfend < 0:
        lfend = len(target)
    spstart = target.rfind("  ", 0, mini)
    spend = target.find("  ", mini)
    if spend < 0:
        spend = len(target)
    if lfstart >= spstart:
        start = lfstart +1
        if start < 0:
            start = 0
    else:
        start = spstart +2
    if spend < lfend:
        end = spend
    else:
        end = lfend
    return (start, end)


def get_current_line(target, mini):
    """ # xxx\n...min....\nxxx """
    start = target.rfind("\n", 0, mini) +1
    if start < 0:
        start = 0
    end = target.find("\n", mini)
    if end < 0:
        end = len(target)
    return (start, end)


def get_first_word(line):
    pos = line.lstrip().find(" ")
    if pos < 0:
        pos = len(line)
    return line[0:pos]

