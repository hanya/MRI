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

import uno
import sys
import traceback
import types
import operator
import threading

import mytools_Mri
import mytools_Mri.ui.frame
import mytools_Mri.ui.listeners
import mytools_Mri.ui.dialogs
import mytools_Mri.values
from mytools_Mri.ui import info
from mytools_Mri.unovalues import TypeClass

class MRIUi(info.ExtendedInfo):
    """User Interface for MRI based on css.awt toolkit."""
    
    def __init__(self, ctx, main):
        """Initialize UI with engine."""
        info.ExtendedInfo.__init__(self, main.engine, main.config)
        self.ctx = ctx
        self.main = main
        smgr = ctx.getServiceManager()
        self.desktop = smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", ctx)
        self.listeners = {}
        self.property_mode = True
        self.tree = None
        self.dlgs = mytools_Mri.ui.dialogs.Dialogs(ctx, smgr, self)
        self.status_eraser = None
        try:
            mytools_Mri.ui.frame.create_frame(self, ctx, smgr, 
                self.config, self.config.grid, self.config.use_tab)
            mytools_Mri.ui.listeners.set_listeners(
                self, self.config.grid, self.config.use_tab)
        except Exception as e:
            print(e)
            traceback.print_exc()
        self._init_ui()
    
    def _init_ui(self):
        """ Initialize with UI settings. """
        config = self.config
        self.pages.set_font(config.font_name, config.char_size)
    
    def message(self, message, title=''):
        """ Shows message. """
        self.dlgs.dialog_info(message, title)
    
    def error(self, message, title='Error'):
        """ Shows error message. """
        self.message(message, title)
    
    def status(self, message=''):
        """ Show status text. """
        self.pages.set_status(message)
        if message:
            if self.status_eraser:
                self.status_eraser.cancel()
            eraser = threading.Timer(5, self.status)
            eraser.start()
            self.status_eraser = eraser
    
    def entry_changed(self, history=False, update=True):
        """ Let update the view. """
        if history:
            entry = self.main.current
            name = "--%s" % entry.name
            n = self.main.history.get_history_index(entry)
            self.pages.insert_history(n, name)
            if self.tree:
                self.tree.add_entry(entry.get_parent(), entry, update)
        if update:
            self.reload_entry()
    
    def code_updated(self):
        """ Update code on the view. """
        self.pages.set_code(self.main.cg.get())
    
    def reload_entry(self):
        """ Rewrite information. """
        pages = self.pages
        index = pages.get_active()
        pages.reset()
        entry = self.main.current
        entry_type = entry.type
        type_class = entry_type.getTypeClass()
        if type_class == TypeClass.INTERFACE:
            try:
                pages.set_type_name(entry_type.getName())
                if entry_type.getName() in mytools_Mri.values.IGNORED_INTERFACES:
                    pass
                else:
                    pages.set_imple_name(self.engine.get_imple_name(entry))
                    pages.enable_index_button(
                        self.engine.has_interface2(self.main.current, 
                            'com.sun.star.container.XIndexAccess'))
                    pages.enable_name_button(
                        self.engine.has_interface2(self.main.current, 
                            'com.sun.star.container.XNameAccess'))
            except Exception as e:
                print(("Exception: reload_entry INTERFACE\n%s" + str(e)))
                traceback.print_exc()
        elif type_class == TypeClass.STRUCT or \
                type_class == TypeClass.SEQUENCE:
            pages.set_updated(1)
            pages.set_updated(2)    
            pages.enable_index_button(False)
            pages.enable_name_button(False)
            type_name = entry.type.Name
            pages.set_type_name(type_name)
            pages.set_imple_name('')
        
        try:
            self.update_info(index)
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.error("Error during to update: %s" % str(e))
    
    def update_info(self, index):
        """ Request to update specific view. """
        if self.pages.is_updated(index): return
        config = self.config
        entry = self.main.current
        entry_type = entry.type
        type_class = entry_type.getTypeClass()
        pages = self.pages
        if type_class == TypeClass.INTERFACE:
            if index == 0:
                pages[index] = self.get_properties_info(entry, config)
            elif index == 1:
                pages[index] = self.get_methods_info(entry, config)
            elif index == 2:
                pages[index] = self.get_interfaces_listeners_info(entry, config)
            elif index == 3:
                pages[index] = self.get_services_info(entry, config)
            pages.set_updated(index)
        elif type_class == TypeClass.STRUCT:
            if index == 0:
                pages[index] = self.get_struct_info(entry, config)
            elif index == 3:
                pages[index] = self.get_struct_name(entry, config)
            pages.set_updated(index)
        elif type_class == TypeClass.SEQUENCE:
            base_type = self.engine.get_component_base_type(entry.type)
            base_type_class = base_type.getTypeClass()
            if base_type_class == TypeClass.INTERFACE:
                if index == 0:
                    pages[index] = self.get_interface_sequence_info(entry, config)
            elif base_type_class == TypeClass.STRUCT:
                if index == 0:
                    try:
                        pages[index] = self.get_struct_sequence_info(entry, config)
                    except:
                        entry._overflow = True
                        pages[index] = "%s elements." % len(entry.target)
                elif index == 3:
                    pages[index] = self.get_struct_name(entry, config)
                pages.set_updated(index)
            else:
                if index == 0:
                    pages[index] = self.get_sequence_info(entry, config)
        else:
            raise Exception("Illegal type class: %s" % type_class)
    
    def category_changed(self, index=None):
        """ Change information category. """
        try:
            if index is None:
                index = self.pages.get_active()
            self.update_info(index)
            self.pages.activate(index)
        except Exception as e:
            print(e)
    
    def update_config(self):
        """ Request to update configuration. """
        self.main.update_config(store=True)
        self._init_ui()
    
    def try_index_access(self):
        """ Try to get an element though css.container.XIndexAccess. """
        if self.engine.has_interface2(self.main.current, 
                "com.sun.star.container.XIndexAccess"):
            self.info_action(category=1, word="getByIndex")
            self.pages.set_index_button_state(0)
        else:
            self.pages.enable_index_button(False)
    
    def try_name_access(self):
        """ Try to get an elemetn though css.container.XNameAccess. """
        if self.engine.has_interface2(self.main.current, 
                "com.sun.star.container.XNameAccess"):
            self.info_action(category=1, word="getByName")
            self.pages.set_name_button_state(0)
        else:
            self.pages.enable_name_button(False)
    
    def search_word(self):
        """ Start to search. """
        word = self.pages.get_search_string()
        if word:
            try:
                self.pages.search(word)
            except Exception as e:
                self.status(str(e))
    
    def show_history_tree(self, ev=None):
        """ Show the window of history tree. """
        if self.tree:
            self.tree._tree_frame.close(True)
            self.tree = None
        else:
            try:
                from mytools_Mri.ui import tree
                tree_frame = tree.create_tree_window(self, self.ctx, self.window, ev)
                self.tree = tree.HistoryTreeUi(self, tree_frame)
            except Exception as e:
                print(("Error: show_tree, " + str(e)))
                traceback.print_exc()
    
    def history_change(self, index, update_tree=True):
        """ Change to specific entry. """
        if self.main.change_history(index):
            self.main.change_history(index)
            if update_tree and self.tree:
                self.tree.set_selected(self.main.current)
        n = self.main.history.get_history_index(self.main.current)
        self.pages.set_history_index(n)
    
    def history_back(self):
        """ Go to previous entry. """
        n = self.pages.get_history_selected()
        if n > 0:
            parent = self.main.current.get_parent()
            m = self.main.history.get_history_index(parent)
            if m == -1:
                n -= 1
            else:
                n = m
            self.history_change(n)
    
    def history_forward(self):
        """ Go to next entry. """
        n = self.pages.get_history_selected()
        if n < self.pages.get_history_count() -1:
            if self.main.current.get_child_count():
                m = self.main.history.get_history_index(self.main.current.get_children()[0])
                if m == -1:
                    n += 1
                else:
                    n = m
            else:
                n += 1
            self.history_change(n)
    
    
    def info_action(self, category=None, word=''):
        """ To get/set property value or call method action on the UI. """
        if category is None:
            category = self.pages.get_active()
        if not word:
            word = self.pages.get_first_word()
        #print(category, word)
        if category == 0:
            entry = self.main.current
            type_class = entry.type.getTypeClass()
            if type_class == TypeClass.INTERFACE:
                if self.property_mode:
                    self.main.get_property_value(word)
                else:
                    try:
                        if self.main.set_property_value(word, 
                            get_value=self.make_single_value, get_args=self.get_arguments):
                            self.pages[0] = self.get_properties_info(entry, self.config)
                    except:
                        return
            elif type_class == TypeClass.STRUCT:
                if self.property_mode:
                    self.main.get_struct_element(word)
                else:
                    self.main.set_struct_element(word, value=None, get_value=self.make_single_value)
            elif type_class == TypeClass.SEQUENCE:
                base_type = self.engine.get_component_base_type(entry.type)
                base_tc = base_type.getTypeClass()
                if base_tc == TypeClass.INTERFACE:
                    length = len(entry.target)
                    if length > 0:
                        n = self.dlgs.dialog_select(tuple(range(length)))
                        if not n is None:
                            try:
                                self.main.manage_sequence(entry, int(n))
                            except Exception as e:
                                print(e)
                                traceback.print_exc()
                else:
                    if hasattr(entry, "_overflow"):
                        length = len(entry.target)
                        n = self.dlgs.dialog_select(tuple(range(length)))
                        if not n is None:
                            try:
                                self.main.manage_sequence(entry, int(n))
                            except Exception as e:
                                print(e)
                                traceback.print_exc()
                        return
                    tag = self.pages.get_tag()
                    if tag:
                        index = tag.split(',')
                        if False in [i.isdigit() for i in index]: return
                        if base_tc == TypeClass.STRUCT or base_tc == TypeClass.EXCEPTION or \
                           base_tc == TypeClass.SEQUENCE:
                            try:
                                self.get_field_from_struct_sequence(word, [int(i) for i in index])
                            except Exception as e:
                                print(e)
                                traceback.print_exc()
                        else:
                            try:
                                self.main.manage_sequence(entry, int(index[0]))
                            except Exception as e:
                                print(e)
                    else:
                        print("tag not found: " + str(n))
        elif category == 1:
            self.main.call_method(word, get_args=self.get_arguments)
    
    def get_field_from_struct_sequence(self, name, ids):
        """ Get value from sequence of struct. """
        for i in ids:
            self.main.manage_sequence(self.main.current, i)
        self.main.get_struct_element(name)
    
    def open_idl_reference(self, target='', word=''):
        """ Open reference. """
        if target:
            return self.main.web.open_idl_reference(target, word)
        try:
            n = self.pages.get_active()
            selected = self.pages.get_selected().strip()
            word = ""
            if n == 0:
                if len(selected) > 1 and selected.startswith('.'):
                    target = "com.sun.star%s" % selected
                else:
                    word = self.pages.get_first_word()
                    word, target = self.engine.find_declared_module(self.main.current, word)
            elif n == 1:
                if len(selected) > 4 and selected[0:4] == "com." :
                    target = selected
                elif len(selected) > 1 and selected[0] == '.':
                    target = "com.sun.star%s" % selected
                else:
                    word = self.pages.get_first_word()
                    d0, d1, target, d3 = self.engine.get_method_info(self.main.current, word)
            else:
                target = self.pages.get_current_line()
        
            self.main.web.open_idl_reference(target, word)
        except Exception as e:
            print(e)
    
    def execute_macro(self, file_name, func_name, context=None, *args):
        """ Try to execute macro. """
        ret = None
        self.main.set_mode(False)
        #_current = self.main.current
        try:
            fn = self.main.macros.get_function(file_name, func_name, context)
            ret = fn(self.main, *args)
            if isinstance(ret, types.GeneratorType):
                for parent, value in ret:
                    self.main.set_mode(True)
                    self.main.current = parent
                    self.main.action_by_type(value)
                    self.main.set_mode(False)
            #else:
            #   self.main.current = _current
        except Exception as e:
            print("Error at execute_macro")
            error = "".join((e.__class__.__name__, ": ", str(e), "\n\n", 
                "\n".join(traceback.format_tb(sys.exc_info()[2]))))
            self.error(error)
        self.main.set_mode(True)
        #self.main.current = _current
        self.reload_entry()
        self.code_updated()
        if self.tree:
            n = self.pages.get_history_selected()
            self.history_change(n)
        return None
    
    def get_interface_sequence_info(self, entry, config):
        """ Get text for sequence of interface. """
        length = len(entry.target)
        if length == 0:
            text = "no element."
        elif length == 1:
            text = "1 element."
        else:
            text = "%s elements." % length
        return text

