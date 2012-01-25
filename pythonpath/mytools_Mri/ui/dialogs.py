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

from com.sun.star.awt import XActionListener, XMouseListener, \
    Rectangle


class InputButtonListener(unohelper.Base, XActionListener):
    def __init__(self,cast,idltarget='',word=''):
        self.cast = cast
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
            accBtn = self.cast.getControl('obtn').getAccessibleContext()
            if accBtn.getAccessibleActionCount() > 0:
                # push OK
                accBtn.doAccessibleAction(0)
            # after 3.3
            # self.cast.endDialog(1)


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
            dialog = self.smgr.createInstanceWithContext( 
                'com.sun.star.awt.UnoControlDialog',self.ctx)
            dialog_model = self.smgr.createInstanceWithContext( 
                'com.sun.star.awt.UnoControlDialogModel',self.ctx)
            dialog_model.setPropertyValues( 
                ('Height','HelpURL','PositionX','PositionY','Width',), 
                (136,'mytools.Mri:d_info',30,50,176,) )
            
            edit_model = dialog_model.createInstance( 
                'com.sun.star.awt.UnoControlEditModel')
            edit_model.setPropertyValues( 
                ('Height','HelpURL','HideInactiveSelection','HScroll','MultiLine',
                'PositionX','PositionY','VScroll','Width',), 
                (110,'mytools.Mri:d_info_edit',False,True,True,2,1,True,172,) )
            label_model = dialog_model.createInstance( 
                'com.sun.star.awt.UnoControlFixedTextModel')
            label_model.setPropertyValues( 
                ('FontHeight','Height','PositionX','PositionY','Width',), 
                (9,23,5,115,123,) )
            btn_model = dialog_model.createInstance( 
                'com.sun.star.awt.UnoControlButtonModel')
            btn_model.setPropertyValues( 
                ('DefaultButton','Height','HelpURL','Label','PositionX',
                'PositionY','PushButtonType','Width'), 
                (True,16,'mytools.Mri:d_info_btn','~close',130,117,2,43) )
        
            dialog_model.insertByName('edit',edit_model)
            dialog_model.insertByName('btn',btn_model)
            dialog_model.insertByName('label',label_model)
        
            dialog.setModel(dialog_model)
            dialog.setVisible(True)
            self.dlg_info = dialog
        else:
            dialog = self.dlg_info
            label_model = dialog.getModel().getByName('label')
            edit_model = dialog.getModel().getByName('edit')
        
        label_model.Label = label
        edit_model.Text = value
        dialog.getControl('btn').setFocus()
        
        return dialog.execute()
        #dialog.dispose() #dlg_info is reused, do not dispose it
    
    
    def dialog_select(self, itemtuple, title='', index=False):
        """ Let user select an entry from items. """
        dialog = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        dialog_model = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialogModel', self.ctx)
        dialog_model.setPropertyValues( 
            ('Height','HelpURL','PositionX','PositionY','Width',), 
            (120,'mytools.Mri:d_select',30,50,120,) )
        
        list_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlListBoxModel' )
        list_model.setPropertyValues( 
            ('Height','MultiSelection','PositionX','PositionY','Width',), 
            (100,False,2,2,116,) )
        cbtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel' )
        cbtn_model.setPropertyValues( 
            ('Height','Label','PositionX','PositionY','PushButtonType','Width',), 
            (14,'~cancel',82,104,2,36,) )
        obtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel' )
        obtn_model.setPropertyValues( 
            ('DefaultButton','Height','Label','PositionX',
            'PositionY','PushButtonType','Width',), 
            (True,14,'~OK',42,104,1,36,) )
        
        dialog_model.insertByName('list',list_model)
        dialog_model.insertByName('cbtn',cbtn_model)
        dialog_model.insertByName('obtn',obtn_model)
        
        dialog.setModel(dialog_model)
        dialog.setTitle(title)
        dialog.setVisible(True)
        
        list_ctl = dialog.getControl('list')
        if isinstance(itemtuple, tuple) or \
            isinstance(itemtuple, list):
            if isinstance(itemtuple, list):
                itemtuple = tuple(itemtuple)
            list_ctl.addItems(itemtuple,0)
        else:
            try:
                list_ctl.addItems(list(itemtuple),0)
            except:
                pass
        if list_ctl.getItemCount() > 0:
            list_ctl.selectItemPos(0,True)
        else:
            obtn_model.Enabled = False
        l = SelectListListener(dialog)
        list_ctl.addMouseListener(l)
        
        if dialog.execute():
            if index:
                selected = list_ctl.getSelectedItemPos()
            else:
                selected = list_ctl.getSelectedItem()
        else:
            selected = None
        dialog.setVisible(False)
        list_ctl.removeMouseListener(l)
        dialog.dispose()
        return selected
    
    
    def dialog_input(self, label='', txt='', init=''):
        """ Input dialog. """
        dialog = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialog',self.ctx)
        dialog_model = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialogModel',self.ctx)
        dialog_model.setPropertyValues( 
            ('Height','HelpURL','PositionX','PositionY','Width',), 
            (65,'mytools.Mri:d_input',30,50,177,) )
        
        line_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlFixedLineModel')
        line_model.setPropertyValues( 
            ('Height','PositionX','PositionY','Width',), 
            (12,4,1,170) )
        edit_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlEditModel')
        edit_model.setPropertyValues( 
            ('Height','MultiLine','PositionX','PositionY','Width',), 
            (13,False,2,15,171,) )
        cbtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        cbtn_model.setPropertyValues( 
            ('Height','Label','PositionX','PositionY','PushButtonType','Width',), 
            (14,'~cancel',142,48,2,29,) )
        obtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        obtn_model.setPropertyValues( 
            ('DefaultButton','Height','Label','PositionX',
            'PositionY','PushButtonType','Width',), 
            (True,14,'~OK',142,32,1,29,) )
        label_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlFixedTextModel')
        label_model.setPropertyValues( 
            ('FontHeight','Height','MultiLine','PositionX','PositionY','Width',),
            (8,30,True,2,30,130) )
        
        dialog_model.insertByName('line',line_model)
        dialog_model.insertByName('cbtn',cbtn_model)
        dialog_model.insertByName('obtn',obtn_model)
        dialog_model.insertByName('edit',edit_model)
        dialog_model.insertByName('label',label_model)
        
        line_model.Label = label
        label_model.Label = txt
        edit_model.Text = init
        
        dialog.setModel(dialog_model)
        dialog.setVisible(True)
        dialog.getControl('edit').setFocus()
        if init != '':
            from com.sun.star.awt import Selection
            selrange = Selection()
            selrange.Min = len(init)
            selrange.Max = selrange.Min
            dialog.getControl('edit').setSelection(selrange)
        
        state = dialog.execute()
        
        if state:
            txt = dialog_model.getByName('edit').Text
        else:
            txt = ''
        dialog.dispose()
        
        return (txt,state)
    
    
    def dialog_input2(self,label='',txt='',init='',dclass='',word=''):
        """ Input dialog 2. """
        dialog = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialog',self.ctx)
        dialog_model = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialogModel',self.ctx)
        dialog_model.setPropertyValues( 
            ('Height','HelpURL','PositionX','PositionY','Width',), 
            (81,'mytools.Mri:d_input2',30,50,177,) )
        
        line_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlFixedLineModel')
        line_model.setPropertyValues( 
            ('Height','PositionX','PositionY','Width',), 
            (12,4,1,170) )
        edit_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlEditModel')
        edit_model.setPropertyValues( 
            ('Height','MultiLine','PositionX','PositionY','Width',), 
            (13,False,2,15,171,) )
        cbtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        cbtn_model.setPropertyValues( 
            ('Height','Label','PositionX','PositionY','PushButtonType','Width',), 
            (14,'~cancel',142,48,2,29,) )
        obtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        obtn_model.setPropertyValues( 
            ('DefaultButton','Height','Label','PositionX',
            'PositionY','PushButtonType','Width',), 
            (True,14,'~OK',142,32,1,29,) )
        #label_model = dialog_model.createInstance( 
        #   'com.sun.star.awt.UnoControlFixedTextModel')
        #label_model.setPropertyValues( 
        #   ('FontHeight','Height','MultiLine','PositionX','PositionY','Width',),
        #   (8,46,True,2,30,130) )
        label_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlEditModel')
        label_model.setPropertyValues( 
            ('FontHeight','Height','MultiLine','PositionX','PositionY','ReadOnly','Width',),
            (8,48,True,2,30,True,135) )
        
        ibtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        ibtn_model.setPropertyValues( 
            ('Height','Label','PositionX','PositionY','PushButtonType','Width',), 
            (14,'~Ref.',142,64,0,29,) )
        dialog_model.insertByName('line',line_model)
        dialog_model.insertByName('cbtn',cbtn_model)
        dialog_model.insertByName('obtn',obtn_model)
        dialog_model.insertByName('edit',edit_model)
        dialog_model.insertByName('label',label_model)
        dialog_model.insertByName('ibtn',ibtn_model)
        
        line_model.Label = label
        #label_model.Label = txt
        label_model.Text = txt
        edit_model.Text = init
        
        dialog.setModel(dialog_model)
        dialog.setVisible(True)
        dialog.getControl('edit').setFocus()
        
        ibtn = dialog.getControl('ibtn')
        ibtn.ActionCommand = 'idlref'
        buttonlistener = InputButtonListener(self.cast,dclass,word)
        ibtn.addActionListener(buttonlistener)
        
        state = dialog.execute()
        ibtn.removeActionListener(buttonlistener)
        
        if state:
            txt = dialog_model.getByName('edit').Text
        else:
            txt = ''
        
        dialog.dispose()
        return (txt,state)
    
    
    def dialog_inputstruct(self,label='',txt='',init='',dclass=''):
        dialog = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialog',self.ctx)
        dialog_model = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialogModel',self.ctx)
        dialog_model.setPropertyValues( 
            ('Height','HelpURL','PositionX','PositionY','Width',), 
            (134,'mytools.Mri:d_inputstruct',30,50,180,) )
            
        obtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        obtn_model.setPropertyValues(
            ('DefaultButton','Height','Label','PositionX','PositionY','PushButtonType','Width'),
            (True,14,'~OK',148,85,1,29) )
        cbtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        cbtn_model.setPropertyValues(
            ('Height','Label','PositionX','PositionY','PushButtonType','Width'),
            (14,'~cancel',148,101,2,29) )
        ibtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        ibtn_model.setPropertyValues(
            ('Height','Label','PositionX','PositionY','Width'),
            (14,'~Ref.',148,117,29) )
        iedit_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlEditModel')
        iedit_model.setPropertyValues(
            ('FontHeight','Height','MultiLine','PositionX','PositionY','ReadOnly','VScroll','Width'),
            (8,47,True,2,84,True,True,142) )
        medit_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlEditModel')
        medit_model.setPropertyValues(
            ('Height','MultiLine','PositionX','PositionY','VScroll','Width'),
            (66,True,2,15,True,176) )
        hline_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlFixedLineModel')
        hline_model.setPropertyValues(
            ('Height','PositionX','PositionY','Width'),
            (12,1,1,178) )
        
        dialog_model.insertByName('obtn',obtn_model)
        dialog_model.insertByName('cbtn',cbtn_model)
        dialog_model.insertByName('ibtn',ibtn_model)
        dialog_model.insertByName('hline',hline_model)
        dialog_model.insertByName('iedit',iedit_model)
        dialog_model.insertByName('medit',medit_model)
        
        hline_model.Label = label
        iedit_model.Text = txt
        medit_model.Text = init
        
        dialog.setModel(dialog_model)
        dialog.setVisible(True)
        
        ibtn = dialog.getControl('ibtn')
        ibtn.ActionCommand = 'idlref'
        buttonlistener = InputButtonListener(self.cast,dclass,'')
        ibtn.addActionListener(buttonlistener)
        
        state =  dialog.execute()
        ibtn.removeActionListener(buttonlistener)
        
        if state:
            txt = medit_model.Text
        else:
            txt = ''
        
        dialog.dispose()
        return (txt,state)
    
    def dialog_elemental_input(self, elements, label='', txt='', doc=('', '')):
        from com.sun.star.style.VerticalAlignment import BOTTOM as VA_BOTTOM
        y = 14
        
        dialog = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        dialog_model = self.smgr.createInstanceWithContext( 
            'com.sun.star.awt.UnoControlDialogModel', self.ctx)
        dialog_model.setPropertyValues( 
            ('Height', 'HelpURL', 'PositionX', 'PositionY', 'Width',), 
            (67 + len(elements) * 27, 'mytools.Mri:d_input2', 30, 50, 177,) )
        
        line_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlFixedLineModel')
        line_model.setPropertyValues( 
            ('Height', 'PositionX', 'PositionY', 'Width',), 
            (12, 4, 1, 170) )
        
        for i in range(len(elements)):
            label_model = dialog_model.createInstance( 
                'com.sun.star.awt.UnoControlFixedTextModel')
            label_model.setPropertyValues( 
                ('Height', 'NoLabel', 'PositionX', 'PositionY', 'VerticalAlign', 'Width',), 
                (12, True, 4, y, VA_BOTTOM, 170) )
            dialog_model.insertByName('label_%s' % i, label_model)
            label_model.Label = elements[i]
            
            edit_model = dialog_model.createInstance( 
                'com.sun.star.awt.UnoControlEditModel')
            edit_model.setPropertyValues(
                ('Height', 'MultiLine', 'PositionX', 'PositionY', 'Width',), 
                (13, False, 2, y + 13, 171,) )
            dialog_model.insertByName('edit_%s' % i, edit_model)
            y += 27
            
        y += 3
        obtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        obtn_model.setPropertyValues( 
            ('DefaultButton', 'Height', 'Label', 'PositionX',
            'PositionY', 'PushButtonType', 'Width',), 
            (True, 14, '~OK', 142, y, 1, 29,) )
        cbtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        cbtn_model.setPropertyValues( 
            ('Height', 'Label', 'PositionX', 'PositionY', 'PushButtonType', 'Width',), 
            (14, '~cancel', 142, y +15, 2, 29,) )
        ibtn_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlButtonModel')
        ibtn_model.setPropertyValues( 
            ('Height', 'Label', 'PositionX', 'PositionY', 'PushButtonType', 'Width',), 
            (14, '~Ref.', 142, y + 30, 0, 29,) )
        
        label_model = dialog_model.createInstance( 
            'com.sun.star.awt.UnoControlEditModel')
        label_model.setPropertyValues( 
            ('FontHeight', 'Height', 'MultiLine', 'PositionX', 'PositionY', 'ReadOnly', 'Width',),
            (8, 48, True, 2, y, True, 135) )
        
        dialog_model.insertByName('line',line_model)
        dialog_model.insertByName('obtn',obtn_model)
        dialog_model.insertByName('cbtn',cbtn_model)
        dialog_model.insertByName('ibtn',ibtn_model)
        dialog_model.insertByName('label',label_model)
        
        line_model.Label = label
        label_model.Text = txt
        
        dialog.setModel(dialog_model)
        dialog.setVisible(True)
        dialog.getControl('edit_0').setFocus()
        
        ibtn = dialog.getControl('ibtn')
        ibtn.ActionCommand = 'idlref'
        buttonlistener = InputButtonListener(self.cast, doc[0], doc[1])
        ibtn.addActionListener(buttonlistener)
        
        state = dialog.execute()
        ibtn.removeActionListener(buttonlistener)
        
        args = []
        if state:
            args = []
            for i in range(len(elements)):
                args.append(dialog_model.getByName('edit_%s' % i).Text)
        
        dialog.dispose()
        return state, args
    
    def message(self, message, title="", type="messbox", buttons=1):
        """ Message box, see css.awt.XMessageBoxFactory. """
        desktop = self.smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.ctx)
        frame = desktop.getActiveFrame()
        window = frame.getContainerWindow()
        msgbox = window.getToolkit().createMessageBox(
            window, Rectangle(), type, buttons, title, message)
        n = msgbox.execute()
        msgbox.dispose()
        return n
    
    
    def history_selector(self, title="", listener=None):
        """ Select an entry from history. """
        mri = self.cast.main
        
        class Wrapper(unohelper.Base):
            def __init__(self, obj):
                self.obj = obj
        
        from mytools_Mri.values import MRI_DIR
        dlg = mri.create_service("com.sun.star.awt.DialogProvider", nocode=True).\
                createDialog(MRI_DIR + "/dialogs/empty.xdl")
        dlg_model = dlg.getModel()
        dlg_model.setPropertyValues(
            ("Height", "Width"), 
            (140, 180))
        def create(ctrl_name, name, x, y, width, height, 
            names, values, nonfull=True):
            if nonfull:
                ctrl_name = "com.sun.star.awt.UnoControl%sModel" % ctrl_name
            ctrl_model = dlg_model.createInstance(ctrl_name)
            ctrl_model.setPropertyValues(
                ("Height", "PositionX", "PositionY", "Width"), 
                (height, x, y, width))
            if names and values:
                ctrl_model.setPropertyValues(names, values)
            dlg_model.insertByName(name, ctrl_model)
            return ctrl_model
        create("FixedText", "labelHistory", 5, 3, 96, 12, 
            ("Label", ), ("History",))
        create("Button", "btnOk", 134, 4, 43, 14, 
            ("Label", "PushButtonType"), ("OK", 1))
        create("Button", "btnCancel", 134, 24, 43, 14, 
            ("Label", "PushButtonType"), ("Cancel", 2))
        data_model = mri.create_service(
            'com.sun.star.awt.tree.MutableTreeDataModel', nocode=True)
        tree_model = create("com.sun.star.awt.tree.TreeControlModel", 
            "treeHistory", 3, 18, 127, 117, 
            ("DataModel", "SelectionType", "RootDisplayed"), (data_model, 1, True), False)
        
        child = mri.history.get_children()[0]
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
        
        tree = dlg.getControl("treeHistory")
        if listener:
            tree.addSelectionChangeListener(listener)
        dlg.getControl("btnOk").setEnable(False)
        tree.makeNodeVisible(root.getChildAt(0))
        
        obj = None
        dlg.setTitle(title)
        if dlg.execute():
            selected = tree.getSelection()
            if selected:
                obj = selected.DataValue.obj
        dlg.dispose()
        return obj

