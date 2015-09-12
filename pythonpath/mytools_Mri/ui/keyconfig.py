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

from mytools_Mri import macros

import uno
import unohelper
import traceback
import os.path

from com.sun.star.awt.tree import XTreeExpansionListener
class TreeExpansionListener(unohelper.Base, XTreeExpansionListener):
    def __init__(self, act):
        self.act = act
    def dispose(self, ev):
        self.act = None
    def requestChildNodes(self, ev):
        self.act.request_nodes(ev)
    def treeExpanding(self, ev):
        pass
    def treeCollapsing(self, ev):
        pass
    def treeExpanded(self, ev):
        pass
    def treeCollapsed(self, ev):
        pass

from com.sun.star.view import XSelectionChangeListener
class SelectionChangeListener(unohelper.Base, XSelectionChangeListener):
    def __init__(self, act):
        self.act = act
    def disposing(self, ev):
        self.act = None
    def selectionChanged(self, ev):
        self.act.selection_changed(ev)

from com.sun.star.awt import XKeyListener
class KeyListener(unohelper.Base, XKeyListener):
    def __init__(self, act):
        self.act = act
    def disposing(self, ev):
        self.act = None
    def keyPressed(self, ev):
        # tab
        if ev.KeyCode != 1282:
            self.act.key_pressed(ev)
    def keyReleased(self, ev):
        pass

from com.sun.star.awt import XItemListener
class ItemListener(unohelper.Base, XItemListener):
    def __init__(self, act):
        self.act = act
    def disposing(self, ev):
        self.act = None
    def itemStateChanged(self, ev):
        self.act.item_selected(ev)

from com.sun.star.awt import XActionListener
class ActionListener(unohelper.Base, XActionListener):
    def __init__(self, act):
        self.act = act
    def disposing(self, ev):
        self.act = None
    def actionPerformed(self, ev):
        cmd = ev.ActionCommand
        try:
            if cmd == "assign":
                self.act.assign()
            elif cmd == "delete":
                self.act.delete()
            elif cmd == "macros":
                self.act.macros()
            elif cmd == "default":
                self.act.default()
            elif cmd == "add":
                self.act.add()
            elif cmd == "store":
                self.act.store()
            elif cmd == "close":
                ev.Source.getContext().endExecute()
        except Exception as e:
            print(e)
            traceback.print_exc()


class KeyEntry(object):
    """ Individual key entry. """
    
    def __init__(self, command, name, code, mod, desc, macro_file=None, macro_name=None):
        self.command = command
        self.name = name
        self.keycode = code
        self.modifires = mod
        self.keydesc = desc
        self.macro_file = macro_file
        self.macro_name = macro_name
    
    def eql(self, mod, key):
        return self.modifires == mod and self.keycode == key
    
    def __repr__(self):
        return "<KeyEntry: %s>" % self.name
    
    def to_a(self):
        return [self.command, self.modifires, self.keycode]


from com.sun.star.awt import Rectangle
from com.sun.star.awt.KeyModifier import SHIFT, MOD1, MOD2#, MOD3
from mytools_Mri.ui.keys import KeyConfigLoader, default_keys
import mytools_Mri.values
MOD3 = 8

_commands = {
    "ref": "Open IDL Reference", 
    "execute": "Get/Set Value or Call Method", 
    "opennew": "Open in New Window", 
    "next": "Go Forward", 
    "previous": "Go Back", 
    "properties": "Switch to Properties", 
    "methods": "Switch to Methods", 
    "interfaces": "Switch to Interfaces", 
    "services": "Switch to Services", 
    "search": "Search", 
    "selectline": "Select Line", 
    "selectword": "Select Word", 
    "sort": "Switch Sort", 
    "abbr": "Switch Abbriviation", 
    "pseud_prop": "Switch Pseud-Property", 
    "code": "Switch Code", 
    "contextmenu": "Context Menu for Grid", 
    "index": "XIndexAccess shortcut", 
    "name": "XNameAccess shortcut", 
    "gridcopy": "Copy on Grid"
}

class KeyConfig(KeyConfigLoader):
    """ Extended key configuration to modify keys. """
    
    SHIFT = "Shift"
    MOD_1 = "Ctrl"
    MOD_2 = "Alt"
    MOD_3 = "Ctrl"
    MOD__ = "Cmd"
    
    MACRO = "macro:"
    FUNC_SEP = "$"
    KEYS_SEP = "+"
    MARGIN = 25
    
    ROOT = "ROOT"
    
    CONFIG_DIALOG = "KeyConfig"
    COMMANDS_DIALOG = "CommandList"
    MACROS_DIALOG = "MacroSelector"
    
    EXTENSION_DIALOGS = None
    
    def __init__(self, ctx):
        KeyConfigLoader.__init__(self, ctx)
        #self.config = Config()
        self.entries = None
        self.keys = None
        self.keys_list = None
        self.keys_edit = None
        self.font = None
        self.width = None
        self.space_width = None
        self._mod = 0 # current
        self._key = 0
        self.macros_dlg = None
        self._macros = macros.Macros(self)
        
        self.EXTENSION_DIALOGS = mytools_Mri.values.MRI_DIR + "/dialogs/"
        # check os type
        import sys
        if sys.platform.find("mac") >= 0:
            KeyConfig.MOD_3 = KeyConfig.MOD__
    
    def start(self):
        """ To show the window to modify. """
        self.keys = self._get_key_map()
        
        self._init_entries()
        dlg = self._create_dialog(self.CONFIG_DIALOG)
        dc = dlg.getControl
        listener = ActionListener(self)
        btn_assign = dc("btnAssign")
        btn_delete = dc("btnDelete")
        btn_macros = dc("btnMacros")
        btn_default = dc("btnDefault")
        btn_add = dc("btnAdd")
        btn_store = dc("btnStore")
        btn_close = dc("btnClose")
        
        for name, value in locals().items():
            if name.startswith("btn_"):
                value.addActionListener(listener)
                value.setActionCommand(name[4:].lower())
        
        self.keys_edit = dc("editKeys")
        self.keys_list = dc("listKeys")
        self.keys_edit.addKeyListener(KeyListener(self))
        self.keys_list.addItemListener(ItemListener(self))
        
        peer = dlg.getPeer()
        device = peer.createDevice(10, 10)
        font = device.getFont(dlg.getModel().FontDescriptor)
        space_width = font.getStringWidth(" ")
        #length = max([font.getStringWidth(entry.name) for entry in self.entries])
        margin = self.MARGIN
        width = self.keys_list.getPosSize().Width
        entries = []
        for entry in self.entries:
            _length1 = font.getStringWidth(entry.name)
            _length2 = font.getStringWidth(entry.keydesc)
            entries.append(entry.name + (" " * int((width - _length1 - _length2 - margin) / space_width)) + entry.keydesc)
        self.keys_list.addItems(tuple(entries), 0)
        self.width = width
        self.space_width = space_width
        self.font = font
        dlg.execute()
        self._dispose()
        dlg.dispose()
    
    
    def _dispose(self):
        """ To help to close the dialog. """
        self.keys_edit = None
        self.keys_list = None
        self.font = None
        if self.macros_dlg:
            self.macros_dlg.dispose()
            self.macros_dlg = None
    
    def _init_entries(self):
        """ Prepare keys. """
        commands = _commands
        #keys = _keys
        keys = self.load()
        if keys is None:
            keys = default_keys
        entries = []
        for key in keys:
            name = commands.get(key[0], None)
            if name is None:
                cmd = key[0][6:]
                file_name, func_name = cmd.split(self.FUNC_SEP, 2)
                item = self._macros.get_function_info(file_name, func_name)
                if item is None:
                    continue
                entry = KeyEntry(key[0], item[1], key[2], key[1], 
                    self.get_key_desc(key[1], key[2]), file_name, func_name)
            else:
                entry = KeyEntry(key[0], name, key[2], key[1], 
                    self.get_key_desc(key[1], key[2]))
            entries.append(entry)
        self.entries = entries
    
    def add_entry(self, entry):
        """ Add new entry. """
        self.entries.append(entry)
        self.add_item(self.create_item(entry.name, self.get_key_desc(entry.modifires, entry.keycode)))
    
    def _create_dialog(self, name):
        """ Helps to instantiate dialog with name. """
        return self._create_service(
            "com.sun.star.awt.DialogProvider").createDialog(
            self.EXTENSION_DIALOGS + name + ".xdl")
    
    def _get_key_map(self):
        """ Get key-value pairs. """
        keys = {}
        tdm = self.ctx.getByName(
            "/singletons/com.sun.star.reflection.theTypeDescriptionManager")
        constants = tdm.getByHierarchicalName("com.sun.star.awt.Key")
        for constant in constants.getConstants():
            keys[constant.getConstantValue()] = constant.getName()
        return keys
    
    def set_current(self, mod, key):
        self._mod = mod
        self._key = key
    
    def set_key(self, desc):
        self.keys_edit.getModel().Text = desc
    
    def get_key(self):
        return self.keys_edit.getModel().Text
    
    def get_selected(self):
        return self.keys_list.getSelectedItemPos()
    
    def item_selected(self, ev):
        n = self.get_selected()
        if n >= 0:
            entry = self.entries[n]
            mod = entry.modifires
            key = entry.keycode
            desc = entry.keydesc
        else:
            mod = 0
            key = 0
            desc = ""
        self.keys_edit.getModel().Text = desc
        self.set_current(mod, key)
    
    def replace_item(self, n, item, select=True):
        self.keys_list.removeItems(n, 1)
        self.keys_list.addItem(item, n)
        if select:
            self.keys_list.selectItemPos(n, True)
    
    def add_item(self, item, select=True):
        n = self.keys_list.getItemCount()
        self.keys_list.addItem(item, n)
        if select:
            self.keys_list.selectItemPos(n, True)
    
    def key_pressed(self, ev):
        mod = ev.Modifiers
        key = ev.KeyCode
        desc = self.get_key_desc(mod, key)
        self.set_key(desc)
        self.set_current(mod, key)
        #if key == 0:
        #   self.keys_list.getContext().getControl("btnAssign").setEnable(False)
    
    def get_key_desc(self, mod, key):
        name = self.keys.get(key, None)
        if name:
            sep = self.KEYS_SEP
            _desc = []
            if mod & SHIFT:
                _desc.append(self.SHIFT)
                _desc.append(sep)
            if mod & MOD1:
                _desc.append(self.MOD_1)
                _desc.append(sep)
            if mod & MOD2:
                _desc.append(self.MOD_2)
                _desc.append(sep)
            if mod & MOD3:
                _desc.append(self.MOD_3)
                _desc.append(sep)
            _desc.append(name[21:])
            return "".join(_desc)
        return ""
    
    def create_item(self, name, keydesc):
        _length1 = self.font.getStringWidth(name)
        _length2 = self.font.getStringWidth(keydesc)
        length = (self.width - _length1 - _length2 - self.MARGIN)
        if length < 10:
            length = 10
        return name + (" " * (length / self.space_width)) + keydesc
    
    def assign(self):
        n = self.get_selected()
        if n >= 0:
            mod = self._mod
            key = self._key
            desc = self.get_key_desc(mod, key)
            
            other = self._check_duplicated(mod, key)
            if other:
                if self.confirm(("%s is used. " % desc) + \
                    "Do you want to use it for this entry?", "Confirm") != 2:
                    return
            
            entry = self.entries[n]
            entry.modifires = mod
            entry.keycode = key
            entry.keydesc = desc
            
            if other:
                other.keycode = 0
                other.modifires = 0
                other.keydesc = ""
                pos = self.entries.index(other)
                item = self.create_item(other.name, other.keydesc)
                self.replace_item(pos, item, False)
            
            item = self.create_item(entry.name, entry.keydesc)
            self.replace_item(n, item)
    
    def _check_duplicated(self, mod, key):
        for entry in self.entries:
            if entry.eql(mod, key):
                return entry
        return None
    
    def confirm(self, message, title=""):
        """ Query to do something. """
        msgbox = self._message(title, message, "querybox", 3)
        n = msgbox.execute()
        msgbox.dispose()
        return n
    
    def _message(self, title, message, type, buttons):
        desktop = self._create_service("com.sun.star.frame.Desktop")
        frame = desktop.getActiveFrame()
        window = frame.getContainerWindow()
        toolkit = window.getToolkit()
        return toolkit.createMessageBox(
            window, Rectangle(), type, buttons, title, message)
    
    def delete(self):
        """ Delete shortcut key in the edit. """
        self.set_key("")
        self.set_current(0, 0)
        #self.keys_list.getContext().getControl("btnAssign").setEnable(True)
    
    def macros(self):
        """ Add macro entry. """
        macro = self.choose_macro()
        if macro:
            entry = KeyEntry("".join((self.MACRO, macro[0], self.FUNC_SEP, macro[1])), macro[2], 0, 0, "", 
                macro[0], macro[1])
            self.add_entry(entry)
            self.keys_edit.setFocus()
    
    def choose_macro(self):
        if self.macros_dlg is None:
            dlg = self._create_dialog(self.MACROS_DIALOG)
            self.macros_dlg = dlg
            dc = dlg.getControl
            tree_macros = dc("treeMacros")
            tree_macros_model = tree_macros.getModel()
            data_model = tree_macros_model.DataModel
            if data_model is None:
                data_model = self._create_service(
                    "com.sun.star.awt.tree.MutableTreeDataModel")
                tree_macros_model.DataModel = data_model
            
            root = data_model.createNode(self.ROOT, False)
            data_model.setRoot(root)
            
            tree_macros_model.SelectionType = 1
            for name in self._macros.get_macro_names():
                node = data_model.createNode(os.path.basename(name), True)
                node.DataValue = name
                root.appendChild(node)
            
            tree_macros_model.RootDisplayed = True
            tree_macros_model.RootDisplayed = False
            tree_macros.addTreeExpansionListener(TreeExpansionListener(self))
            tree_macros.addSelectionChangeListener(SelectionChangeListener(self))
            
        if self.macros_dlg.execute():
            tree_macros = self.macros_dlg.getControl("treeMacros")
            selection = tree_macros.getSelection()
            if selection:
                file_name = selection.getParent().DataValue
                item = selection.DataValue
            return file_name, item[0], item[1] # name, title
        return None
    
    def request_nodes(self, ev):
        node = ev.Node
        if node and node.getChildCount() == 0:
            parent = node.getParent()
            if parent and parent.getDisplayValue() != self.ROOT:
                return
            file_name = node.DataValue
            items = self._macros.get_functions(file_name)
            if items:
                tree_macros = ev.Source
                tree_macros_model = tree_macros.getModel()
                data_model = tree_macros_model.DataModel
                
                for item in items:
                    if item:
                        _node = data_model.createNode(item[1], False)
                        _node.DataValue = tuple(item)
                        node.appendChild(_node)
    
    def selection_changed(self, ev):
        tree_macros = ev.Source
        selection = tree_macros.getSelection()
        if selection:
            state = False
            desc = ""
            parent = selection.getParent()
            if parent and parent.getDisplayValue() != self.ROOT:
                state = True
                desc = selection.DataValue[2]
                if desc is None: desc = ""
            btn_ok = tree_macros.getContext().getControl("btnOk")
            btn_ok.setEnable(state)
            label_desc = tree_macros.getContext().getControl("labelDescription")
            label_desc.setText(desc)
    
    def default(self):
        n = self.get_selected()
        if n >= 0:
            keys = default_keys
            entry = self.entries[n]
            command = entry.command
            if not command.startswith(self.MACRO):
                found = None
                for key in keys:
                    if command == key[0]:
                        found = key
                        break
                if found:
                    self.set_current(key[1], key[2])
                    self.set_key(self.get_key_desc(key[1], key[2]))
    
    def add(self):
        commands = _commands
        names = list(commands.values())
        names.sort()
        dlg = self._create_dialog(self.COMMANDS_DIALOG)
        list_names = dlg.getControl("listCommands")
        list_names.addItems(tuple(names), 0)
        list_names.selectItemPos(0, True)
        
        if dlg.execute():
            items = list_names.getSelectedItems()
            if len(items) > 0:
                pairs = {}
                for key, value in commands.items():
                    pairs[value] = key
                for item in items:
                    entry = KeyEntry(pairs[item], item, 0, 0, "")
                    self.add_entry(entry)
        dlg.dispose()
    
    def store(self):
        try:
            import cPickle as pickle
        except:
            import pickle as pickle
        n = len(default_keys)
        a = []
        for i, entry in enumerate(self.entries):
            if entry.macro_file or i >= n and entry.keycode == 0:
                continue
            a.append(entry.to_a())
        path = self.get_key_config_path()
        f = None
        try:
            f = open(path, "wb")
            pickle.dump(a, f, 2)
        except:
            pass
        if f: f.close()
        # update
        KeyConfigLoader(self.ctx).construct_keys(a)

