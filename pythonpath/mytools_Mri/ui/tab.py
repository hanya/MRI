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

from com.sun.star.awt.PosSize import POSSIZE as PS_POSSIZE
from com.sun.star.beans import NamedValue

def _create_tab2(ctx, smgr, subcont, width, height, use_grid, grid_type, tab_type):
    """ With tab control. """
    subcont_model = subcont.getModel()
    if tab_type == 1:
        tab_model = subcont_model.createInstance(
            "com.sun.star.awt.tab.UnoControlTabPageContainerModel")
    else:
        tab_model = subcont_model.createInstance(
            "com.sun.star.awt.UnoMultiPageModel")
    subcont_model.insertByName("tab", tab_model)
    tab = subcont.getControl("tab")
    tab.setPosSize(0, 0, width, height, PS_POSSIZE)
    inner_ps = tab.getOutputSize()
    def _insert_page(title, page_id, name, help_url, pos):
        if tab_type == 1:
            _page_model = tab_model.createTabPage(page_id)
            _page_model.Title = title
            _page_index = tab_model.getCount()
            tab_model.insertByIndex(_page_index, _page_model)
        else:
            # LibreOffice kind
            _page_model = tab_model.createInstance("com.sun.star.awt.UnoPageModel")
            tab_model.insertByName("page_%s" % pos, _page_model)
            tab.setTabProps(pos + 1, (NamedValue("Title", title),))
            _page_index = pos
        _page = tab.getControls()[_page_index]
        if use_grid:
            from mytools_Mri.ui.grid import _create_grid2
            ctrl = _create_grid2(ctx, smgr, _page, name, help_url, pos, grid_type)
        else:
            from mytools_Mri.ui.frame import _create_edit2
            ctrl = _create_edit2(_page, name, help_url)
        ctrl.setPosSize(0, 0, width, inner_ps.Height, PS_POSSIZE)
        return ctrl
    help_url = "mytools.Mri:edit_info"
    info_0 = _insert_page("Properties", 1, "info_0", help_url, 0)
    info_1 = _insert_page("Methods", 2, "info_1", help_url, 1)
    info_2 = _insert_page("Interfaces", 3, "info_2", help_url, 2)
    info_3 = _insert_page("Services", 4, "info_3", help_url, 3)
    if tab_type == 1:
        tab.ActiveTabPageID = 1
    else:
        tab.activateTab(1)
    return tab, info_0, info_1, info_2, info_3

try:
    from com.sun.star.awt.tab import XTabPageContainerListener
    class TabPageListener(unohelper.Base, XTabPageContainerListener):
        def __init__(self, cast):
            self.cast = cast
        def disposing(self, ev):
            self.cast = None
        def tabPageActivated(self, ev):
            self.cast.category_changed(ev.TabPageID - 1)
except:
    pass
try:
    # LibreOffice
    from com.sun.star.awt import XTabListener
    class TabListener(unohelper.Base, XTabListener):
        def __init__(self, cast):
            self.cast = cast
        def disposing(self, ev):
            self.cast = None
        def inserted(self, id): pass
        def removed(self, id): pass
        def changed(self, id, args): pass
        def deactivaged(self, id): pass
        def activated(self, id):
            self.cast.category_changed(id -1)
except:
    pass

