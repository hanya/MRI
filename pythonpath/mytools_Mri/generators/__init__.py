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

__all__ = ["Basic", "Cpp", "CSharp", "Java", "Python"]


from mytools_Mri.unovalues import TypeClass, ParamMode

class GeneratorBase(object):
    
    NAME = None
    PSEUD_PROPERTY = False
    VAR_NAME = "oInitialTarget"
    OBJ_PREFIX = ""
    
    def __init__(self):
        self.counter = 0
    
    def change_state(self, name, value):
        """Change state.
        used to change pseud_property state.
        """
        setattr(self, name, value)
        pass
    
    def add(self, element):
        pass
    
    def get(self):
        pass
    
    def next_object(self):
        self.counter += 1
        return self.OBJ_PREFIX % self.counter
    
    def get_last_part(self, name):
        """ Returns last string after last dot. """
        dot = name.rfind(".")
        if dot > 0:
            return name[dot+1:]
        else:
            return name
    
    def get_out_param_index(self, idl):
        """ Returns list of out/inout param indexes. """
        params = idl.getParameterInfos()
        if params:
            return [i for i, info in enumerate(params) if info.aMode == ParamMode.OUT or info.aMode == ParamMode.INOUT]
        else:
            return None
    
    def parse_seq(self, idl):
        """ Get type name and dimension of sequence. """
        n = 1
        comp_type = idl.getComponentType()
        while True:
            if comp_type.getTypeClass() != TypeClass.SEQUENCE:
                comp_type = idl.getComponentType()
                break
            n += 1
        return comp_type, n

