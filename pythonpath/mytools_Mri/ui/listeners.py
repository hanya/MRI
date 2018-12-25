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
import sys
import os.path
import traceback
from com.sun.star.awt import XActionListener, XItemListener, \
    XMouseListener, XWindowListener, XMenuListener, \
    XKeyListener, XMouseMotionListener, \
    FocusEvent, Rectangle, KeyEvent, MouseEvent
from com.sun.star.lang import XEventListener
from com.sun.star.awt.PosSize import X as PS_X, Y as PS_Y, \
    WIDTH as PS_WIDTH, SIZE as PS_SIZE, HEIGHT as PS_HEIGHT
from com.sun.star.awt.MenuItemStyle import RADIOCHECK as MIS_RADIOCHECK
from com.sun.star.awt.MouseButton import LEFT as MB_LEFT, RIGHT as MB_RIGHT
from mytools_Mri.tools import get_configvalue, call_dispatch, open_help, create_service

class KeyModifier(object):
    from com.sun.star.awt.KeyModifier import MOD1, MOD2, SHIFT


class SplitterMouseListener(unohelper.Base, XMouseListener, XMouseMotionListener):
    def __init__(self,cast,use_tab):
        self.cast = cast
        window_pos = self.cast.window.OutputSize
        self.Y = (window_pos.Height - 65) * 3 / 4
        self.minimized = True
        self.tab_mode = use_tab
    def disposing(self,ev):
        self.cast = None
    def mouseMoved(self,ev):    pass
    def mouseDragged(self,ev):
        if ev.Buttons == MB_LEFT:
            split_pos = ev.Source.getPosSize()
            window_pos = self.cast.window.OutputSize
            if 86 < split_pos.Y + ev.Y < window_pos.Height - 25:
                ev.Source.setPosSize(0,split_pos.Y + ev.Y,0,0,PS_Y)
                cont = self.cast.cont
                edit_code = cont.getControl('edit_code')
                nY = split_pos.Y - 65
                ph = PS_HEIGHT
                self._resize_edit_info(0, nY, ph)
                edit_code.setPosSize(0, split_pos.Y +6, 0, window_pos.Height - 27 - split_pos.Y, ph + PS_Y )
                self.minimized = False#not self.minimized
    
    def mouseReleased(self,ev): pass
    def mouseEntered(self,ev): pass
    def mouseExited(self,ev): pass
    def mousePressed(self,ev):
        if not self.cast.config.show_code: return
        if ev.Source == self.cast.splitter:
            if not (ev.Buttons == MB_LEFT and ev.ClickCount == 2): return
        else:
            if not (ev.Buttons == MB_RIGHT and ev.ClickCount == 2): return
        try:
            self.expand_code_edit()
        except Exception as e:
            print(e)
    
    def expand_code_edit(self):
        if self.minimized:
            self.expand()
        else:
            self.minimize()
    
    def expand(self):
        # restore position of the splitter
        window_pos = self.cast.window.OutputSize
        cont = self.cast.cont
        splitter = self.cast.splitter
        splitter.setPosSize(0,self.Y,0,0,PS_Y)
        split_pos = splitter.getPosSize()
        
        edit_code = cont.getControl('edit_code')
        height = split_pos.Y -65
        
        self._resize_edit_info(0, height, PS_HEIGHT)
        edit_code.setPosSize(0,split_pos.Y +6, 0,window_pos.Height - 27 - split_pos.Y, PS_HEIGHT | PS_Y )
        self.minimized = False
    
    def minimize(self):
        # minize code edit
        window_pos = self.cast.window.OutputSize
        cont = self.cast.cont
        splitter = self.cast.splitter
        split_pos = splitter.getPosSize()
        self.Y = split_pos.Y
        splitter.setPosSize(0,window_pos.Height -26,0,0,PS_Y)
        
        edit_code = cont.getControl('edit_code')
        y = window_pos.Height -90
        
        self._resize_edit_info(0, y, PS_HEIGHT)
        edit_code.setPosSize(0,window_pos.Height -27, 0,0, PS_HEIGHT | PS_Y)
        self.minimized = True
    
    def _resize_edit_info(self, width, height, mode):
        cont = self.cast.cont
        subcont = cont.getControl('subcont')
        subcont.setPosSize(0, 0, width, height, mode)
        if self.tab_mode:
            tab = subcont.getControl('tab')
            tab.setPosSize(0, 0, width, height, mode)
            tab_pages = tab.getControls()
            if hasattr(tab, "ActiveTabPageID"):
                tab_ps = tab_pages[tab.ActiveTabPageID - 1].getOutputSize()
            else:
                tab_ps = tab_pages[tab.ActiveTabID - 1].getOutputSize()
            width = tab_ps.Width
            height = tab_ps.Height
            for i, tab_page in enumerate(tab_pages):
                tab_page.getControl('info_%s' % i).setPosSize(
                    0, 0, width, height, mode)
        else:
            for i in range(4):
                subcont.getControl('info_%s' % i).setPosSize(
                    0, 0, width, height, mode)
    
    def set_visible(self, state):
        self.cast.splitter.setVisible(state)
    
    def close(self):
        self.minimize()
        self.set_visible(False)
    
    def open(self):
        self.set_visible(True)
        self.expand()


class ButtonListener(unohelper.Base, XActionListener):
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev): pass
    def actionPerformed(self, ev):
        cmd = str(ev.ActionCommand)
        if cmd == 'ref':
            self.cast.open_idl_reference()
        elif cmd == 'back':
            self.cast.history_back()
        elif cmd == 'forward':
            self.cast.history_forward()
        elif cmd == 'search':
            self.cast.search_word()
        elif cmd == 'index':
            self.cast.try_index_access()
        elif cmd == 'name':
            self.cast.try_name_access()
        elif cmd == 'history':
            self.cast.show_history_tree(ev)


class KeyListener(unohelper.Base, XKeyListener):
    
    MACRO = "macro:"
    
    def __init__(self, cast, grid=False):
        self.cast = cast
        self.grid = grid
        from mytools_Mri.ui import keys
        loader = keys.KeyConfigLoader(cast.main.ctx)
        loader.construct_keys()
        self.keys = keys.KeyConfigLoader
        self.funcs = {
            "next": self.cast.history_forward, 
            "previous": self.cast.history_back, 
            "ref": self.cast.open_idl_reference, 
            "search": self.cast.cont.getControl('edit_search').setFocus, 
            "selectline": self.cast.pages.select_current_line, 
            "selectword": self.cast.pages.select_current_sentence, 
            "sort": self.sort, 
            "abbr": self.abbr, 
            "pseud_prop": self.pseud_prop, 
            "code": self.code, 
            "index": self.cast.try_index_access, 
            "name": self.cast.try_name_access, 
            "properties": self.properties, 
            "methods": self.methods, 
            "interfaces": self.interfaces, 
            "services": self.services
        }
        if grid:
            self.funcs["gridcopy"] = self.copy
    def disposing(self, ev): pass
    def keyReleased(self, ev): pass
    def keyPressed(self, ev):
        key = ev.KeyCode
        mod = ev.Modifiers
        cmd = self.keys.KEYS.get((mod, key), "")
        fn = self.funcs.get(cmd, None)
        if fn:
            try:
                fn()
            except Exception as e:
                print(e)
        elif cmd == "execute" or cmd == "opennew":
            self.open(cmd, mod)
        elif cmd == "contextmenu" or key == 1305:
            if self.grid: self.context_menu(ev)
        elif cmd.startswith(self.MACRO):
            self.execute_macro()
    
    def execute_macro(self, cmd):
        file_name, func_name = cmd[6:].split("$")
        self.cast.execute_macro(file_name, func_name)
    
    def properties(self):
        self.cast.category_changed(0)
    def methods(self):
        self.cast.category_changed(1)
    def interfaces(self):
        self.cast.category_changed(2)
    def services(self):
        self.cast.category_changed(3)
    
    def open(self, cmd, mod):
        category = self.cast.pages.get_active()
        if cmd == "opennew":
            self.cast.main.open_new = True
        try:
            self.cast.info_action(category)
        except:
            pass
    
    def sort(self):
        item = self.cast.menu.getPopupMenu(1)
        self.cast.config.sorted = not item.isItemChecked(0)
        item.checkItem(0, self.cast.config.sorted)
        self.cast.reload_entry()
    def abbr(self):
        item = self.cast.menu.getPopupMenu(1)
        self.cast.config.abbrev = not item.isItemChecked(1)
        item.checkItem(1, self.cast.config.abbrev)
        self.cast.reload_entry()
    def pseud_prop(self):
        item = self.cast.menu.getPopupMenu(1)
        self.cast.config.property_only = item.isItemChecked(6)
        item.checkItem(6, not self.cast.config.property_only)
        self.cast.reload_entry()
    def code(self):
        self.cast.listeners['splitter'].expand_code_edit()
    def copy(self):
        word = self.cast.pages.get_first_word()
        try:
            from mytools_Mri.ui import transferable
            transferable.set_text_to_clipboard(self.cast.ctx, word)
        except:
            pass
    
    def context_menu(self, ev):
        try:
            ps = ev.Source.getPosSize()
            ev = MouseEvent(ev.Source, 0, MB_RIGHT, 
                ps.Width / 2,  ps.Height / 4, 1, False)
            listener = self.cast.listeners['grid_info']
            listener.mousePressed(ev)
        except Exception as e:
            print(e)

class ListScopeListener(unohelper.Base, XItemListener):
    """ Detect change of the category list box. """
    
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev): pass
    def itemStateChanged(self, ev):
        self.cast.category_changed(ev.Selected)

class ListHistoryListener(unohelper.Base, XItemListener):
    """ Detect the change of the history list box. """
    
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev): pass
    def itemStateChanged(self, ev):
        self.cast.history_change(ev.Selected)


class EditInfoListener(unohelper.Base, XMouseListener):
    """ Actions on text edit of the window. """
    
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev): pass
    def mouseReleased(self, ev): pass
    def mouseEntered(self, ev): pass
    def mouseExited(self, ev): pass
    def mousePressed(self, ev):
        if ev.Buttons == 1 and ev.ClickCount == 2:
            category = self.cast.pages.get_active()
            mod = ev.Modifiers
            if mod == KeyModifier.SHIFT:
                return
            if category == 0:
                if mod == KeyModifier.MOD2 or \
                    mod == (KeyModifier.SHIFT | KeyModifier.MOD1):
                    mode = self.cast.property_mode
                    self.cast.property_mode = (not mode)
                    try:
                        self.cast.info_action(category)
                    except:
                        pass
                    self.cast.property_mode = mode
                else:
                    if mod == KeyModifier.MOD1:
                        self.cast.main.open_new = True
                    self.cast.info_action(category)
            elif category == 1:
                if mod == KeyModifier.SHIFT:
                    self.cast.main.open_new = True 
                self.cast.info_action(category)


class WindowListener(unohelper.Base, XWindowListener):
    """ Manages size of the window. """
    def __init__(self, cast, use_tab):
        self.cast = cast
        self.tab_mode = use_tab
    def disposing(self, ev): pass
    def windowMoved(self, ev): pass
    def windowShown(self, ev): pass
    def windowHidden(self, ev): pass
    def windowResized(self, ev):
        try:
            width = ev.Width
            height = self.cast.window.OutputSize.Height
            if height < 130: height = 130
            cont = self.cast.cont
            gcont = cont.getControl
            subcont = gcont('subcont')
            gsc = subcont.getControl
            if self.tab_mode:
                edit_info = subcont.getControl('tab')
                tab = edit_info
            else:
                edit_info = gsc('info_0')
            
            edit_code = gcont('edit_code')
            label_status = gcont('label_status')
            edit_in = gcont('edit_in')
            edit_search = gcont('edit_search')
            btn_search = gcont('btn_search')
        
            info_pos = subcont.getPosSize()
            code_pos = edit_code.getPosSize()
        
            info_height = info_pos.Height
            code_height = code_pos.Height
            if code_height <= 2: code_height = 0
            
            if self.cast.config.show_code:
                full_height = height - 90
                total_height = info_height + code_height
                info_height = full_height * info_height / total_height
            else:
                full_height = height - 85
                total_height = info_height
                info_height = full_height
        
            code_height = full_height * code_height / total_height
            
            subcont.setPosSize(0, 0, width, info_height, PS_SIZE)
            if self.tab_mode:
                tab.setPosSize(0, 0, width, info_height, PS_SIZE)
                if hasattr(tab, "ActiveTabPageID"):
                    tab_ps = tab.getControls()[tab.ActiveTabPageID - 1].getOutputSize()
                else:
                    tab_ps = tab.getControls()[tab.ActiveTabID - 1].getOutputSize()
                tab_width = tab_ps.Width
                tab_height = tab_ps.Height
                #print(tab_width, tab_height)
                tab_pages = tab.getControls()
                tab_pages[0].getControl('info_0').setPosSize(0, 0, tab_width, tab_height, PS_SIZE)
                tab_pages[1].getControl('info_1').setPosSize(0, 0, tab_width, tab_height, PS_SIZE)
                tab_pages[2].getControl('info_2').setPosSize(0, 0, tab_width, tab_height, PS_SIZE)
                tab_pages[3].getControl('info_3').setPosSize(0, 0, tab_width, tab_height, PS_SIZE)
            else:
                gsc('info_0').setPosSize(0, 0, width, info_height, PS_SIZE)
                gsc('info_1').setPosSize(0, 0, width, info_height, PS_SIZE)
                gsc('info_2').setPosSize(0, 0, width, info_height, PS_SIZE)
                gsc('info_3').setPosSize(0, 0, width, info_height, PS_SIZE)
            
            self.cast.splitter.setPosSize(0,info_pos.Y + info_height,width,0,PS_WIDTH | PS_Y)
            edit_code.setPosSize(0,info_pos.Y + info_height +6,width,code_height,PS_SIZE | PS_Y)
        
            stbar_Y = height - 20
            label_status.setPosSize(0, stbar_Y, width - 320, 0, PS_Y + PS_WIDTH)
            edit_in.setPosSize(width - 315, stbar_Y, 0, 0, PS_Y + PS_X)
            edit_search.setPosSize(width - 109, stbar_Y, 0, 0, PS_Y + PS_X)
            btn_search.setPosSize(width - 39, stbar_Y, 0, 0, PS_Y + PS_X)
        except Exception as e:
            print(("resize error: " + str(e)))
            traceback.print_exc()


class MenuListener(unohelper.Base, XMenuListener):
    """ Executed by choosing a menu entry. """
    
    def __init__(self, cast):
        self.cast = cast
        self.functions = {
            't_': self.tools_menu, 'f_': self.file_menu, 
            'w_': self.window_menu, 'o_': self.targets_menu, 
            'm_': self.mode_menu, 'h_': self.help_menu, 
            's_': self.macros_menu, "e_": self.execute_macro}
    
    def disposing(self,ev): pass
    
    def activate(self,ev): pass
    def deactivate(self,ev): pass
    
    def highlight(self,ev):
        self.itemHighlighted(ev)
    
    def select(self, ev):
        self.itemSelected(ev)
    
    # since AOO 4.0
    def itemActivated(self, ev): pass
    def itemDeactivated(self, ev): pass
    
    def itemSelected(self, ev):
        menu = ev.Source
        mid = ev.MenuId
        cmd = menu.getCommand(mid)[12:]
        fn = self.functions.get(cmd[0:2], None)
        if fn:
            try:
                fn(menu, mid, cmd)
            except Exception as e:
                print(e)
    
    def itemHighlighted(self, ev):
        cmd = ev.Source.getCommand(ev.MenuId)
        
        if cmd == 'targets':
            menu = ev.Source.getPopupMenu(ev.MenuId)
            menu.removeItem(6,menu.getItemCount() -6)
            frames = self.cast.desktop.getFrames()
            for i in range(frames.getCount()):
                mid = i+6
                title = frames.getByIndex(i).getTitle()
                menu.insertItem(mid, title, 0, mid)
                menu.setCommand(mid, 'mytools.Mri:o_' + title)
        
        elif cmd == 'window':
            menu = ev.Source.getPopupMenu(ev.MenuId)
            menu.removeItem(3,menu.getItemCount()-3)
            frames = self.cast.desktop.getFrames()
            for i in range(frames.getCount()):
                mid = i + 4
                frame = frames.getByIndex(i)
                title = frame.Title
                menu.insertItem(mid, title,MIS_RADIOCHECK, mid)
                menu.setCommand(mid, 'mytools.Mri:w_' + title)
                if frame == self.cast.frame:
                    menu.checkItem(mid, True)
        
        elif cmd == "mytools.Mri:t_code":
            menu = ev.Source.getPopupMenu(ev.MenuId)
            if menu.getItemCount() < 5:
                code_type = self.cast.main.config.code_type
                generators = self.cast.main.cg.get_generator_list()
                for i,g in enumerate(generators):
                    mid = i + 5
                    menu.insertItem(mid, g[1], MIS_RADIOCHECK, mid -1)
                    menu.setCommand(mid, 'mytools.Mri:t_code_%s' % g[0])
                    if g[0] == code_type:
                        menu.checkItem(mid, True)
        
        elif cmd == 'macros':
            if not self.cast.main.macros.is_loaded():
                menu = ev.Source.getPopupMenu(ev.MenuId)
                menu.removeItem(0, menu.getItemCount())
                try:
                    names = self.cast.main.macros.get_macro_names()
                except Exception as e:
                    return self.cast.status(str(e))
                names.sort()
                for i, name in enumerate(names):
                    menu.insertItem(i +3, os.path.basename(name), 0, i+2)
                    menu.setCommand(i +3, "mytools.Mri:s_" + name)
        
        elif cmd.startswith("mytools.Mri:s_"):
            file_name = cmd[14:]
            menu = ev.Source
            if not menu.getPopupMenu(ev.MenuId):
                try:
                    items = self.cast.main.macros.get_functions(file_name)
                except Exception as e:
                    return self.cast.status(str(e))
                if items:
                    ctx = self.cast.main.ctx
                    popup = ctx.getServiceManager().createInstanceWithContext(
                        'com.sun.star.awt.PopupMenu',ctx)
                    popup.addMenuListener(self.cast.main.ui.listeners['menu'])
                    tip = hasattr(popup, "setTipHelpText")
                    for i, item in enumerate(items):
                        if item is None:
                            popup.insertSeparator(i)
                        else:
                            popup.insertItem(i +1, item[1], 0, i)
                            popup.setCommand(i +1, 
                                "mytools_Mri:s_%s$%s" % (file_name, item[0]))
                            if tip:
                                tooltip = item[2]
                                if tooltip is None:
                                    tooltip = ""
                                popup.setTipHelpText(i +1, tooltip)
                    menu.setPopupMenu(ev.MenuId, popup)
    
    def change_frame(self,wid,name):
        if wid > 0:
            frames = self.cast.desktop.getFrames()
            frame = frames.getByIndex(wid -4)
            if frame.getTitle() == name:
                frame.focusGained(FocusEvent())
    
    def tools_menu(self, menu, mid, cmd):
        if cmd == 't_sort':
            self.cast.config.sorted = menu.isItemChecked(mid)
            self.cast.reload_entry()
        elif cmd == 't_abbr':
            self.cast.config.abbrev = menu.isItemChecked(mid)
            self.cast.reload_entry()
        elif cmd == "t_pseud":
            self.cast.config.property_only = not menu.isItemChecked(mid)
            self.cast.reload_entry()
        elif cmd == 't_showlabels':
            self.cast.config.show_labels = menu.isItemChecked(mid)
            self.cast.reload_entry()
        elif cmd == 't_config':
            import mytools_Mri.ui.config
            try:
                if mytools_Mri.ui.config.ConfigDialog(self.cast).\
                    dialog_config(self.cast.config):
                    self.cast.update_config()
            except Exception as e:
                print(e)
                traceback.print_exc()
        elif cmd == 't_showcode':
            try:
                state = menu.isItemChecked(mid)
                self.cast.config.show_code = state
                self.cast.main.cg.change_state(enabled=state)
                if state:
                    self.cast.listeners['splitter'].open()
                else:
                    self.cast.listeners['splitter'].close()
            except Exception as e:
                print(e)
                traceback.print_exc()
        elif cmd == 't_pseudproperty':
            state = menu.isItemChecked(mid)
            self.cast.config.use_pseud_props = state
            self.cast.main.cg.change_state(pseud=state)
            self.cast.code_updated()
        elif cmd.startswith('t_code_'):
            new_type = cmd[7:]
            if new_type != self.cast.config.code_type:
                last_pos = menu.getItemCount() -1
                for i in range(5,menu.getItemId(last_pos) +1):
                    menu.checkItem(i, False)
                menu.checkItem(mid, True)
                self.cast.config.code_type = new_type
                self.cast.main.cg.change_state(code_type=new_type)
                self.cast.code_updated()
    
    def targets_menu(self, menu, mid, cmd):
        self.cast.execute_macro("bundle.py", "inspect_frame", "extension", cmd[2:len(cmd)])
    
    def window_menu(self, menu, mid, cmd):
        self.change_frame(mid, cmd[2:])
    
    def mode_menu(self, menu, mid, cmd):
        if cmd == 'm_get':
            self.cast.property_mode = True
        elif cmd == 'm_set':
            self.cast.property_mode = False
        menu.checkItem(0,self.cast.property_mode)
        menu.checkItem(1,not self.cast.property_mode)
    
    def help_menu(self, menu, mid, cmd):
        if cmd == 'h_about':
            self.about_MRI()
        elif cmd == 'h_doc':
            self.open_help()
        elif cmd == 'h_what':
            call_dispatch(self.cast.ctx, self.cast.desktop, '.uno:ExtendedHelp')
    
    def file_menu(self, menu, mid, cmd):
        if cmd.startswith('f_doc_'):
            tg = cmd[6:]
            name = {'swriter': 'Text Document', 'scalc': 'Spreadsheet', 
                'simpress': 'Presentation', 'sdraw': 'Drawing'}.get(tg, None)
            if tg:
                self.cast.execute_macro("bundle.py", "inspect_new_document", "extension", tg)
        elif cmd == 'f_mri':
            if self.cast.main.current == None: return
            self.cast.execute_macro("bundle.py", "duplicate_mri_window", "extension")
        elif cmd == 'f_basicide':
            status = call_dispatch(
                self.cast.ctx, self.cast.desktop, '.uno:BasicIDEAppear')
        elif cmd == 'f_calc':
            import mytools_Mri.output
            mytools_Mri.output.Mri_output_calc(self.cast)
        elif cmd == 'f_html':
            import mytools_Mri.output
            mytools_Mri.output.Mri_output_html(self.cast.main)
        elif cmd == 'f_close':
            try:
                status = call_dispatch(
                    self.cast.ctx, self.cast.frame, '.uno:CloseWin')
            except Exception as e:
                print(e)
                traceback.print_exc()
    
    def open_help(self):
        """ Try to open the window of online help. """
        help_exists = get_configvalue(
            self.cast.ctx, '/org.openoffice.Office.SFX', 'Help')
        
        lang_type = get_configvalue(self.cast.ctx,
            '/org.openoffice.Setup/L10N', 'ooLocale')
        if not lang_type:
            lang_type = get_configvalue(self.cast.ctx,
                '/org.openoffice.Office.Linguistic/General', 'DefaultLocale')
        
        if not help_exists:
            # check existence of help files on LibreOffice
            path = get_configvalue(
                self.cast.ctx, "/org.openoffice.Office.Common/Path/Current", "Help")
            try:
                path = create_service(self.cast.ctx, 
                    "com.sun.star.util.PathSubstitution").substituteVariables(path, True)
                sfa = create_service(self.cast.ctx, "com.sun.star.ucb.SimpleFileAccess")
                help_exists = sfa.exists(path + "/main_transform.xsl") and \
                              sfa.getFolderContents(path + "/" + lang_type, False)
            except Exception as e:
                print(e)
                pass
        if not help_exists or \
            (isinstance(help_exists, tuple) and \
                any((i.endswith("contents.js") for i in help_exists))):
            # show external webpage in the local webbrowser
            self.cast.main.web.open_url("https://github.com/hanya/MRI/wiki")
            return
        system_type = get_configvalue(self.cast.ctx,
            '/org.openoffice.Office.Common/Help', 'System')
        if not system_type:
            system_type = 'WIN'
        from mytools_Mri.values import MRI_ID
        hpage = ('vnd.sun.star.help://shared/%s%%2Findex.xhp?Language=' % MRI_ID) + \
                    "%s&System=%s#bm_idindex" % (lang_type, system_type)
        help_frame = open_help(self.cast.desktop,hpage)
        if not help_frame:
            call_dispatch(self.cast.ctx,self.cast.desktop, '.uno:HelpIndex')
            help_frame = open_help(self.cast.desktop,hpage)
            if not help_frame:
                return self.cast.error("Faild to open help files. \n" + \
                    " Help system is not supported by the application.")
        call_dispatch(self.cast.ctx,help_frame,hpage)
    
    def about_MRI(self):
        """ Show about message. """
        from mytools_Mri.values import MRINAME, MRI_HOME, MRI_ID
        from mytools_Mri.tools import get_package_version
        version = get_package_version(self.cast.ctx, MRI_ID)
        txt = []
        txt.append("%s\tversion: %s \n" % (MRINAME, version))
        txt.append("Home:\n%s" % MRI_HOME)
        txt.append("\n\nPython %s" % sys.version)
        self.cast.message("\n".join(txt), MRINAME)
    
    def macros_menu(self, menu, mid, cmd):
        """ Macro entry is selected. """
        path = cmd[2:]
        try:
            file_name, func_name = path.split("$", 2)
            if not func_name:
                raise Exception()
        except:
            self.cast.status("function name is not specified: \n%s" % path)
            return
        self.cast.execute_macro(file_name, func_name)
    
    def execute_macro(self, menu, mid, cmd):
        """ Execute selected macro. """
        if cmd.startswith("e_extension"):
            context = "extension"
            file_name, func_name = cmd[12:].split("$", 2)
        elif cmd.startswith("e_user"):
            context = "user"
            file_name, func_name = cmd[7:].split("$", 2)
        self.cast.execute_macro(file_name, func_name, context)


class ComponentWindowListener(unohelper.Base, XEventListener):
    """ Detect window closing and cleaning. """
    
    def __init__(self,cast):
        self.cast = cast
    
    def disposing(self, ev):
        try:
            cast = self.cast
            config = cast.config
            removeListeners(cast, config.grid, config.use_tab)
            cast.listeners = None
            cast.splitter.dispose()
            if config.use_tab:
                subcont = self.cast.cont.getControl("subcont")
                try:
                    for control in subcont.getControls():
                        for c in control.getControls():
                            control.removeControl(c)
                            c.dispose()
                        subcont.removeControl(control)
                        control.dispose()
                    self.cast.cont.removeControl(subcont)
                    subcont.dispose()
                except Exception as e:
                    print(e)
            cast.config = None
            cast.engine = None
            cast.cont = None
            cast.pages = None
            menu = cast.menu
            menu.getPopupMenu(0).setPopupMenu(0, None)
            menu.getPopupMenu(0).setPopupMenu(1, None)
            menu.getPopupMenu(1).setPopupMenu(5, None)
            for i in range(7):
                menu.setPopupMenu(i, None)
            cast.menu = None
            cast.window.setMenuBar(None) # !
            cast.window = None
            cast.dlg = None
            cast.splitter = None
            call_dispatch(self.cast.ctx, self.cast.frame, '.uno:CloseDoc')
            cast.frame = None
            self.cast = None
            if cast.status_eraser:
                cast.status_eraser.cancel()
        except Exception as e:
            print(e)


def set_listeners(self, use_grid=False, use_tab=False):
    from mytools_Mri.ui.frame import get_filler
    cont = self.cont
    gc = cont.getControl
    subcont = gc("subcont")
    gsc = subcont.getControl
    listeners = self.listeners
    ctl = self.window
    listener = WindowListener(self, use_tab)
    ctl.addWindowListener(listener)
    listeners['win'] = listener
    
    cwl = ComponentWindowListener(self)
    cont.addEventListener(cwl)
    listeners['cont'] = cwl
    
    listener = ButtonListener(self)
    listeners['btn'] = listener
    
    gc('btn_ref').addActionListener(listener)
    gc('btn_search').addActionListener(listener)
    gc('btn_back').addActionListener(listener)
    gc('btn_forward').addActionListener(listener)
    gc('btn_index_acc').addActionListener(listener)
    gc('btn_name_acc').addActionListener(listener)
    gc('btn_tree').addActionListener(listener)
    
    if use_tab:
        tab = subcont.getControl('tab')
        tab_pages = tab.getControls()
        info_0 = tab_pages[0].getControl('info_0')
        info_1 = tab_pages[1].getControl('info_1')
        info_2 = tab_pages[2].getControl('info_2')
        info_3 = tab_pages[3].getControl('info_3')
        if hasattr(tab, "addTabPageContainerListener"):
            from mytools_Mri.ui.tab import TabPageListener
            listener = TabPageListener(self)
            tab.addTabPageContainerListener(listener)
        elif hasattr(tab, "addTabPageListener"):
            from mytools_Mri.ui.tab import TabPageListener
            listener = TabPageListener(self)
            tab.addTabPageListener(listener)
        else:
            from mytools_Mri.ui.tab import TabListener
            listener = TabListener(self)
            tab.addTabListener(listener)
        listeners['tab'] = listener
    else:
        info_0 = gsc('info_0')
        info_1 = gsc('info_1')
        info_2 = gsc('info_2')
        info_3 = gsc('info_3')
        ctl = cont.getControl('list_category')
        listener = ListScopeListener(self)
        ctl.addItemListener(listener)
        listeners['list_category'] = listener
    
    listener2 = KeyListener(self, use_grid)
    listeners['key'] = listener2
    info_0.addKeyListener(listener2)
    info_1.addKeyListener(listener2)
    info_2.addKeyListener(listener2)
    info_3.addKeyListener(listener2)
    
    if use_grid:
        from mytools_Mri.ui.grid import GridInfoListener
        listener = GridInfoListener(self)
        listeners['grid_info'] = listener
        info_2.addMouseListener(listener)
        info_3.addMouseListener(listener)
    else:
        listener = EditInfoListener(self)
    listeners['info'] = listener
    info_0.addMouseListener(listener)
    info_1.addMouseListener(listener)
    
    ctl = cont.getControl('list_hist')
    listener = ListHistoryListener(self)
    ctl.addItemListener(listener)
    listeners['list_hist'] = listener
    
    listener = SplitterMouseListener(self, use_tab)
    self.splitter.addMouseListener(listener)
    self.splitter.addMouseMotionListener(listener)
    
    if not use_grid:
        get_filler(info_0).addMouseListener(listener)
        get_filler(info_1).addMouseListener(listener)
        get_filler(info_2).addMouseListener(listener)
        get_filler(info_3).addMouseListener(listener)
    
    filler = get_filler(cont.getControl('edit_code'))
    if filler: filler.addMouseListener(listener)
    listeners['splitter'] = listener
    
    listener = MenuListener(self)
    listeners['menu'] = listener
    menu = self.menu
    menu.addMenuListener(listener)
    for i in range(7):
        menu.getPopupMenu(i).addMenuListener(listener)
    menu.getPopupMenu(0).getPopupMenu(0).addMenuListener(listener)
    menu.getPopupMenu(0).getPopupMenu(1).addMenuListener(listener)
    menu.getPopupMenu(1).getPopupMenu(5).addMenuListener(listener)
    return

# remove all listeners
def removeListeners(self, use_grid=False, use_tab=False):
    if not self.window: return
    try:
        listeners = self.listeners
        ctl = self.window
        ctl.removeWindowListener(listeners['win'])
        
        ctls = self.cont.getControls()
        if ctls:
            cont = self.cont
            gc = cont.getControl
            subcont = cont.getControl('subcont')
            gsc = subcont.getControl
            listener = listeners['btn']
            gc('btn_ref').removeActionListener(listener)
            gc('btn_search').removeActionListener(listener)
            gc('btn_back' ).removeActionListener(listener)
            gc('btn_forward').removeActionListener(listener)
            
            if use_tab:
                tab = subcont.getControl("tab")
                tab_pages = tab.getControls()
                info_0 = tab_pages[0].getControl('info_0')
                info_1 = tab_pages[1].getControl('info_1')
                info_2 = tab_pages[2].getControl('info_2')
                info_3 = tab_pages[3].getControl('info_3')
            else:
                info_0 = gsc('info_0')
                info_1 = gsc('info_1')
                info_2 = gsc('info_2')
                info_3 = gsc('info_3')
            
            if use_tab:
                if hasattr(tab, "removeTabPageContainerListener"):
                    tab.removeTabPageContainerListener(listeners['tab'])
                elif hasattr(tab, "removeTabPageListener"):
                    tab.removeTabPageListener(listeners['tab'])
                else:
                    tab.removeTabListener(listeners['tab'])
            else:
                cont.getControl('list_category').removeItemListener(listeners['list_category'])
            
            mouse_listener = listeners['info']
            key_listener = listeners['key']
            info_0.removeMouseListener(mouse_listener)
            info_0.removeKeyListener(key_listener)
            info_1.removeMouseListener(mouse_listener)
            info_1.removeKeyListener(key_listener)
            info_2.removeMouseListener(mouse_listener)
            info_2.removeKeyListener(key_listener)
            info_3.removeMouseListener(mouse_listener)
            info_3.removeKeyListener(key_listener)
            
            del mouse_listener, key_listener
            cont.getControl('list_hist').removeItemListener(listeners['list_hist'])
        listener = listeners['splitter']
        self.splitter.removeMouseListener(listener)
        self.splitter.removeMouseMotionListener(listener)
        
        menu = self.menu
        listener = self.listeners['menu']
        menu.removeMenuListener(listener)
        for i in range(7):
            menu.getPopupMenu(i).removeMenuListener(listener)
        menu.getPopupMenu(0).getPopupMenu(0).removeMenuListener(listener)
        menu.getPopupMenu(0).getPopupMenu(1).removeMenuListener(listener)
        menu.getPopupMenu(1).getPopupMenu(5).removeMenuListener(listener)
    except Exception as e:
        print(e)
        traceback.print_exc()

