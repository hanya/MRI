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
import unohelper

from com.sun.star.lang import XComponent
class Component(XComponent):
    """ For life-time management. """
    def __init__(self):
        self.event_listeners = []
    
    def dispose(self):
        for listener in self.event_listeners:
            try:
                listener.disposing(self)
            except:
                pass
    
    def addEventListener(self, listener):
        try:
            self.event_listeners.index(listener)
        except:
            self.event_listeners.append(listener)
    
    def removeEventListener(self, listener):
        try:
            self.event_listeners.remove(listener)
        except:
            pass

from com.sun.star.awt.tree import TreeDataModelEvent, \
    XTreeDataModel, XTreeNode
from com.sun.star.lang import IndexOutOfBoundsException, \
    IllegalArgumentException


class ChangeType(object):
    NodeChanged = 0x0
    NodeInserted = 0x1
    NodeRemoved = 0x2
    StructureChanged = 0x4


class CustomTreeNode(unohelper.Base, XTreeNode):
    
    NODE_GRAPHIC = ""
    NODE_GRAPHIC2 = ""
    
    def __init__(self, data_model, display_value, on_demand):
        self.display_value = display_value
        self.on_demand = on_demand
        self.data_model = data_model
        self.parent = None
        self.children = []
        
        self.data = None
    
    def clear(self):
        self.display_value = None
        self.data_model = None
        self.parent = None
        self.data = None
        self.children = None
    
    def __str__(self):
        return "<TreeNode: %s>" % self.display_value
    
    def get_data(self):
        return self.data
    
    def set_data(self, data):
        self.data = data
    
    def get_child_from_data(self, data):
        for child in self.children:
            if child.get_data() == data:
                return child
        return None
    
    # XTreeNode
    def getChildAt(self, index):
        if index < len(self.children):
            return self.children[index]
        raise IndexOutOfBoundsException()
    
    def getChildCount(self):
        return len(self.children)
    
    def getParent(self):
        return self.parent
    
    def getIndex(self, node):
        try:
            return self.children.index(node)
        except:
            return -1
    
    def hasChildrenOnDemand(self):
        return self.on_demand
    
    def getDisplayValue(self):
        return self.display_value
    
    def setDisplayValue(self, display_value):
        self.display_value = display_value
    
    def getNodeGraphicURL(self):
        return ""#self.NODE_GRAPHIC
    
    def getExpandedGraphicURL(self):
        return self.NODE_GRAPHIC
    
    def getCollapsedGraphicURL(self):
        return self.NODE_GRAPHIC
    
    def set_parent(self, node):
        self.parent = node
    
    def appendChild(self, node):
        if not node.getParent():
            node.set_parent(node)
            self.children.append(node)
            try:
                self.data_model.changed(ChangeType.NodeInserted, self, (node,))
            except Exception as e:
                print(e)
        else:
            e = IllegalArgumentException()
            e.ArgumentPosition = 0
            raise e
    
    def removeChildByIndex(self, n):
        node = self.children.pop(n)
        self.data_model.changed(ChangeType.NodeRemoved, self, (node,))


class TreeRootNode(CustomTreeNode):
    """ Root. """
    NODE_GRAPHIC = ""


class CustomTreeDataModel(unohelper.Base, Component, XTreeDataModel):
    
    def __init__(self):
        Component.__init__(self)
        self.tree_listeners = []
        self.root = None
    
    def changed(self, change_type, parent, nodes):
        ev = TreeDataModelEvent(self, nodes, parent)
        for listener in self.tree_listeners:
            if change_type == ChangeType.NodeChanged:
                listener.treeNodesChanged(ev)
            elif change_type == ChangeType.NodeInserted:
                listener.treeNodesInserted(ev)
            elif change_type == ChangeType.NodeRemoved:
                listener.treeNodesRemoved(ev)
            elif change_type == ChangeType.StructureChanged:
                listener.treeStructureChanged(ev)
    
    def create_node(self, name, on_demand):
        return CustomTreeNode(self, name, on_demand)
    
    def create_root(self, name, on_demand):
        return TreeRootNode(self, name, on_demand)
    
    # XTreeDataModel
    def getRoot(self):
        return self.root
    
    def addTreeDataModelListener(self, listener):
        if not listener in self.tree_listeners:
            self.tree_listeners.insert(0, listener)
    
    def removeTreeDataModelListener(self, listener):
        if listener in self.tree_listeners:
            del self.tree_listeners[listener]
    
    def set_root(self, node):
        if self.root != node:
            self.root = node
            self.changed(ChangeType.StructureChanged, node, (node,))

from com.sun.star.awt.PosSize import POSSIZE as PS_POSSIZE, SIZE as PS_SIZE

from com.sun.star.view import XSelectionChangeListener
class TreeSelectionListener(unohelper.Base, XSelectionChangeListener):
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev): pass
    def selectionChanged(self, ev):
        try:
            if self.cast.tree and self.cast.tree.ignore:
                self.cast.tree.ignore = False
                return
        except:
            pass
        try:
            tree = ev.Source
            if tree.getSelectionCount() > 0 and self.cast.tree:
                selected = tree.getSelection()
                if isinstance(selected, tuple):
                    tree_node = selected[0]
                else:
                    tree_node = selected
                if tree_node is None:
                    return
                node = self.cast.tree.find_node(tree_node)
                if node and not node == self.cast.main.current:
                    n = self.cast.main.history.get_history_index(node)
                    self.cast.history_change(n, update_tree=False)
        except Exception as e:
            print(("selectionChanged: " + str(e)))
            traceback.print_exc()

from com.sun.star.awt import XWindowListener
class TreeWindowListener(unohelper.Base, XWindowListener):
    def __init__(self,cast):
        self.cast = cast
    def disposing(self,ev):
        self.cast = None
    def windowMoved(self,ev): pass
    def windowShown(self,ev): pass
    def windowHidden(self,ev): pass
    def windowResized(self,ev):
        ps = ev.Source.getPosSize()
        self.cast.tree.tree.setPosSize(0, 0, ps.Width, ps.Height, PS_SIZE)

from com.sun.star.lang import XEventListener
class TreeComponentWindowListener(unohelper.Base, XEventListener):
    def __init__(self,cast):
        self.cast = cast
    def disposing(self, ev):
        tree = self.cast.tree
        tree.close()
        self.cast.tree = None
        self.cast = None
        del self.cast.listeners['tree']
        del self.cast.listeners['tree_cont']
        del self.cast.listeners['tree_win']
        del self.cast.listeners["tree_mouse"]

from com.sun.star.awt.MouseButton import RIGHT as MB_RIGHT
from com.sun.star.awt import Point, Rectangle

from com.sun.star.awt import XMouseListener
class TreeMouseListener(unohelper.Base, XMouseListener):
    def __init__(self, cast):
        self.cast = cast
        self.popup = None
        
        import mytools_Mri.tools
        self.use_point = mytools_Mri.tools.check_method_parameter(self.cast.ctx, 
            "com.sun.star.awt.XPopupMenu", "execute", 1, "com.sun.star.awt.Point")
        
    def disposing(self, ev):
        self.cast = cast
    def mouseEntered(self, ev): pass
    def mouseExited(self, ev): pass
    def mousePressed(self, ev): pass
    def mouseReleased(self, ev):
        if ev.Buttons == MB_RIGHT and ev.ClickCount == 1:
            if not self.popup:
                self.popup = self._create_popup()
                if not self.popup: return
            pos = ev.Source.getPosSize()
            if self.use_point:
                _pos = Point(pos.X + ev.X, pos.Y + ev.Y)
            else:
                _pos = Rectangle(pos.X + ev.X, pos.Y + ev.Y, 0, 0)
            n = self.popup.execute(ev.Source.getPeer(), _pos, 0)
            if n > 0:
                self.do_command(ev, n)
    
    def do_command(self, ev, n):
        tree = ev.Source
        data_model = tree.getModel().DataModel
        root = data_model.getRoot()
        if n == 1:
            def expand(node):
                children = node.children
                if children:
                    tree.makeNodeVisible(children[0])
                for child in children:
                    expand(child)
            expand(root)
        elif n == 2:
            def collapse(node):
                children = node.children
                if children:
                    tree.collapseNode(node)
                for child in children:
                    collapse(child)
            collapse(root)
    
    def _create_popup(self):
        items = ((1, 0, 0, 'Expand All', ':ExpandAll', None), 
            (2, 1, 0, "Collapse All", ":CollapseAll", None))
        
        import mytools_Mri.ui.tools
        popup = mytools_Mri.ui.tools.create_popupmenu(self.cast.ctx, items)
        try:
            popup.hideDisabledEntries(True)
        except:
            pass
        return popup


from com.sun.star.awt.WindowAttribute import \
    BORDER as WA_BORDER, SHOW as WA_SHOW, \
    SIZEABLE as WA_SIZEABLE, MOVEABLE as WA_MOVEABLE, CLOSEABLE as WA_CLOSEABLE
from com.sun.star.view.SelectionType import SINGLE as ST_SINGLE
from com.sun.star.awt.WindowClass import SIMPLE as WC_SIMPLE
from com.sun.star.beans import NamedValue

def create_tree_window(self, ctx, parent, ev=None):
    from mytools_Mri.ui.frame import create_window
    smgr = ctx.getServiceManager()
    def create(name):
        return smgr.createInstanceWithContext(name, ctx)
    
    WIDTH = 300
    WINDOW_HEIGHT = 350
    x = 100
    y = 100
    if ev:
        ps = ev.Source.getPosSize()
        x = ps.X + 250
        y = ps.Y
    
    toolkit = parent.getToolkit()
    
    frame = create('com.sun.star.frame.Frame')
    window = create_window(toolkit, parent, WC_SIMPLE, "floatingwindow", 
        WA_BORDER | WA_SHOW | WA_SIZEABLE | WA_MOVEABLE | WA_CLOSEABLE, 
        x, y, WIDTH, WINDOW_HEIGHT)
    frame.initialize(window)
    frame.setTitle("History")
    
    cont = create('com.sun.star.awt.UnoControlContainer')
    cont_model = create('com.sun.star.awt.UnoControlContainerModel')
    cont.setModel(cont_model)
    cont.createPeer(toolkit,window)
    cont.setPosSize(0,0,WIDTH,WINDOW_HEIGHT,PS_POSSIZE)
    #cont_model.BackgroundColor = 0xFAFAFA
    frame.setComponent(cont, None)
    try:
        tree = create('com.sun.star.awt.tree.TreeControl')
        tree_model = create('com.sun.star.awt.tree.TreeControlModel')
        tree_model.setPropertyValues(
            ('SelectionType', 'RootDisplayed'), 
            (ST_SINGLE, True))
        #data_model = smgr.createInstanceWithContext(
        #   'com.sun.star.awt.tree.MutableTreeDataModel', ctx)
        tree_model.DataModel = CustomTreeDataModel()
        tree.setModel(tree_model)
        tree.setPosSize(0, 0, WIDTH, WINDOW_HEIGHT, PS_POSSIZE)
        cont.addControl('tree', tree)
        tree_listener = TreeSelectionListener(self)
        tree.addSelectionChangeListener(tree_listener)
        self.listeners['tree'] = tree_listener
        cont_listener = TreeComponentWindowListener(self)
        cont.addEventListener(cont_listener)
        self.listeners['tree_cont'] = cont_listener
        win_listener = TreeWindowListener(self)
        window.addWindowListener(win_listener)
        self.listeners['tree_win'] = win_listener
        listener = TreeMouseListener(self)
        self.listeners["tree_mouse"] = listener
        tree.addMouseListener(listener)
    except Exception as e:
        print(e)
    return frame


class HistoryTreeUi(object):
    """ Manages history tree. """
    def __init__(self, ui, tree_frame):
        self.ignore = True # ignore selection change
        self._ui = ui
        self._tree_frame = tree_frame
        
        history = ui.main.history
        children = history.get_children() # first child is the top one
        
        cont = tree_frame.getComponentWindow()
        tree = cont.getControl("tree")
        tree_model = tree.getModel()
        data_model = tree_model.DataModel
        
        root = data_model.create_root(children[0].name, True)
        root.set_data(children[0])
        dummy_node = data_model.create_node('dummy', False)
        
        data_model.set_root(root)
        root.appendChild(dummy_node) # to show root node
        root.removeChildByIndex(0)
        children[0]._tree_node = root
        
        self._data_model = data_model
        # set node items
        self._add_nodes(children[0])
        # show current one
        current_node = self._ui.main.current._tree_node
        tree.makeNodeVisible(current_node)
        tree.select(current_node)
        self._tree = tree
        self.ignore = False
        self.tree = self._tree
    
    def close(self):
        # clean-up all nodes
        root = self._data_model.getRoot()
        def _clean(node):
            for c in node.children:
                if c.children:
                    _clean(c)
                c.clear()
        _clean(root)
        self._tree_frame = None
        self._ui = None
        self._data_model = None
        self._tree = None
        self.tree = None
    
    def _add_nodes(self, parent):
        for c in parent.get_children():
            node = self._data_model.create_node(c.name, True)
            node.set_data(c)
            parent._tree_node.appendChild(node)
            c._tree_node = node
            if c.get_child_count() > 0:
                self._add_nodes(c)
    
    def find_node(self, tree_node):
        return tree_node.get_data()
    
    def show_entry(self, entry):
        self._tree.makeNodeVisible(entry._tree_node)
    
    def set_selected(self, entry):
        self.ignore = True
        self._tree.select(entry._tree_node)
        #self.ignore = False
    
    def add_entry(self, parent, entry, select=False):
        node = self._data_model.create_node(entry.name, True)
        node.set_data(entry)
        parent._tree_node.appendChild(node)
        entry._tree_node = node
        if select:
            self.set_selected(entry)
            self.show_entry(entry)
    
    def update_labels(self):
        data_model = self._data_model
        def walk(node):
            entry = node.get_data()
            if entry:
                node.setDisplayValue(entry.name)
            if node.getChildCount():
                for i in range(node.getChildCount()):
                    walk(node.getChildAt(i))
                data_model.changed(ChangeType.NodeChanged, node, tuple(node.children))
        root = self._data_model.getRoot()
        walk(root)
