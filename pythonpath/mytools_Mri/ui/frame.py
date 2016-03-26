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

import traceback
import mytools_Mri.values
import mytools_Mri.tools

from com.sun.star.awt.MenuItemStyle import CHECKABLE as MIS_CHECKABLE, \
    AUTOCHECK as MIS_AUTOCHECK, RADIOCHECK as MIS_RADIOCHECK
from com.sun.star.awt.ScrollBarOrientation import VERTICAL as SBO_VERTICAL
from com.sun.star.awt.WindowClass import SIMPLE as WC_SIMPLE
from com.sun.star.awt.PosSize import POSSIZE as PS_POSSIZE, SIZE as PS_SIZE
from com.sun.star.awt.WindowAttribute import BORDER as WA_BORDER, SHOW as WA_SHOW
from com.sun.star.style.VerticalAlignment import MIDDLE as VA_MIDDLE
from com.sun.star.accessibility.AccessibleRole import FILLER as AR_FILLER
from com.sun.star.view.SelectionType import SINGLE as ST_SINGLE
from com.sun.star.awt import Rectangle, WindowDescriptor
from com.sun.star.beans import NamedValue


def _create_frame(self, ctx, smgr, ps):
    self.frame = smgr.createInstanceWithContext(
        'com.sun.star.frame.TaskCreator', ctx).createInstanceWithArguments(
        (NamedValue('FrameName', mytools_Mri.values.MRINAME), 
        NamedValue('PosSize', Rectangle(*ps))))
    frame = self.frame
    self.window = frame.getContainerWindow()
    desktop = smgr.createInstanceWithContext(
        'com.sun.star.frame.Desktop', ctx)
    frame.setTitle(create_window_name(desktop))
    frame.setCreator(desktop)
    desktop.getFrames().append(frame)
    return frame, self.window


def _create_menu(self, ctx, smgr, config, window, use_grid=False):
    menubar = smgr.createInstanceWithContext(
        'com.sun.star.awt.MenuBar',ctx)
    menubar_insert = menubar.insertItem
    menubar.removeItem(0,menubar.getItemCount())
    menubar_insert(0,'~File',0,0)
    menubar_insert(1,'~Tools',0,1)
    menubar_insert(2,'T~argets',0,2)
    menubar_insert(4,'~Mode',0,3)
    menubar_insert(6,'Mac~ros',0,4)
    menubar_insert(5,'~Window',0,5)
    menubar_insert(3,'~Help',0,6)
    menubar.setCommand(2,'targets')
    menubar.setCommand(5,'window')
    menubar.setCommand(6,'macros')
    window.setMenuBar(menubar)
    self.menu = menubar
    
    cpm = create_popupmenu
    filemenu = cpm(smgr,ctx,(
        (0,'~New',0,0,'mytools.Mri:f_new'),
        (None,1),
        (1,'~Output',0,2,'mytools.Mri:f_output'),
        (None,3),
        (7, '~Rename',0,4,'mytools.Mri:e_extension?bundle.py$change_title'),
        (None, 6), 
        (6,'~Close',0,7,'mytools.Mri:f_close') ) )
    newmenu = cpm(smgr,ctx,(
        (5,'~Basic IDE',0,1,'mytools.Mri:f_basicide'),
        (None,2),
        (0,'~Text Document',0,3,'mytools.Mri:f_doc_swriter'),
        (1,'~Spreadsheet',0,4,'mytools.Mri:f_doc_scalc'),
        (2,'~Presentation',0,5,'mytools.Mri:f_doc_simpress'),
        (3,'~Drawing',0,6,'mytools.Mri:f_doc_sdraw') ) )
    filemenu.setPopupMenu(0,newmenu)
    outputmenu = cpm(smgr,ctx,(
        (0,'~Spreadsheet',0,0,'mytools.Mri:f_calc'), 
        (2,'~HTML', 0, 10, 'mytools.Mri:f_html'),))
    filemenu.setPopupMenu(1,outputmenu)
    
    targetsmenu = cpm(smgr,ctx,(
        (0,'~Desktop',0,0,'mytools.Mri:e_extension?bundle.py$inspect_desktop'),
        (1,'Service~Manager',0,1,'mytools.Mri:e_extension?bundle.py$inspect_service_manager'),
        (2,'~Service',0,2,'mytools.Mri:e_extension?bundle.py$inspect_service'),
        (3,'S~truct',0,3,'mytools.Mri:e_extension?bundle.py$inspect_struct'),
        (4,'~Configuration',0,4,'mytools.Mri:e_extension?bundle.py$inspect_configuration'),
        (None,5)))
    
    mis_autocheck = MIS_AUTOCHECK
    toolsmenu = cpm(smgr,ctx,(
        (0,'~Sort A-z',mis_autocheck,0,'mytools.Mri:t_sort'),
        (1,'~Abbreviated',mis_autocheck,1,'mytools.Mri:t_abbr'),
        (6, "~Pseud Property", mis_autocheck, 2,"mytools.Mri:t_pseud"),
        (None,3),
        (3,'~Show Labels',mis_autocheck,4,'mytools.Mri:t_showlabels'),
        (None,5),
        (5,'C~ode',0,6,'mytools.Mri:t_code'),
        (None,7),
        (4,'~Configuration...',0,8,'mytools.Mri:t_config')))
    toolsmenu.checkItem(0,config.sorted)
    toolsmenu.checkItem(1,config.abbrev)
    toolsmenu.checkItem(6,not config.property_only)
    toolsmenu.checkItem(3,config.show_labels)
    if use_grid:
        toolsmenu.enableItem(3, False)
    
    entries = [
        (1,'~Code',mis_autocheck,0,'mytools.Mri:t_showcode'),
        (None,1),
        (2,'~Pseud Property',mis_autocheck,2,'mytools.Mri:t_pseudproperty'),
        (None,3)]
    codemenu = cpm(smgr,ctx,entries)
    toolsmenu.setPopupMenu(5,codemenu)
    codemenu.checkItem(1,config.show_code)
    codemenu.checkItem(2,config.use_pseud_props)
    
    modemenu = cpm(smgr,ctx,(
        (0, '~Get',MIS_RADIOCHECK,0, 'mytools.Mri:m_get'),
        (1, '~Set',MIS_RADIOCHECK,1, 'mytools.Mri:m_set')))
    modemenu.checkItem(0,self.property_mode)
    modemenu.checkItem(1,not self.property_mode)
    
    macrosmenu = cpm(smgr,ctx,())
    windowmenu = cpm(smgr,ctx,(
        (1,'~New Window',0,0,'mytools.Mri:e_extension?bundle.py$duplicate_mri_window'),
        (2,'~Close Window',0,1,'mytools.Mri:f_close'),  
        (None,2),))
    helpmenu = cpm(smgr,ctx,(
        (0,'~MRI Help',0,1,'mytools.Mri:h_doc'),
        (1,'What\'s ~This?',0,2,'mytools.Mri:h_what'),
        (None,3),
        (2,'~About MRI',0,4,'mytools.Mri:h_about'),))
    menubar_set_popup = menubar.setPopupMenu
    menubar_set_popup(0,filemenu)
    menubar_set_popup(1,toolsmenu)
    menubar_set_popup(2,targetsmenu)
    menubar_set_popup(3,helpmenu)
    menubar_set_popup(4,modemenu)
    menubar_set_popup(5,windowmenu)
    menubar_set_popup(6,macrosmenu)
    # ToDo set modifier keys


def _create_window(ctx, smgr, frame, window, toolkit, ui):
    cont = smgr.createInstanceWithContext( 
        'com.sun.star.awt.UnoControlContainer', ctx)
    cont_model = smgr.createInstanceWithContext( 
        'com.sun.star.awt.UnoControlContainerModel', ctx)
    cont.setModel(cont_model)
    cont.createPeer(toolkit,window)
    cont.setPosSize(0,0,500,400,PS_POSSIZE)
    cont_model.BackgroundColor = get_backgroundcolor(window, 0xFAFAFA)
    try:
        import mytools_Mri.ui.controller
        controller = mytools_Mri.ui.controller.MRIUIController(frame, None)
        controller.set_ui(ui)
        frame.setComponent(cont,controller)
    except Exception as e:
        print(("Error during to set controller: " + str(e)))
    return cont


def _create_controls(ctx, smgr, cont, ps, use_tab):
    width = ps[2]
    height = ps[3]
    cctrl = create_control
    x_corr = 0
    if use_tab:
        x_corr -= 80
    
    label_status = cctrl( 
        smgr,ctx, 'FixedText', 2,height -20,width -320,20, 
        ('FontHeight','HelpURL','Label','VerticalAlign'), 
        (8,'mytools.Mri:label_status','',VA_MIDDLE))
    
    btn_ref = cctrl(
        smgr,ctx, 'Button', 290 + x_corr,3,105,30, 
        ('FontHeight','HelpText','HelpURL','Label',), 
        (8,'Open IDL Reference (Ctrl+I)','mytools.Mri:btn_ref','ID~L Ref.',))
    
    if not use_tab:
        list_category = cctrl(
            smgr,ctx, 'ListBox', 0,0,80,60, 
            ('FontHeight','HelpURL','MultiSelection','ReadOnly',), 
            (8,'mytools.Mri:list_category',False,False,))
    
    edit_type = cctrl( #show typeinfo from CoreReflection
        smgr,ctx, 'Edit', 85 + x_corr,5,200,25,
        ('Align','Border','FontHeight','HelpText','HelpURL',
            'HideInactiveSelection','ReadOnly','Tabstop',),
        (1,2,8,'Type of target','mytools.Mri:edit_type',True,True,False,))
    edit_in = cctrl( #show implementationName
        smgr,ctx, 'Edit', width -315, height-20, 200, 20,
        ('Align','Border','FontHeight','HelpText','HelpURL','ReadOnly','Tabstop',),
        (1,0,8,'Implementation name of the target.','mytools.Mri:edit_in',True,False,))
    list_hist = cctrl( 
        smgr,ctx, 'ListBox', 85 + x_corr,35,175,25, 
        ('Dropdown','FontHeight','HelpText','HelpURL','LineCount','MultiSelection',), 
        (True, 8, 'History','mytools.Mri:list_hist',10,False,))
    btn_search = cctrl( 
        smgr,ctx, 'Button', width -39, height-20, 38, 20,
        ('FontHeight','HelpText','HelpURL','Label','Tabstop',), 
        (8,'Search','mytools.Mri:btn_search','S',True,))
    edit_search = cctrl( 
        smgr,ctx, 'Edit', width -110, height -20,68,20, 
        ('Border','HelpText','FontHeight','HelpURL','Tabstop',), 
        (2,'Search string',8,'mytools.Mri:edit_search',True,))
    btn_back = cctrl( 
        smgr,ctx, 'Button', 290 + x_corr,35,50,25, 
        ('FontHeight','HelpText','HelpURL','Label',), 
        (8,'Go back (Alt+LEFT)','mytools.Mri:btn_back','~<',))
    btn_forward = cctrl( 
        smgr,ctx, 'Button', 345 + x_corr,35,50,25, 
        ('FontHeight','HelpText','HelpURL','Label',), 
        (8,'Go forward (Alt+RIGHT)','mytools.Mri:btn_forward','~>',))
    
    btn_tree = cctrl( 
        smgr,ctx, 'Button', 85 + x_corr + 176,35,24,25, 
        ('FontHeight','HelpText','HelpURL','Label',), 
        (8,'History tree','mytools.Mri:btn_tree','-',))
    
    btn_index_acc = cctrl( 
        smgr,ctx, 'Button', 400 + x_corr,35,50,25, 
        ('FontHeight','HelpText','HelpURL','Label', 'Toggle',), 
        (8,'Shortcut for css.container.XIndexAccess (Ctrl+U)', 
            'mytools.Mri:btn_index_acc','index', True,))
    
    btn_name_acc = cctrl( 
        smgr,ctx, 'Button', 455 + x_corr,35,50,25, 
        ('FontHeight','HelpText','HelpURL','Label', 'Toggle',), 
        (8,'Shortcut for css.container.XNamedAccess (Ctrl+N)',
            'mytools.Mri:btn_name_acc','name', True,))
    
    btn_index_acc.setEnable(False)
    btn_name_acc.setEnable(False)
    
    btn_ref.ActionCommand   = 'ref'
    btn_search.ActionCommand = 'search'
    btn_back.ActionCommand   = 'back'
    btn_forward.ActionCommand = 'forward'
    btn_tree.ActionCommand = 'history'
    btn_index_acc.ActionCommand = 'index'
    btn_name_acc.ActionCommand = 'name'
    
    ad = cont.addControl
    ad('btn_ref',btn_ref)
    if not use_tab:
        ad('list_category',list_category)
    ad('label_status',label_status)
    ad('edit_type',edit_type)
    ad('edit_in',edit_in)
    ad('list_hist',list_hist)
    ad('btn_back',btn_back)
    ad('btn_forward',btn_forward)
    ad('edit_search',edit_search)
    ad('btn_search',btn_search)
    ad('btn_tree', btn_tree)
    ad('btn_index_acc',btn_index_acc)
    ad('btn_name_acc',btn_name_acc)


def _create_code(ctx, smgr, cont, config, ps):
    edit_code = create_control( 
        smgr,ctx, 'Edit', 0,ps[3] -26,ps[2],0,
        ('Align','Border','FontHeight','HelpURL','HideInactiveSelection', 'HScroll',
            'MultiLine','ReadOnly','Tabstop','VScroll',),
        (0,2,9,'mytools.Mri:edit_code',
        False,True,True,False,False,True))
    edit_code.setVisible(config.show_code)
    cont.addControl('edit_code', edit_code)
    return edit_code

def _create_splitter(ctx, smgr, toolkit, cont, ps):
    spl = create_window(
        toolkit, cont.getPeer(), 
        WC_SIMPLE, 'splitter', WA_SHOW | WA_BORDER,
        0,ps[3] -26,ps[2],6)
    spl.setProperty('BackgroundColor', 0xEEEEEE)
    spl.setProperty('Border',1)
    spl.setProperty('BorderColor', 0xEEEEEE)
    return spl

def _create_edit2(page, name, help_url):
    model = page.getModel()
    edit_model = model.createInstance(
        "com.sun.star.awt.UnoControlEditModel")
    edit_model.setPropertyValues(
        ("Border", "HelpURL", "HideInactiveSelection", 
        "HScroll", "MultiLine", "ReadOnly", "VScroll"), 
        (1, help_url, False, True, True, True, True))
    model.insertByName(name, edit_model)
    return page.getControl(name)


def _create_info(ctx, smgr, subcont, width, height, use_grid, grid_type):
    """ Without tab control """
    subcont_model = subcont.getModel()
    inner_ps = subcont.getOutputSize()
    height = inner_ps.Height
    def _insert_info(name, help_url, pos):
        if use_grid:
            from mytools_Mri.ui.grid import _create_grid2
            ctrl = _create_grid2(ctx, smgr, subcont, name, help_url, pos, grid_type)
        else:
            ctrl = _create_edit2(subcont, name, help_url)
        ctrl.setPosSize(0, 0, width, height, PS_POSSIZE)
        return ctrl
    help_url = "mytools.Mri:edit_info"
    
    info_0 = _insert_info("info_0", help_url, 0)
    info_1 = _insert_info("info_1", help_url, 1)
    info_2 = _insert_info("info_2", help_url, 2)
    info_3 = _insert_info("info_3", help_url, 3)
    info_1.setVisible(False)
    info_2.setVisible(False)
    info_3.setVisible(False)
    return info_0, info_1, info_2, info_3


def _create_empty_container(ctx, smgr, parent):
    return smgr.createInstanceWithContext(
        "com.sun.star.awt.ContainerWindowProvider", ctx).createContainerWindow(
            mytools_Mri.values.MRI_DIR + "/dialogs/empty.xdl", 
            "", parent, None)


def _create_subcontainer(ctx, smgr, cont, width, height):
    """ Create empty container window. """
    subcont = _create_empty_container(ctx, smgr, cont.getPeer())
    subcont.setPosSize(0, 65, width, height, PS_POSSIZE)
    subcont.setVisible(True)
    cont.addControl("subcont", subcont)
    return subcont


def create_frame(self, ctx, smgr, config, use_grid=False, use_tab=False):
    """ Create main frame of the MRI window. """
    grid_type = config.__class__.GRID
    tab_type = config.__class__.TAB
    ps = list(map(int, config.pos_size.split(',')))
    
    frame, window = _create_frame(self, ctx, smgr, ps)
    toolkit = window.getToolkit()
    _create_menu(self, ctx, smgr, config, window, use_grid)
    
    ps[3] = window.OutputSize.Height # excepting menubar height
    if config.show_code:
        info_height = ps[3] -90
    else:
        info_height = ps[3] -85
    
    cont = _create_window(ctx, smgr, frame, window, toolkit, self)
    self.cont = cont
    #frame.getController().set_ui(self)
    _create_controls(ctx, smgr, cont, ps, use_tab)
    subcont = _create_subcontainer(ctx, smgr, cont, ps[2], info_height)
    _create_code(ctx, smgr, cont, config, ps)
    self.splitter = _create_splitter(ctx, smgr, toolkit, cont, ps)
    self.splitter.setVisible(config.show_code)
    if use_tab:
        from mytools_Mri.ui.tab import _create_tab2
        tab, info_0, info_1, info_2, info_3 = _create_tab2(
            ctx, smgr, subcont, ps[2], info_height, use_grid, grid_type, tab_type)
        list_category = None
    else:
        tab = None
        info_0, info_1, info_2, info_3 = _create_info(
            ctx, smgr, subcont, ps[2], info_height, use_grid, grid_type)
        list_category = cont.getControl('list_category')
        list_category.addItems( 
            ('Properties', 'Methods', 'Interfaces', 'Services'), 0)
        list_category.selectItemPos(0, True)
    if use_grid:
        columns = info_0.getModel().ColumnModel
        columns.getColumn(0).ColumnWidth = 12
        columns.getColumn(1).ColumnWidth = 12
        columns.getColumn(2).ColumnWidth = 6
        columns.getColumn(3).ColumnWidth = 3
        columns.getColumn(4).ColumnWidth = 5
    else:
        info_0.setFocus()
    
    window.setVisible(True)
    if use_tab:
        tab_out_size = tab.getControls()[0].getOutputSize()
        _width = tab_out_size.Width
        _height = tab_out_size.Height
        info_0.setPosSize(0, 0, _width, _height, PS_SIZE)
        info_1.setPosSize(0, 0, _width, _height, PS_SIZE)
        info_2.setPosSize(0, 0, _width, _height, PS_SIZE)
        info_3.setPosSize(0, 0, _width, _height, PS_SIZE)
    
    cgc = cont.getControl
    if use_grid:
        import mytools_Mri.ui.grid
        pages = mytools_Mri.ui.grid.GridUi(0, 
            [info_0, info_1, info_2, info_3], 
            list_category, 
            cgc('edit_code'), cgc('label_status'), 
            [get_editvscrollbar(info_0), get_editvscrollbar(info_1), 
            get_editvscrollbar(info_2), get_editvscrollbar(info_3)], 
            tab)
    else:
        import mytools_Mri.ui.pages
        pages = mytools_Mri.ui.pages.InfoUi(0, 
            [info_0, info_1, info_2, info_3], 
            list_category, 
            cgc('edit_code'), cgc('label_status'), 
            None, 
            tab)
    pages.set_ui_controls(
        cgc('edit_type'), cgc('edit_in'), 
        cgc('btn_index_acc'), cgc('btn_name_acc'), 
        cgc("edit_search"), cgc("list_hist"))
    self.pages = pages


# get target has the interface
def has_interface(target,interface):
    try:
        types = target.Types
        for ti in types:
            if ti.typeName == interface:
                return True
    except:
        pass
    return False


# get information edit's vertical scroll bar control
def get_editvscrollbar(edit):
    acedit = edit.getAccessibleContext()
    for idx in range(acedit.getAccessibleChildCount()):
        child = acedit.getAccessibleChild(idx)
        if has_interface(child,'com.sun.star.awt.XScrollBar'):
            if child.Orientation == SBO_VERTICAL:
                return child
    return None


def get_filler(edit):
    acedit = edit.getAccessibleContext()
    for idx in range(acedit.getAccessibleChildCount()):
        child = acedit.getAccessibleChild(idx)
        if has_interface(child,'com.sun.star.accessibility.XAccessible'):
            acc_child = child.getAccessibleContext()
            if acc_child.getAccessibleRole() == AR_FILLER:
                return child


# items [id,text,type,pos,command], if separator [-1,pos]
def create_popupmenu(smgr,ctx,items):
    menu = smgr.createInstanceWithContext('com.sun.star.awt.PopupMenu',ctx)
    menu_insert = menu.insertItem
    menu_set_command = menu.setCommand
    menu_insert_separator = menu.insertSeparator
    for item in items:
        if (not item[0] is None) and -1 < item[0]:
            menu_insert(item[0],item[1],item[2],item[3])
            menu_set_command(item[0],item[4])
        else:
            menu_insert_separator(item[1])
        #if len(item) >= 6 and item[5] is not None:
        #   menu.setAcceleratorKeyEvent(item[0], item[5])
    return menu


# create control by its type with property values
def create_control(smgr, ctx, ctrltype, x, y, width, height, names, values):
    ctrl = smgr.createInstanceWithContext( 
        'com.sun.star.awt.UnoControl%s' % ctrltype, ctx)
    ctrl_model = smgr.createInstanceWithContext( 
        'com.sun.star.awt.UnoControl%sModel' % ctrltype, ctx)
    ctrl_model.setPropertyValues(names, values)
    ctrl.setModel(ctrl_model)
    ctrl.setPosSize(x, y, width, height, PS_POSSIZE)
    return ctrl


def create_window(toolkit, parent, wtype, service, attrs, x, y, width, height):
    return toolkit.createWindow(
        WindowDescriptor(wtype, service, parent, -1, 
        Rectangle(x, y, width, height), attrs))


# create identical window name
def create_window_name(desktop):
    mri_name = mytools_Mri.values.MRINAME
    frames = desktop.getFrames()
    count = 0
    for i in range(frames.getCount()):
        if frames.getByIndex(i).getName() == mri_name:
            count = count + 1
    title = [mri_name]
    while count > 0:
        title[0] = '%s - %s' % (mri_name,(count +1))
        for i in range(frames.getCount()):
            frame = frames.getByIndex(i)
            if frame.getName() == mri_name and frame.getTitle() != title[0]:
                count = -2
                break
        count = count + 1
    return title[0]


def get_backgroundcolor(window, defalut=0xeeeeee):
    """ Get background color through accesibility api. """
    import sys
    try:
        acc = window.getAccessibleContext()
        if sys.platform.startswith("win"):
            return acc.getAccessibleChild(0).getBackground()
        else:
            return acc.getBackground()
    except:
        pass
    return defalut

