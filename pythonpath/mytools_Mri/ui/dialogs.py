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

import unohelper
import traceback

from com.sun.star.awt import XActionListener, XMouseListener, \
    XItemListener, Rectangle
from com.sun.star.view import XSelectionChangeListener

class InputButtonListener(unohelper.Base, XActionListener):
    def __init__(self,cast,idltarget='',word=''):
        self.cast = cast
        self.idltarget = idltarget
        self.word = word
    
    def set_target(self, idltarget, word):
        self.idltarget = idltarget
        self.word = word
    
    def disposing(self,ev):
        pass
    
    def actionPerformed(self,actionEvent):
        cmd = str(actionEvent.ActionCommand)
        if cmd == 'idlref':
            self.cast.open_idl_reference(self.idltarget, self.word)


class SelectListListener(unohelper.Base, XMouseListener):
    def __init__(self,cast):
        self.cast = cast
    def disposing(self,ev):
        pass
    def mouseReleased(self,ev):
        pass
    def mouseEntered(self,ev):
        pass
    def mouseExited(self,ev):
        pass
    def mousePressed(self,ev):
        if ev.ClickCount == 2:
            self.cast.endDialog(1)


class DialogBase(object):
    
    DISPOSE = True
    
    POSSIZE = 0,0,0,0
    HELP_URL = ""
    
    def __init__(self, ctx, cast, *args):
        self.ctx = ctx
        self.cast = cast
        self._dialog = self._create_dialog(*self.POSSIZE, help_url=self.HELP_URL)
        self._create()
    
    def execute(self):
        toolkit = self.ctx.getServiceManager().createInstanceWithContext( 
                "com.sun.star.awt.Toolkit", self.ctx)
        self._dialog.createPeer(toolkit, None)
        #self._dialog.setVisible(True)
        self._prepare()
        
        n = self._dialog.execute()
        ret = self._done(n)
        if self.DISPOSE:
            self._destruct()
            self._dialog.dispose()
        return ret
    
    def _create(self): pass
    def _destruct(self): pass
    def _prepare(self): pass
    def _done(self, n):
        return n
    
    def _create_service(self, name):
        return self.ctx.getServiceManager().createInstanceWithContext(name, self.ctx)
    
    # create control functions 
    
    def _create_dialog(self, x, y, width, height, help_url):
        smgr = self.ctx.getServiceManager()
        dialog = smgr.createInstanceWithContext( 
                'com.sun.star.awt.UnoControlDialog', self.ctx)
        dialog_model = smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialogModel', self.ctx)
        dialog_model.setPropertyValues( 
            ('Height','HelpURL','PositionX','PositionY','Width',), 
            (height, help_url, x, y, width,) )
        dialog.setModel(dialog_model)
        #dialog.setVisible(False)
        #dialog.createPeer(toolkit, None)
        dialog.setVisible(False)
        self._dialog = dialog
        return dialog
    
    def set_title(self, title):
        self._dialog.setTitle(title)
    
    def add_control(self, _type, name, x, y, width, height, names=None, props=None):
        model = self._dialog.getModel().createInstance(_type)
        model.setPropertyValues(
                ("Height", "PositionX", "PositionY", "Width"), 
                (height, x, y, width))
        if names and props:
            model.setPropertyValues(names, props)
        self._dialog.getModel().insertByName(name, model)
        return model
    
    def add_edit(self, name, x, y, width, height, names=None, props=None):
        return self.add_control("com.sun.star.awt.UnoControlEditModel", 
                        name, x, y, width, height, names, props)
    
    def add_label(self, name, x, y, width, height, names=None, props=None):
        return self.add_control("com.sun.star.awt.UnoControlFixedTextModel", 
                        name, x, y, width, height, names, props)
    
    def add_button(self, name, x, y, width, height, names=None, props=None, command=None):
        model = self.add_control("com.sun.star.awt.UnoControlButtonModel", 
                        name, x, y, width, height, names, props)
        if command:
            self.get_control(name).setActionCommand(command)
        return model
    
    def add_check(self, name, x, y, width, height, names=None, props=None):
        return self.add_control("com.sun.star.awt.UnoControlCheckBoxModel", 
                        name, x, y, width, height, names, props)
    
    def add_list(self, name, x, y, width, height, names=None, props=None):
        return self.add_control("com.sun.star.awt.UnoControlListBoxModel", 
                        name, x, y, width, height, names, props)
    
    def add_line(self, name, x, y, width, height, names=None, props=None):
        return self.add_control("com.sun.star.awt.UnoControlFixedLineModel", 
                        name, x, y, width, height, names, props)
    
    def add_ok(self, name, x, y, width, height):
        return self.add_button(name, x, y, width, height, 
            ("DefaultButton", "Label", "PushButtonType"), (True, "~OK", 1))
    
    def add_cancel(self, name, x, y, width, height):
        return self.add_button(name, x, y, width, height, 
            ("Label", "PushButtonType"), ("~Cancel", 2))
    
    def add_tree(self, name, x, y, width, height, names=None, props=None):
        return self.add_control("com.sun.star.awt.tree.TreeControlModel", 
                        name, x, y, width, height, names, props)
    
    def get_control(self, name):
        return self._dialog.getControl(name)
    
    def get_control_model(self, name):
        return self._dialog.getModel().getByName(name)
    
    def set_dialog_height(self, height):
        self._dialog.getModel().Height = height
    
    # set/get value to/from a control
    
    def set_y(self, name, y):
        self.get_control_model(name).PositionY = y
    
    def set_label(self, name, label):
        self.get_control_model(name).Label = label
    
    def set_text(self, name, text):
        self.get_control_model(name).Text = text
    
    def get_text(self, name):
        return self.get_control_model(name).Text
    
    def set_text_selection(self, name, r):
        self.get_control(name).setSelection(r)
    
    def is_checked(self, name):
        return self.get_control_model(name).State == 1
    
    ## list
    
    def add_items(self, name, index, items):
        _items = tuple(items) if isinstance(items, list) else items
        self.get_control(name).addItems(_items, index)
    
    def get_item_count(self, name):
        return self.get_control(name).getItemCount()
    
    def select_item_pos(self, name, index, state=True):
        self.get_control(name).selectItemPos(index, state)
    
    def get_selected_item(self, name):
        return self.get_control(name).getSelectedItem()
    
    def get_selected_item_pos(self, name):
        return self.get_control(name).getSelectedItemPos()
    
    # misc
    
    def set_visible(self, name, state=True):
        self.get_control(name).setVisible(state)
    
    def set_enable(self, name, state=True):
        self.get_control(name).setEnable(state)
    
    def set_focus(self, name):
        return self.get_control(name).setFocus()
    
    def create_tree_data_model(self):
        return self._create_service("com.sun.star.awt.tree.MutableTreeDataModel")
    


class InfoDialog(DialogBase):
    
    DISPOSE = False
    
    POSSIZE = 30, 50, 176, 136
    HELP_URL = "mytools.Mri:d_info"
    
    def _create(self):
        self.add_edit("edit", 2, 1, 172, 110, 
                ('HelpURL','HideInactiveSelection','HScroll','MultiLine', 'VScroll',), 
                ('mytools.Mri:d_info_edit',False,True,True, True,))
        self.add_button("btn", 130, 117, 43, 16, 
                ('DefaultButton', 'HelpURL','Label', 'PushButtonType'), 
                (True, 'mytools.Mri:d_info_btn','~close', 2))
        self.add_label("label", 5, 115, 123, 23, 
                ("FontHeight",), 
                (9,))
    
    def _prepare(self):
        self.set_focus("btn")
    
    def execute(self, value, label=""):
        self.set_text("edit", value)
        self.set_label("label", label)
        return DialogBase.execute(self)


class SelectDialog(DialogBase):
    
    POSSIZE = 30, 50, 150, 150
    HELP_URL = 'mytools.Mri:d_select'
    
    def _create(self):
        self.add_list("list", 2, 2, 146, 130)
        self.add_cancel("cbtn", 82, 134, 36, 14)
        self.add_ok("obtn", 42, 134, 36, 14)
        self.get_control("list").addMouseListener(SelectListListener(self._dialog))
    
    def _prepare(self):
        if self.get_item_count("list"):
            self.select_item_pos("list", 0, True)
    
    def execute(self, itemtuple, title="", index=False):
        if isinstance(itemtuple, tuple) or isinstance(itemtuple, list):
            self.add_items("list", 0, itemtuple)
        
        if self.get_item_count("list") <= 0:
            self.set_enable("obtn", False)
        self._index = index
        return DialogBase.execute(self)
    
    def _done(self, n):
        if n:
            if self._index:
                return self.get_selected_item_pos("list")
            else:
                return self.get_selected_item("list")
        else:
            return None


class InputDialog(DialogBase):
    
    POSSIZE = 30, 50, 177, 65
    HELP_URL = "mytools.Mri:d_input"
    
    def _create(self):
        self.add_line("line", 4, 1, 170, 12)
        self.add_cancel("cbtn", 142, 48, 29, 14)
        self.add_ok("obtn", 142, 32, 29, 14)
        self.add_edit("edit", 2, 15, 171, 13, ("MultiLine",), (False,))
        self.add_label("label", 2, 30, 130, 8, ("FontHeight", "MultiLine"), (8, True))
        self._selection = None
    
    def _prepare(self):
        self.set_focus("edit")
        if self._selection:
            from com.sun.star.awt import Selection
            self.set_text_selection("edit", Selection(0, self._selection))
    
    def execute(self, label="", txt="", init="", select=True):
        self.set_label("line", label)
        self.set_label("label", txt)
        self.set_text("edit", init)
        if init and select:
            self._selection = len(init)
        return DialogBase.execute(self)
    
    def _done(self, n):
        return (self.get_text("edit") if n else ""), n


class InputDialog2(InputDialog):
    
    POSSIZE = 30, 50, 177, 81
    
    def _create(self):
        self.add_line("line", 4, 1, 170, 12)
        self.add_cancel("cbtn", 142, 48, 29, 14)
        self.add_ok("obtn", 142, 32, 29, 14)
        self.add_edit("edit", 2, 15, 171, 13, ("MultiLine",), (False,))
        self.add_label("label", 2, 30, 135, 8, ("FontHeight", "MultiLine"), (8, True))
        self.add_button("ibtn", 142, 64, 29, 14, ("Label", "PushButtonType"), ("~Ref.", 0), command="idlref")
        self._button_listener = InputButtonListener(self.cast)
        self.get_control("ibtn").addActionListener(self._button_listener)
        self._selection = None
    
    def execute(self, label="", txt="", init="", dclass="", word="", select=True):
        self.set_label("line", label)
        self.set_label("label", txt)
        self.set_text("edit", init)
        self._button_listener.set_target(dclass, word)
        if init and select:
            self._selection = len(init)
        return DialogBase.execute(self)


class ElementalInputDialog(InputDialog):
    
    POSSIZE = 30, 50, 177, 67
    FROM_HISTORY = {"INTERFACE", "STRUCT", "EXCEPTION", "SEQUENCE"}
    
    class Result:
        def __init__(self, type_name, value=None, value_type=None):
            self.type_name = type_name
            self.value = value
            self.value_type = value_type
    
    class ListenerBase(unohelper.Base):
        def __init__(self, act):
            self.act = act
        def disposing(self, ev):
            self.act = None
    
    class ButtonListener(ListenerBase, XActionListener):
        def actionPerformed(self, ev):
            try:
                self.act.button_pushed(ev)
            except Exception as e:
                print(e)
                traceback.print_exc()
    
    class TreeSelectionListener(ListenerBase, XSelectionChangeListener):
        def selectionChanged(self, ev):
            ev.Source.getContext().getControl("btnOk").setEnable(
                    self.act.tree_selection_changed())
    
    class ItemListener(ListenerBase, XItemListener):
        def itemStateChanged(self, ev):
            self.act.void_check_changed(ev.Selected == 1)
    
    def _create(self):
        self.add_line("line", 4, 1, 170, 12)
        self.add_ok("obtn", 142, 0, 29, 14)
        self.add_cancel("cbtn", 142, 0, 29, 14)
        self.add_button("ibtn", 142, 0, 29, 14, ("Label",), ("~Ref.",), "idlref")
        self.add_edit("label", 2, 0, 135, 48, ("FontHeight", "MultiLine"), (8, True))
        self._button_listener = InputButtonListener(self.cast)
        self.get_control("ibtn").addActionListener(self._button_listener)
    
    def _prepare(self):
        self.set_focus("edit_0")
    
    def execute(self, elements, label="", txt="", doc=("", "")):
        self._results = []
        self.set_dialog_height(67 + len(elements) * 27)
        self.set_label("line", label)
        self.set_text("label", txt)
        self._button_listener.set_target(*doc)
        # add and rearrange controls
        from com.sun.star.style.VerticalAlignment import BOTTOM as VA_BOTTOM
        listener = self.__class__.ButtonListener(self)
        y = 14
        complex_types = self.FROM_HISTORY | {"ANY"}
        for i, element in enumerate(elements):
            is_complex = element[1] in complex_types
            self.add_label("label_%s" % i, 4, y, 170, 12, 
                ("Label", "NoLabel", "VerticalAlign"), (element[0], True, VA_BOTTOM))
            self.add_edit("edit_%s" % i, 2, y + 13, (130 if is_complex else 171), 13, 
                ("MultiLine",), (False,))
            if is_complex:
                if element[1] != "ANY":
                    self.set_enable("edit_%s" % i, False)
                self.add_button("btn_%s" % i, 133, y + 13, 40, 13, ("Label",), ("...",), str(i))
                self.get_control("btn_%s" % i).addActionListener(listener)
            self._results.append(self.Result(element[1]))
            y += 27
        y += 3
        self.set_y("obtn", y)
        self.set_y("cbtn", y + 15)
        self.set_y("ibtn", y + 30)
        self.set_y("label", y)
        self._history_selector = None
        return DialogBase.execute(self)
    
    def void_check_changed(self, state):
        self._history_selector.enable_ok_button(
            state or self._history_selector.is_tree_selection_valid())
    
    def tree_selection_changed(self):
        return self._history_selector.is_tree_selection_valid()
    
    def button_pushed(self, ev):
        control = ev.Source
        n = int(ev.ActionCommand)
        type_name = self._results[n].type_name
        with_type = False
        if type_name == "ANY":
            with_type = True
            from mytools_Mri.ui.tools import create_popupmenu
            entries = ((1, 0, 0, "void", "VOID", None), 
                       (2, 1, 0, "boolean", "BOOLEAN", None), 
                       (3, 2, 0, "byte", "BYTE", None), 
                       (4, 3, 0, "short", "SHORT", None), 
                       (5, 4, 0, "unsigned short", "UNSIGNED_SHORT", None), 
                       (6, 5, 0, "long", "LONG", None), 
                       (7, 6, 0, "unsigned long", "UNSIGNED_LONG", None), 
                       (8, 7, 0, "hyper", "HYPER", None), 
                       (9, 8, 0, "unsigned hyper", "UNSIGNED_HYPER", None), 
                       (10, 9, 0, "float", "FLOAT", None), 
                       (11, 10, 0, "double", "DOUBLE", None), 
                       (12, 11, 0, "string", "STRING", None), 
                       (13, 12, 0, "type", "TYPE", None), 
                       (14, 13, 0, "enum", "ENUM", None), 
                       (None, 14, 0, "", "", None), 
                       (15, 15, 0, "struct", "STRUCT", None), 
                       (16, 16, 0, "exception", "EXCEPTION", None), 
                       (17, 17, 0, "sequence", "SEQUENCE", None), 
                       (18, 18, 0, "interface", "INTERFACE", None))
            popup = create_popupmenu(self.ctx, entries)
            r = popup.execute(ev.Source.getPeer(), Rectangle(0, ev.Source.getPosSize().Height, 0, 0), 0)
            if r == 0: return
            value_type_name = popup.getCommand(r)
            control.setLabel(popup.getItemText(r))
            if value_type_name in self.FROM_HISTORY:
                self.set_enable("edit_%s" % n, False)
            else:
                self.set_enable("edit_%s" % n, True)
                self._results[n].value_type = value_type_name
                return
        obj = None
        try:
            self._history_selector = HistorySelectorDialog(self.ctx, self.cast)
            obj = self._history_selector.execute(
                        "History", self.TreeSelectionListener(self), 
                        allow_void=True, void_listener=self.ItemListener(self))
            self._history_selector = None
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            if obj is None:
                return
        name = "edit_%s" % n
        if obj == "void":
            self.set_text(name, "void")
            self._results[n].value = None
            self._results[n].value_type = "VOID"
        elif obj:
            self.set_text(name, str(obj))
            self._results[n].value = obj
            self._results[n].value_type = value_type_name if with_type else type_name
    
    def _done(self, n):
        if n:
            for i, result in enumerate(self._results):
                if result.type_name in self.FROM_HISTORY or result.value_type == "ANY":
                    pass
                else:
                    result.value = self.get_text("edit_%s" % i)
        return n, self._results


class HistorySelectorDialog(DialogBase):
    
    POSSIZE = 30, 50, 180, 140
    
    def _create(self):
        class Wrapper(unohelper.Base):
            def __init__(self, obj):
                self.obj = obj
        
        self.add_label("labelHistory", 5, 3, 96, 12, ("Label",), ("History",))
        self.add_ok("btnOk", 134, 4, 43, 14)
        self.add_cancel("btnCancel", 134, 24, 43, 14)
        self.add_check("checkVoid", 134, 50, 43, 14, ("Label",), ("~void",))
        data_model = self.create_tree_data_model()
        self.add_tree("treeHistory", 3, 18, 127, 117, 
            ("DataModel", "SelectionType", "RootDisplayed"), 
            (data_model, 1, True))
        
        child = self.cast.main.history.get_children()[0]
        def create_node(parent, entry):
            for i in entry.children:
                node = data_model.createNode(i.name, False)
                parent.appendChild(node)
                node.DataValue = Wrapper(i)
                if i.get_child_count() > 0:
                    create_node(node, i)
        root = data_model.createNode(child.name, False)
        root.DataValue = Wrapper(child)
        create_node(root, child)
        data_model.setRoot(root)
    
    def _prepare(self):
        root = self.get_control_model("treeHistory").DataModel.getRoot()
        if root.getChildCount() > 0:
            self.get_control("treeHistory").makeNodeVisible(root.getChildAt(0))
    
    def execute(self, title="", listener=None, allow_void=False, void_listener=None):
        if listener:
            self.get_control("treeHistory").addSelectionChangeListener(listener)
        self.set_enable("btnOk", False)
        self.set_title(title)
        self.set_visible("checkVoid", allow_void)
        if void_listener:
            self.get_control("checkVoid").addItemListener(void_listener)
        return DialogBase.execute(self)
    
    def _done(self, n):
        if n:
            if self.is_checked("checkVoid"):
                return "void"
            else:
                selected = self.get_control("treeHistory").getSelection()
                if selected:
                    return selected.DataValue.obj
        else:
            return None
    
    def enable_ok_button(self, state):
        self.set_enable("btnOk", state)
    
    def is_tree_selection_valid(self):
        tree = self.get_control("treeHistory")
        state = False
        selected = tree.getSelection()
        if selected:
            state = selected != tree.getModel().DataModel.getRoot()
        return state


class Dialogs(object):
    """ Provides dialogs. """
    
    def __init__(self,ctx,smgr,cast):
        self.ctx = ctx
        self.smgr = smgr
        self.cast = cast
        self.dlg_info = None
    
    def dialog_info(self, value, label=''):
        """ Shows value as a message with label. """
        if not self.dlg_info:
            self.dlg_info = InfoDialog(self.ctx, self.cast)
        return self.dlg_info.execute(value, label)
    
    def dialog_select(self, itemtuple, title='', index=False):
        """ Let user select an entry from items. """
        return SelectDialog(self.ctx, self.cast).execute(itemtuple, title, index)
    
    def dialog_input(self, label='', txt='', init=''):
        """ Input dialog. """
        return InputDialog(self.ctx, self.cast).execute(label, txt, init)
    
    def dialog_input2(self,label='',txt='',init='',dclass='',word=''):
        """ Input dialog 2. """
        return InputDialog2(self.ctx, self.cast).execute(label, txt, init, dclass, word)
    
    def dialog_elemental_input(self, elements, label='', txt='', doc=('', '')):
        return ElementalInputDialog(self.ctx, self.cast).execute(elements, label, txt, doc)
    
    def message(self, message, title="", type="messbox", buttons=1):
        """ Message box, see css.awt.XMessageBoxFactory. """
        import mytools_Mri.tools
        
        desktop = self.smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.ctx)
        frame = desktop.getActiveFrame()
        window = frame.getContainerWindow()
        if mytools_Mri.tools.check_method_parameter(
            self.ctx, "com.sun.star.awt.XMessageBoxFactory", 
            "createMessageBox", 1, "com.sun.star.awt.Rectangle"):
            msgbox = window.getToolkit().createMessageBox(
                window, Rectangle(), type, buttons, title, message)
        else:
            import uno
            _type = uno.Enum("com.sun.star.awt.MessageBoxType", 
                            {"messbox": "MESSAGEBOX", "infobox": "INFOBOX", 
                             "warningbox": "WARNINGBOX", "errorbox": "ERRORBOX", 
                             "querybox": "QUERYBOX"}[type])
            msgbox = window.getToolkit().createMessageBox(
                window, _type, buttons, title, message)
        n = msgbox.execute()
        msgbox.dispose()
        return n
    
    
    def history_selector(self, title="", listener=None):
        """ Select an entry from history. """
        return HistorySelectorDialog(self.ctx, self.cast).execute(title, listener)
    
    def _create_file_dialog(self, title, default_name, display_dir, filters, default_filter, template):
        fp = self.smgr.createInstanceWithContext("com.sun.star.ui.dialogs.FilePicker", self.ctx)
        fp.initialize((template,))
        fp.setTitle(title)
        fp.setDefaultName(default_name)
        if display_dir:
            fp.setDisplayDirectory(display_dir)
        for name, f in filters:
            fp.appendFilter(name, f)
        if default_filter:
            fp.setCurrentFilter(filters[default_filter])
        return fp
    
    def dialog_open(self, title="", default_name="", display_dir="", filters=(('All Files (*.*)', '*.*'),), default_filter=0, multiple=False, template=0):
        fp = self._create_file_dialog(title, default_name, display_dir, filters, default_filter, template)
        fp.setMultiSelectionMode(multiple)
        
        ret = None
        if fp.execute() == 1:
            files = fp.getFiles()
            if multiple:
                dir_url = files[0]
                if not dir_url.endswith("/"):
                    dir_url += "/"
                ret = [dir_url + name for name in files[1:]]
            else:
                ret = files[0]
        fp.dispose()
        return ret
    
    def dialog_save(self, title="", default_name="", display_dir="", filters=(('All Files (*.*)', '*.*'),), default_filter=0, template=1):
        fp = self._create_file_dialog(title, default_name, display_dir, filters, default_filter, template)
        ret = None
        if fp.execute() == 1:
            ret = fp.getFiles()[0]
        fp.dispose()
        return ret
    
    def directory_choose(self, title="", description="", directory=""):
        fp = self.smgr.createInstanceWithContext("com.sun.star.ui.dialogs.FolderPicker", self.ctx)
        fp.setTitle(title)
        fp.setDescription(description)
        if directory:
            fp.setDisplayDirectory(directory)
        ret = None
        if fp.execute() == 1:
            ret = fp.getDirectory()
        fp.dispose()
        return ret

