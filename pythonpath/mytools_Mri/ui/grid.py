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

from com.sun.star.awt import XMouseListener, KeyEvent, Point, Rectangle
from com.sun.star.awt.MouseButton import RIGHT as MB_RIGHT, LEFT as MB_LEFT
from mytools_Mri.ui import transferable

class KeyModifier(object):
    from com.sun.star.awt.KeyModifier import MOD1, MOD2, SHIFT

titles = (
    ('Name', 'Value Type', 'Value', 'Info.', 'Attr.'), #, 'Handle'), 
    ('Name', 'Arguments', 'Return Type', 'Declaring Class', 'Exceptions'), 
    ('Interfaces',), 
    ('Services',)
)

def _create_grid2(ctx, smgr, page, name, help_url, title_id, grid_type):
    #from com.sun.star.awt import FontDescriptor
    model = page.getModel()
    grid_model = model.createInstance(
        "com.sun.star.awt.grid.UnoControlGridModel")
    grid_model.setPropertyValues(
        ("BackgroundColor", "Border", "HScroll", "SelectionModel", 
        "ShowColumnHeader", "ShowRowHeader", "VScroll"), 
        (page.StyleSettings.DialogColor, 0, True, 1, True, False, True))
    #desc = FontDescriptor()
    #desc.Name = "DejaVu Sans Mono"
    #grid_model.FontDescriptor = desc
    if grid_type == 1:
        grid_model.EvenRowBackgroundColor = 0xfafafa
    else:
        grid_model.RowBackgroundColors = (0xffffff, 0xfafafa)
    if not grid_model.GridDataModel:
        data = smgr.createInstanceWithContext(
            "com.sun.star.awt.grid.DefaultGridDataModel", ctx)
        grid_model.GridDataModel = data
    if grid_type != 2:
        grid_model.GridDataModel.addRow('', titles[title_id])
    columns = grid_model.ColumnModel
    if not columns:
        columns = smgr.createInstanceWithContext(
            "com.sun.star.awt.grid.DefaultGridColumnModel", ctx)
    for title in titles[title_id]:
        column = smgr.createInstanceWithContext(
            "com.sun.star.awt.grid.GridColumn", ctx)
        column.Title = title
        columns.addColumn(column)
    grid_model.ColumnModel = columns
    model.insertByName(name, grid_model)
    return page.getControl(name)

# ToDo reconstruct
class SimpleGridInfoListener(unohelper.Base, XMouseListener):
    def __init__(self, cast):
        self.cast = cast
        self.popup = None
        
        import mytools_Mri.tools
        self.use_point = mytools_Mri.tools.check_method_parameter(self.cast.ctx, 
            "com.sun.star.awt.XPopupMenu", "execute", 1, "com.sun.star.awt.Point")
        
    def disposing(self,ev): pass
    def mouseReleased(self,ev): pass
    def mouseEntered(self,ev): pass
    def mouseExited(self,ev): pass
    def mousePressed(self, ev):
        if ev.Buttons == MB_RIGHT and ev.ClickCount == 1:
            if not self.popup:
                self.popup = self._create_popup()
                if not self.popup: return
            
            grid_model = ev.Source.getModel()
            if grid_model.ShowColumnHeader:
                if hasattr(grid_model, "ColumnHeaderHeight"):
                    header_height = grid_model.ColumnHeaderHeight
                else:
                    header_height = grid_model.ColumnModel.ColumnHeaderHeight
                if header_height is None: header_height = 20
                if ev.Y <= header_height:
                    return
            try:
                index = self.cast.pages.get_active()
                if index == 0:
                    # properties
                    self._update_popup_states(((2, True), (4, True), (8, False), (512, True)))
                    properties_title = ('Name', 'Value Type', 'Value', 'Info.', 'Attr.')
                    copy_cell_popup = self.popup.getPopupMenu(512)
                    for i, label in zip(range(513, 518), properties_title):
                        copy_cell_popup.setItemText(i, label)
                elif index == 1:
                    # methods
                    self._update_popup_states(((2, False), (4, False), (8, True), (512, True)))
                    
                    methods_title = ('Name', 'Arguments', 'Return Type', 'Declaring Class', 'Exceptions')
                    copy_cell_popup = self.popup.getPopupMenu(512)
                    for i, label in zip(range(513, 518), methods_title):
                        copy_cell_popup.setItemText(i, label)
                else:
                    self._update_popup_states(((2, False), (4, False), (8, False), (512, False)))
                
                pos = ev.Source.getPosSize()
                if self.use_point:
                    _pos = Point(pos.X + ev.X, pos.Y + ev.Y)
                else:
                    _pos = Rectangle(pos.X + ev.X, pos.Y + ev.Y, 0, 0)
                n = self.popup.execute(ev.Source.getPeer(), _pos, 0)
                if n > 0:
                    self.do_command(n)
            except Exception as e:
                print(e)
    
    def do_command(self, n):
        if n == 0x2 or n == 0x8:
            # get value and call method
            self.cast.info_action()
        elif n == 0x4:
            mode = self.cast.property_mode
            self.cast.property_mode = False # to set the value
            try:
                self.cast.info_action()
            except:
                pass
            self.cast.property_mode = mode
        elif n == 32:
            # idl
            self.cast.open_idl_reference()
        elif n == 256 or 513 <= n <= 517 or n == 520:
            # copy
            if n == 256:
                word = self.cast.pages.get_first_word()
            elif 513 <= n <= 517:
                word = self.cast.pages.get_cell(column_index=(n - 513))
            elif n == 520:
                word = ' '.join(self.cast.pages.get_row())
            else:
                return
            try:
                transferable.set_text_to_clipboard(self.cast.ctx, word)
            except Exception as e:
                print(e)
    
    def _update_popup_states(self, states):
        if self.popup:
            for state in states:
                self.popup.enableItem(state[0], state[1])
    
    def _create_popup(self):
        """ [ [id, pos, type, 'label', "command", acc_key], [] ] """
        items = [
            [2, 0, 0, 'Get Value', ':GetValue', None], 
            [4, 1, 0, 'Set Value', ':SetValue', None], 
            [8, 2, 0, 'Call Method', ':CallMethod', None], 
            [-1, 3], 
            [32, 4, 0, 'IDL Ref.', ':IDLRef', None], 
            [None, 5], 
            [256, 6, 0, 'Copy', ':Copy', None], 
            [512, 7, 0, 'Copy Cell', ':CopyCell', None]
        ]
        copy_cell_items = [
            [513, 0, 0, '', ':CopyCell0', None], 
            [514, 1, 0, '', ':CopyCell1', None], 
            [515, 2, 0, '', ':CopyCell2', None], 
            [516, 3, 0, '', ':CopyCell3', None], 
            [517, 4, 0, '', ':CopyCell4', None], 
            [None, 5], 
            [520, 6, 0, 'All', ':CopyCellAll', None]
        ]
        
        import mytools_Mri.ui.tools
        popup = mytools_Mri.ui.tools.create_popupmenu(self.cast.ctx, items)
        copy_cell_popup = mytools_Mri.ui.tools.create_popupmenu(self.cast.ctx, copy_cell_items)
        popup.setPopupMenu(512, copy_cell_popup)
        popup.hideDisabledEntries(True)
        return popup


class GridInfoListener(SimpleGridInfoListener):
    def __init__(self, cast):
        SimpleGridInfoListener.__init__(self, cast)
    
    def mousePressed(self, ev):
        try:
            if ev.Buttons == MB_LEFT and ev.ClickCount == 2:
                category = self.cast.pages.get_active()
                mod = ev.Modifiers
                if mod == KeyModifier.SHIFT:
                    return
                if category == 0:
                    if mod == KeyModifier.MOD2 or \
                        mod == (KeyModifier.SHIFT | KeyModifier.MOD1):
                        mode = self.cast.property_mode
                        self.cast.property_mode = not mode
                        self.cast.info_action(category)
                        self.cast.property_mode = mode
                    else:
                        if mod == KeyModifier.MOD1:
                            self.cast.main.open_new = True
                        self.cast.info_action(category)
                elif category == 1:
                    if mod == KeyModifier.SHIFT:
                        self.cast.main.open_new = True
                    self.cast.info_action(category)
            elif ev.Buttons == MB_RIGHT and ev.ClickCount == 1:
                SimpleGridInfoListener.mousePressed(self, ev)
        except Exception as e:
            print(e)
            import traceback
            traceback.print_exc()

import re
from mytools_Mri.ui.pages import PagesBase, PageStatus, Ui

class GridPagesBase(PagesBase):
    """ Basis of informations shown in grid controls. """
    def __init__(self, active, ctrls, changer, scrolls, tab):
        PagesBase.__init__(self, active, ctrls, changer, tab)
        self.scrolls = scrolls
    
    def __getitem__(self, index):
        return ''
    
    def _re_set_size(self, index):
        grid = self.ctrls[index]
        size = grid.getPosSize()
        grid.setPosSize(0, 0, 0, size.Height +1, 8)
        grid.setPosSize(0, 0, 0, size.Height, 8)
    
    def set_properties(self, index, names, values):
        pass
    
    def set_font(self, name, height):
        """does not effected."""
        pass
    
    def _get_grid(self, index=None):
        if index == None: index = self.get_active()
        return self.ctrls[index]
    
    def get_current_line(self, index=None, r=None):
        return self.get_first_word()
    
    def get_first_word(self, index=None):
        return self.get_cell(index)
    
    def select_row(self, index, row_index):
        ctrl = self._get_grid(index)
        try:
            ctrl.deselectAllRows()
            ctrl.selectRow(row_index)
            self.show_row(index, row_index)
        except Exception as e:
            print(e)
    
    def show_row(self, index, row_index):
        """ make to show the row. """
        if index is None: index = self.get_active()
        scroll = self.scrolls[index]
        if not scroll: return
        if row_index < scroll.getValue():
            scroll.setValue(row_index)
        elif row_index >= (scroll.getBlockIncrement() + scroll.getValue()):
            scroll.setValue(
                row_index - scroll.getBlockIncrement() + 1)


import mytools_Mri.config

class GridPages(GridPagesBase):
    """ Keeps grid controls. """
    
    TAG_EXP = "^\(([^\)]*?)\)"
    
    def select_current_sentence(self, index=None):
        pass
    
    def select_current_line(self, index=None):
        pass
    
    def get_selected(self, index=None):
        ret = ""
        ctrl = self._get_grid(index)
        row_index = self._get_selected(ctrl)
        if not row_index is None:
            data_model = ctrl.getModel().GridDataModel
            ret = self._get_cell_data(data_model, 0, row_index)
        return ret
    
    def get_cell(self, index=None, row_index=None, column_index=0):
        ret = ''
        ctrl = self._get_grid(index)
        row_index = self._get_selected(ctrl)
        if not row_index is None:
            data_model = ctrl.getModel().GridDataModel
            ret = self._get_cell_data(data_model, column_index, row_index)
        return ret
    
    def get_row(self, index=None, row_index=None):
        ctrl = self._get_grid(index)
        row_index = self._get_selected(ctrl)
        if not row_index is None:
            data_model = ctrl.getModel().GridDataModel
            return self._get_row(data_model, row_index)
        return []
    
    def get_tag(self, index=None):
        ret = ''
        ctrl = self._get_grid(index)
        row_index = self._get_selected(ctrl)
        if not row_index is None:
            data_model = ctrl.getModel().GridDataModel
            regexp = re.compile(self.TAG_EXP)
            ret = self._search_in_first_column(data_model, row_index, regexp)
        return ret
    
    def search(self, search_text, index=None):
        start_row = 0
        ctrl = self._get_grid(index)
        row_index = self._get_selected(ctrl)
        if not row_index is None:
            start_row = row_index
        data_model = ctrl.getModel().GridDataModel
        n = self._search(data_model, start_row, search_text)
        if not n is None:
            self.select_row(index, n)
    
    def __init__(self, active, ctrls, changer, scrolls, tab):
        GridPagesBase.__init__(self, active, ctrls, changer, scrolls, tab)
    
    if mytools_Mri.config.Config.GRID == 1:
        def __setitem__(self, index, rows):
            try:
                data_model = self.ctrls[index].getModel().GridDataModel
                data_model.removeAll()
                if not isinstance(rows, (list, tuple)):
                    rows = ((rows,),)
                for row in rows:
                    data_model.addRow('', tuple(row))
            except Exception as e:
                print(e)
        
        def _get_count(self, data_model):
            return data_model.getRowCount()
        
        def _remove_all(self, data_model):
            data_model.removeAll()
        
        def _get_cell_data(self, data_model, column, row):
            return data_model.Data[row][column]
        
        def _get_row(self, data_model, n):
            return data_model.Data[n]
        
        def _add_rows(self, data_model, headings, rows):
            for heading, row in zip(headings, rows):
                data_model.addRow(heading, tuple(row))
        
        def _get_selected(self, grid):
            selections = grid.getSelection()
            if selections:
                return selections[0]
            return None
        
        def _search_in_first_column(self, data_model, row_index, regexp):
            data = data_model.Data
            for i in range(row_index)[::-1]:
                d = data[i]
                m = regexp.search(d[0])
                if m:
                    return m.group(1)
            return None
        
        def _search(self, data_model, start_row, search_text):
            exp = None
            try:
                exp = re.compile(search_text, re.I)
            except:
                pass
            result = None
            n = None
            for i, row in enumerate(data_model.Data[start_row +1:]):
                row_data = '|'.join(row)
                if exp:
                    result = exp.search(row_data, 0)
                    if result:
                        n = i + start_row + 1
                        break
                else:
                    result = row_data.find(search_text)
                    if result >= 0:
                        n = i + start_row + 1
                        break
            return n
    else:
        def __setitem__(self, index, rows):
            try:
                data_model = self.ctrls[index].getModel().GridDataModel
                data_model.removeAllRows()
                if not isinstance(rows, (list, tuple)):
                    rows = ((rows,),)
                trows = tuple([tuple(row) for row in rows])
                headings = tuple(["" for i in range(len(rows))])
                data_model.addRows(headings, trows)
            except:
                pass
            if mytools_Mri.config.Config.GRID_UPDATE:
                self.ctrls[index].getContext().getPeer().invalidate(8)
                self._re_set_size(index)
        
        def _get_count(self, data_model):
            return data_model.RowCount
        
        def _remove_all(self, data_model):
            data_model.removeAllRows()
        
        def _get_cell_data(self, data_model, column, row):
            return data_model.getCellData(column, row)
        
        def _add_rows(self, data_model, headings, rows):
            data_model.addRows(headings, trows)
        
        def _search_in_first_column(self, data_model, row_index, regexp):
            if row_index:
                for i in range(row_index)[::-1]:
                    m = regexp.search(data_model.getCellData(0, i))
                    if m:
                        return m.group(1)
            elif row_index == 0:
                m = regexp.search(data_model.getCellData(0, 0))
                if m:
                    return m.group(1)
            return None
        
        if mytools_Mri.config.Config.GRID == 2:
            def _get_row(self, data_model, n):
                return data_model.getRowData(n)
            
            def _get_selected(self, grid):
                if grid.hasSelectedRows():
                    return grid.getSelectedRows()[0]
                return None
            
            def _search(self, data_model, start_row, search_text):
                exp = None
                try:
                    exp = re.compile(search_text, re.I)
                except:
                    pass
                result = None
                n = None
                for i in range(start_row +1, data_model.RowCount):
                    row_data = "|".join(data_model.getRowData(i))
                    if exp:
                        result = exp.search(row_data, 0)
                        if result:
                            n = i
                            break
                    else:
                        result = row_data.find(search_text)
                        if result >= 0:
                            n = i
                            break
                return n
        else:
            def _get_row(self, data_model, n):
                return [data_model.getCellData(i, n) 
                        for i in range(data_model.ColumnCount)]
            
            def _get_selected(self, grid):
                selections = grid.getSelection()
                if selections:
                    return selections[0]
                return None
            
            def _search(self, data_model, start_row, search_text):
                exp = None
                try:
                    exp = re.compile(search_text, re.I)
                except:
                    pass
                column_count = data_model.ColumnCount
                result = None
                n = None
                for i in range(start_row +1, data_model.RowCount):
                    row_data = "|".join([data_model.getCellData(j, i) 
                        for j in range(column_count)])
                    if exp:
                        result = exp.search(row_data, 0)
                        if result:
                            n = i
                            break
                    else:
                        result = row_data.find(search_text)
                        if result >= 0:
                            n = i
                            break
                return n


class GridUi(Ui, GridPages, PageStatus):
    """UI with grid controls."""
    def __init__(self, active, ctrls, changer, 
        code, status, scrolls, tab, *args):
        Ui.__init__(self, code, status)
        GridPages.__init__(self, active, ctrls, changer, scrolls, tab)
        PageStatus.__init__(self, ctrls)
    
    def reset(self):
        for ctrl in self.ctrls:
            data_model = ctrl.getModel().GridDataModel
            if self._get_count(data_model) > 0:
                self._remove_all(data_model)
        self.update_status = [False for i in range(len(self.ctrls))]

