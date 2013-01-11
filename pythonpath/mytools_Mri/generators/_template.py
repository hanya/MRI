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

from mytools_Mri.generators import GeneratorBase
from mytools_Mri.unovalues import TypeClass
from mytools_Mri.cg import CGMode, CGType, log
from mytools_Mri.engine import Entry

class GeneratorFor(GeneratorBase):
    
    NAME = ""
    PSEUD_PROPERTY = False
    
    INDENT = "\t" * 1
    
    def __init__(self, type_cast=False):
        GeneratorBase.__init__(self)
    
    def get(self):
        pass
    
    def add(self, entry):
        func = self.items.get(entry.type, None)
        if func:
            try:
                func(entry)
            except Exception as e:
                print(("Error on cg#add: " + str(e)))
                traceback.print_exc()
    
    def ad(self, line, breakable=True, _break=False):
        self.lines.append(line)
        if _break or (breakable and len(self.lines) % 4 == 3):
            self.lines.append("")
    
    def add_method(self, entry):
        pass
    
    def add_prop(self, entry):
        pass
    
    def add_attr(self, entry):
        pass
    
    def add_element(self, entry):
        pass
    
    def add_field(self, entry):
        pass
    
    def create_seq(self, entry):
        pass
    
    def create_struct(self, entry):
        pass
    
    def create_service(self, entry):
        pass
    
    def get_component_context(self, entry):
        pass


    