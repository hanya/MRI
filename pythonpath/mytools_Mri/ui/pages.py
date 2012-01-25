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

import re
from mytools_Mri.ui import tools
from com.sun.star.awt import Selection


class PagesBase(object):
    """ Keeps information controls. 
        Properties: 0, Methods: 1, Interfaces: 2, Services 3.
    """
    def __init__(self, active, ctrls, changer, tab):
        self.active = active
        self.ctrls = ctrls
        self.changer = changer
        self.tab = tab
        if tab:
            self.activate = self.activate_tab

    def get_active(self):
        return self.active
    
    def activate(self, index):
        if index == self.active: return
        self.ctrls[index].setVisible(True)
        self.ctrls[self.active].setVisible(False)
        self.active = index
        self.changer.getModel().SelectedItems = (index,)
    
    def activate_tab(self, index):
        if index == self.active: return
        self.active = index
        if hasattr(self.tab, "ActiveTabPageID"):
            self.tab.ActiveTabPageID = index +1
        else:
            self.tab.activateTab(index +1)
    
    def set_properties(self, index, names, values):
        pass
    
    def set_font(self, name, height):
        pass
    
    def get_selected(self, index=None):
        pass
    
    def get_current_line(self, index=None, r=None):
        pass
    
    def get_first_word(self, index=None):
        pass
    
    def get_tag(self, index=None):
        pass
    
    def search(self, search_text, index=None):
        pass
    

class Pages(PagesBase):
    """keeps controls and their switcher."""
    def __init__(self, active, ctrls, changer, tab):
        PagesBase.__init__(self, active, ctrls, changer, tab)
    
    def set_properties(self, index, names, values):
        self.ctrls[index].getModel().setPropertyValues(names, values)
    
    def set_font(self, name, height):
        for ctrl in self.ctrls:
            ctrl.getModel().FontName = name
            ctrl.getModel().FontHeight = height
    
    def get_text(self, index):
        return self.ctrls[index].getModel().getPropertyValue('Text')
    
    def set_text(self, index, text):
        if len(text) > 0xFFFF:
            self.ctrls[index].getModel().setPropertyValue('Text', text[0:64000])
        else:
            self.ctrls[index].getModel().setPropertyValue('Text', text)
    
    def __setitem__(self, index, text):
        if len(text) > 0xFFFF:
            raise Exception("Text overflow.")
        self.ctrls[index].getModel().setPropertyValue('Text', text)
    
    def __getitem__(self, index):
        return self.ctrls[index].getModel().getPropertyValue('Text')
    
    def select_current_sentence(self, index=None):
        if index is None: index = self.active
        edit = self.ctrls[index]
        r = edit.getSelection()
        target = edit.getText()
        start, end = tools.get_current_sentence(target, r.Min)
        if target[start:end].strip():
            r.Min = start
            r.Max = end
            edit.setSelection(r)
    
    def select_current_line(self, index=None):
        if index is None: index = self.active
        edit = self.ctrls[index]
        r = edit.getSelection()
        target = edit.getText()
        start, end = tools.get_current_line(target, r.Min)
        if target[start:end].strip():
            r.Min = start
            r.Max = end
            edit.setSelection(r)
    
    def select_pos(self, selection=None, index=None, 
                    pos_min=None, pos_max=None, match=None):
        if index is None: index = self.active
        if selection is None and (pos_min is not None and pos_max is not None):
            selection = Selection(pos_min, pos_max)
        elif match:
            selection = Selection(match.start(), match.end())
        else: return
        self.ctrls[index].setSelection(selection)
    
    def get_selected(self, index=None):
        """get selected text."""
        if index is None: index = self.active
        return self.ctrls[index].getSelectedText()
    
    def get_current_line(self, index=None, r=None):
        """get current line."""
        if index is None: index = self.active
        edit = self.ctrls[index]
        if r is None:
            r = edit.getSelection()
        target = edit.getText()
        start, end = tools.get_current_line(target, r.Min)
        return target[start:end]
    
    def get_first_word(self, index=None):
        """get first word from current line."""
        if index is None: index = self.active
        line = self.get_current_line(index)
        return tools.get_first_word(line)
    
    def get_tag(self, index=None):
        """find (X) tag."""
        if index is None: index = self.active
        target = self.get_text(index)
        line = self.get_current_line(index)
        r = self.ctrls[index].getSelection()
        
        ret = None
        regindx = re.compile("^\(([^\)]*?)\)")
        if not regindx.search(line):
            start, end = tools.get_current_line(target, r.Min)
            match = regindx.match(target[start:end])
            while not match and start > 0:
                start, end = tools.get_current_line(target, start -1)
                match = regindx.match(target[start:end])
            if match:
                ret = match.group(1)
        return ret
    
    def search(self, search_text, index=None):
        if not search_text: return
        if index is None: index = self.active
        
        edit = self.ctrls[index]
        txt = edit.getText()
        r = edit.getSelection()
        
        try:
            result = self.regexp_search(txt, search_text, r.Max)
        except Exception, e:
            raise e
        if result:
            self.select_pos(index=index, match=result)
        else:
            # search from start position
            result = self.regexp_search(txt, search_text, 0)
            if result: self.select_pos(index=index, match=result)
    
    def regexp_search(self, txt, search_text, start):
        return re.compile(search_text, re.I).search(txt, start)


class PageStatus(object):
    """ Manages update status of pages. """
    def __init__(self, ctrls):
        self.update_status = [False for i in range(len(self.ctrls))]
    
    def set_status(self, txt):
        self.satus.setText(txt)
        self.satus.getModel().HelpText = txt
    
    def reset(self):
        """reset page states."""
        pass
    
    def update(self, index, txt):
        self[index] = txt
        self.update_status[index] = True
    
    def is_updated(self, index):
        return self.update_status[index]
    
    def set_updated(self, index, state=True):
        self.update_status[index] = state


class Ui(object):
    """ Manages ui controls. """
    def __init__(self, code, status):
        self.code = code
        self.satus = status
    
    def set_ui_controls(self, type_ctrl, imple_name_ctrl, btn_index, btn_name, edit_search, list_history):
        self.type_ctrl = type_ctrl
        self.imple_ctrl = imple_name_ctrl
        self.btn_index = btn_index
        self.btn_name = btn_name
        self.edit_search = edit_search
        self.list_history = list_history
    
    def set_history_index(self, n):
        self.list_history.getModel().SelectedItems = (n,)
    
    def get_history_selected(self):
        return self.list_history.getSelectedItemPos()
    
    def get_history_count(self):
        return self.list_history.getItemCount()
    
    def insert_history(self, n, name, select=True):
        list_hist = self.list_history.getModel()
        names = list_hist.StringItemList
        if isinstance(names, tuple):
            names = list(names)
        else:
            names = []
        names.insert(n, name)
        list_hist.StringItemList = tuple(names)
        if select:
            self.set_history_index(n)
    
    def get_search_string(self):
        return self.edit_search.getText()
    
    def get_type_name(self):
        return self.type_ctrl.getText()
    
    def set_type_name(self, name):
        self.type_ctrl.setText(name)
    
    def get_imple_name(self):
        return self.imple_ctrl.getText()
    
    def set_imple_name(self, name):
        self.imple_ctrl.setText(name)
    
    def get_code(self):
        return self.code.getText()
    
    def set_code(self, txt):
        self.code.setText(txt)
    
    def set_font(self, name, height):
        self.code.getModel().FontName = name
        self.code.getModel().FontHeight = height
    
    def enable_index_button(self, state):
        self.btn_index.setEnable(state)
    
    def enable_name_button(self, state):
        self.btn_name.setEnable(state)
    
    def set_index_button_state(self, state):
        self.btn_index.getModel().State = state
    
    def set_name_button_state(self, state):
        self.btn_name.getModel().State = state


class InfoUi(Ui, Pages, PageStatus):
    """UI for text edit control."""
    def __init__(self, active, ctrls, changer, code, status, scrolls, tab, *args):
        Ui.__init__(self, code, status)
        Pages.__init__(self, active, ctrls, changer, tab)
        PageStatus.__init__(self, ctrls)
    
    def set_font(self, name, height):
        Pages.set_font(self, name, height)
        Ui.set_font(self, name, height)
    
    def reset(self):
        """reset page states."""
        for i in range(len(self.ctrls)):
            self[i] = ''
        self.update_status = [False for i in range(len(self.ctrls))]

