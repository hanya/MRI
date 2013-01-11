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

from com.sun.star.awt import XActionListener
from com.sun.star.beans import PropertyValue
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK as EDR_OK
from com.sun.star.ui.dialogs.TemplateDescription import \
    FILEOPEN_SIMPLE as TD_FILEOPEN_SIMPLE

import mytools_Mri.values
from mytools_Mri import tools

class ConfigButtonListener(unohelper.Base, XActionListener):
    def __init__(self, dialogmodel, cast):
        self.dialogmodel = dialogmodel
        self.cast = cast
    
    def disposing(self, ev):
        pass
    
    def actionPerformed(self, ev):
        cmd = str(ev.ActionCommand)
        if cmd == 'sdk':
            idlpath = self.cast.get_directory_url(
                'Select your OpenOffice.org SDK directory.')
            if idlpath:
                edit_idl = self.dialogmodel.getByName('edit_sdk').Text = idlpath
        elif cmd == 'browser':
            browserpath = self.cast.get_file_url()
            if browserpath:
                self.dialogmodel.getByName('edit_browser').Text = browserpath
        elif cmd == 'macros':
            macros = self.cast.get_directory_url(
                "Select macros directory.")
            if macros:
                self.dialogmodel.getByName('edit_macros').Text = macros
        elif cmd == "keyconfig":
            try:
                import mytools_Mri.ui.keyconfig
                mytools_Mri.ui.keyconfig.KeyConfig(self.cast.cast.ctx).start()
            except Exception as e:
                print(e)

# Mri configuration class
class ConfigDialog(object):
    
    def __init__(self,cast):
        self.cast = cast
        self.ctx = cast.ctx
    
    def dialog_config(self, config):
        """configuration dialog."""
        ext_dir = mytools_Mri.values.MRI_DIR
        dlg_url = '%s/dialogs/Config.xdl' % ext_dir
        dlg = tools.create_dialog_from_url(self.ctx, dlg_url)
        if not dlg: raise Exception('configuration dialog not found.')
        dlg_model = dlg.getModel()
        btn_listener = ConfigButtonListener(dlg_model, self)
        dc = dlg.getControl
        
        for i in ("sdk", "browser", "macros", "keyconfig"):
            btn = dc("btn_" + i)
            btn.setActionCommand(i)
            btn.addActionListener(btn_listener)
        
        edit_sdk_model = dlg_model.getByName('edit_sdk')
        edit_browser_model = dlg_model.getByName('edit_browser')
        edit_macros_model = dlg_model.getByName('edit_macros')
        edit_possize_model = dlg_model.getByName('edit_possize')
        edit_fontname_model = dlg_model.getByName('edit_fontname')
        edit_charsize_model = dlg_model.getByName('edit_charsize')
        check_grid_model = dlg_model.getByName('check_grid')
        check_tab_model = dlg_model.getByName('check_tab')
        
        pos_size = self.cast.window.getPosSize() # get current window possize
        pos_size = ','.join( [str(pos_size.X),str(pos_size.Y),
            str(pos_size.Width),str(pos_size.Height)] )
            
        edit_sdk_model.Text = config.sdk_path
        edit_browser_model.Text = config.browser
        edit_macros_model.Text = config.macros
        edit_possize_model.Text = pos_size
        edit_fontname_model.Text = config.font_name
        edit_charsize_model.Text = config.char_size
        
        if config.__class__.GRID == 0:
            dc('check_grid').setEnable(False)
        else:
            v = 1
            if not config.grid:
                v = 0
            check_grid_model.State = v#1 if config.grid else 0
        if config.__class__.TAB == 0:
            dc('check_tab').setEnable(False)
        else:
            v = 1
            if not config.use_tab:
                v = 0
            check_tab_model.State = v#1 if config.use_tab else 0
        
        ret = False
        if dlg.execute():
            ret = True
            
            config.sdk_path = edit_sdk_model.Text
            config.browser = edit_browser_model.Text
            config.macros = edit_macros_model.Text
            
            config.font_name = edit_fontname_model.Text
            config.char_size = float(edit_charsize_model.Text)
            
            if dlg_model.getByName('check_possize').State == 1:
                config.pos_size = edit_possize_model.Text
            
            if dlg_model.getByName('check_options').State == 1:
                config.save_options = True
            
            config.grid = not not check_grid_model.State
            config.use_tab = not not check_tab_model.State
        dlg.dispose()
        return ret
    
    
    def get_directory_url(self, title=""):
        fp = self.ctx.getServiceManager().createInstanceWithContext( 
            'com.sun.star.ui.dialogs.FolderPicker', self.ctx)
        fp.setDescription(title)
        dirpath = ""
        if fp.execute() == EDR_OK:
            dirpath = fp.getDirectory()
            return dirpath
        else:
            return False
    
    
    def get_file_url(self):
        fp = self.ctx.getServiceManager().createInstanceWithContext( 
            'com.sun.star.ui.dialogs.FilePicker', self.ctx)
        fp.initialize((TD_FILEOPEN_SIMPLE,))
        fp.setMultiSelectionMode(False)
        fp.appendFilter('All Files (*.*)', '*.*')
        fp.appendFilter('EXE Files (*.exe)', '*.exe')
        fp.appendFilter('BIN Files (*.bin)', '*.bin')
        fp.appendFilter('SH Files (*.sh)', '*.sh')
        fp.setCurrentFilter('All Files (*.*)')
        
        filepath = ""
        if fp.execute() == EDR_OK:
            filepaths = fp.getFiles()
            filepath = filepaths[0]
            return filepath
        else:
            return False

