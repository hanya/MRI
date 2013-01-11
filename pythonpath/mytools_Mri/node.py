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

class ParentExistsException(Exception):
    """causes if entry already has its parent."""


class Node(object):
    """ Simple node implementation which is used to construct history tree. """
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None
    
    def append_child(self, child):
        """append new child."""
        if child.parent:
            raise ParentExistsException("child has parent.")
        self.children.append(child)
        child.set_parent(self)
    
    def get_parent(self):
        """returns parent entry."""
        return self.parent
    
    def set_parent(self, parent):
        """set parent entry."""
        self.parent = parent
    
    def get_child_count(self):
        return len(self.children)
    
    def get_children(self):
        """returns list of children."""
        return self.children
    
    def get_child_index(self, child):
        return self.children.index(child)
    
    def get_child_at(self, index):
        return self.children[index]
    
    def __repr__(self):
        return self.name


class Root(Node):
    """History root."""
    def __init__(self, name='root'):
        Node.__init__(self, name)
    
    def counter(self, node, obj):
        """try to find the obj in the entry."""
        n = 0
        for child in node.get_children():
            n += 1
            if child == obj:
                return True, n
            found, m = self.counter(child, obj)
            n += m
            if found:
                return True, n
        return False, n
    
    def get_history_index(self, obj):
        """history has tree structure and count them."""
        n = -1
        found = None
        for child in self.get_children():
            n += 1
            if child == obj:
                found = child
            else:
                try:
                    found, m = self.counter(child, obj)
                except Exception as e:
                    print(e)
                n += m
            if found: break
        if found:
            return n
        else:
            return -1
    
    def index_counter(self, entry, index, n):
        for child in entry.get_children():
            n += 1
            if n == index: return child, n
            found, m = self.index_counter(child, index, n)
            n = m
            if found: return found, n
        return None, n
    
    def get_history_entry(self, index):
        """get specific entry by index."""
        n = -1
        for child in self.get_children():
            n += 1
            if n == index: return child
            found, m = self.index_counter(child, index, n)
            n = m
            if found: return found
        return None
    
    def get_next_history_index(self, entry):
        if not entry.get_child_count():
            return self.get_history_index(entry) + 1
        else:
            n = self.get_history_index(entry)
            dummy, m = self.counter(entry, None)
            return n + m +1

