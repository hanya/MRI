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
DEBUG = True
def log(message):
    if DEBUG:
        print((" LOG: " + message))

class CGMode(object):
    GET = 1
    SET = 2

class CGType(object):
    NONE = 0
    METHOD = 4
    PROP = 8
    PSEUD_PROP = 128
    ATTR = 16
    
    FIELD = 32 # struct field
    ELEMENT = 64 # sequence element
    
    SERVICE = 256
    STRUCT = 512
    ENUM = 1024
    TYPE = 2048
    CHAR = 4096
    SEQ = 8192
    CONTEXT = 123
    VARIABLE = 124

class CodeEntry(object):
    """ Individual code entry. """
    
    def __init__(self, type, key, value_type, parent=None, args=None, idl=None, mode=0, misc=None):
        self.type = type
        self.mode = mode
        self.key = key
        
        self.value_type = value_type
        self.parent = parent
        self.args = args
        self.idl = idl
        self.misc = misc
    
    def __repr__(self):
        return "<CodeEntry %s: %s>" % (self.type, self.key)


class CodeGenerator(object):
    """ Manages real code generators. """
    
    CLASS_PREFIX = "GeneratorFor"
    PSEUD_PROPERTY = "PSEUD_PROPERTY"
    
    def __init__(self, code_type, pseud, enabled):
        self.code_type = code_type
        self.entries = []
        self.elements = []
        self.pseud = pseud
        self.enabled = enabled
        
        self.generator = None
        self.set_enable(enabled)
    
    def set_enable(self, state):
        self.enabled = state
        if state:
            self.generator = self.get_generator(self.code_type, self.pseud)
            if self.generator:
                add = self.generator.add
                for entry in self.entries:
                    add(entry)
        else:
            self.generator = None
    
    def change_state(self, enabled=None, code_type=None, pseud=None):
        if not pseud is None:
            self.pseud = pseud
        if not code_type is None:
            self.code_type = code_type
        if not enabled is None:
            self.enabled = enabled
        self.set_enable(self.enabled)
    
    def set_pseud_property(self, state):
        self.pseud = state
        if self.generator:
            klass = self.generator.__class__
            if hasattr(klass, self.PSEUD_PROPERTY) and \
                getattr(klass, self.PSEUD_PROPERTY):
                self.generator.set_pseud_property(state)
    
    def get_generator(self, code_type, pseud):
        g = None
        if not code_type: return
        name = "mytools_Mri.generators.%s" % code_type
        mod = __import__(name)
        mod = getattr(mod.generators, code_type)
        klass = getattr(mod, self.CLASS_PREFIX + code_type)
        g = klass()
        if g and hasattr(klass, self.PSEUD_PROPERTY):
            g.change_state("pseud", pseud)
        return g
    
    def get_generator_list(self, *args):
        generators = []
        import mytools_Mri.generators
        names = mytools_Mri.generators.__all__
        for name in names:
            try:
                mod = __import__(name = "mytools_Mri.generators.%s" % name)
                mod = getattr(mod.generators, name)
                generators.append((name, getattr(mod, self.CLASS_PREFIX + name).NAME))
            except Exception as e:
                print(e)
        return generators
    
    def get(self):
        """ Get code result from current generator. """
        return self.generator.get()
    
    def add(self, type, key, value_type=None, args=None, parent=None, idl=None, mode=0, misc=None):
        entry = CodeEntry(type, key, value_type, parent, args, idl, mode, misc)
        self.entries.append(entry)
        if self.enabled and self.generator:
            try:
                self.generator.add(entry)
            except Exception as e:
                print(e)
                traceback.print_exc()
        return entry

