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
import operator

import mytools_Mri
import mytools_Mri.values
from mytools_Mri.unovalues import TypeClass, TypeClassGroups, ParamMode

try:
    long
except:
    long = int

class Info(object):
    def __init__(self, engine, config):
        self.engine = engine
        self.config = config
    
    # informations
    
    def get_properties_info(self, entry, config):
        try:
            txt = self.engine.get_properties_info(entry, config.property_only)
            if config.abbrev:
                abbr_old = mytools_Mri.values.ABBROLD
                abbr_new = mytools_Mri.values.ABBRNEW
                txt[:] = [(i[0], 
                    i[1].replace(abbr_old, abbr_new),
                    i[2], i[3], i[4], i[5]) for i in txt]
            if config.sorted:
                try:
                    txt.sort(key=operator.itemgetter(0))
                except:
                    _items = [(item[0], item) for item in txt]
                    _items.sort()
                    txt = [item for (key, item) in _items]
            
            if config.grid:
                #return ((t[0], t[1], t[2], t[3], t[4], t[5]) for t in txt)
                return [(t[0], t[1], t[2], t[3], t[4]) for t in txt]
            else:
                if config.show_labels:
                    txt.insert(0, ('(Name)', '(Value Type)', '(Value)',
                        '(Info.)', '(Attr.)', '(Handle)'))
                mnlen = max([len(x[0]) for x in txt])
                mtlen = max([len(x[1]) for x in txt])
                mvlen = max([len(x[2]) for x in txt])
                malen = max([len(x[4]) for x in txt])
                return ''.join([("%s  %s  %s  %s  %s  %s  \n" % 
                    (t[0].ljust(mnlen), t[1].ljust(mtlen),
                    t[2].ljust(mvlen), t[3].ljust(8),
                    t[4].ljust(malen), t[5].rjust(3))) for t in txt])
        except Exception as e:
            print(e)
        return "error"
    
    def get_methods_info(self, entry, config):
        try:
            txt = self.engine.get_methods_info(entry)
            if config.abbrev:
                abbr_old = mytools_Mri.values.ABBROLD
                abbr_new = mytools_Mri.values.ABBRNEW
                txt[:] = [(i[0], 
                    i[1].replace(abbr_old, abbr_new),
                    i[2].replace(abbr_old, abbr_new), 
                    i[3].replace(abbr_old, abbr_new),
                    i[4].replace(abbr_old, abbr_new)) for i in txt]
            if config.sorted:
                try:
                    txt.sort(key=operator.itemgetter(0))
                except:
                    _items = [(item[0], item) for item in txt]
                    _items.sort()
                    txt = [item for (key, item) in _items]
            
            if config.grid:
                return [(i[0], i[1], i[2], i[3], i[4]) for i in txt]
            else:
                if config.show_labels:
                        txt.insert(0, ('(Name)', '(Arguments)', '(Return Type)', 
                        '(DeclaringClass)', '(Exceptions)'))
                mnlen = max([len(x[0]) for x in txt])
                malen = max([len(x[1]) for x in txt])
                mrlen = max([len(x[2]) for x in txt])
                mdlen = max([len(x[3]) for x in txt])
                if malen > 50: malen = 50
                return ''.join([('%s  %s  %s  %s  %s  \n' % 
                    (i[0].ljust(mnlen), i[1].ljust(malen), i[2].ljust(mrlen),
                    i[3].ljust(mdlen), i[4])) for i in txt])
        except Exception as e:
            print(e)
        return "error."
    
    def get_interfaces_listeners_info(self, entry, config):
        slist = []
        iinfos = self.get_interfaces_info(entry, config)
        linfos = self.get_listeners_info(entry, config)
        for li in linfos:
            try: iinfos.remove(li)
            except: pass
        
        iinfos = list(set(iinfos))
        linfos = list(set(linfos))
        if config.sorted:
            iinfos.sort()
            linfos.sort()
        
        if config.grid:
            return [(i,) for i in iinfos] + [('',), ('Listeners',)] + [(i,) for i in linfos]
        else:
            return "\n".join(slist + [
                "(Interfaces)", "\n".join(iinfos), '', 
                "(Listeners)", "\n".join(linfos)])
    
    def get_interfaces_info(self, entry, config):
        try:
            #return self.engine.get_interfaces_info(self.current_entry)
            return self.engine.all_interfaces_info(entry)
        except Exception as e:
            print(e)
    
    def get_listeners_info(self, entry, config):
        return self.engine.get_listeners_info(entry)
    
    def get_services_info(self, entry, config):
        services = []
        v_services = []
        try:
            services = self.engine.get_services_info(entry)
            if config.sorted:
                services.sort()
            if services and not config.grid: services.insert(0, '(Supported Service Names)')
        except:
            if config.grid:
                return (("com.sun.star.lang.XServiceInfo interface is not supported.\n",),)
            else:
                return "com.sun.star.lang.XServiceInfo interface is not supported.\n"
        try:
            v_services = self.engine.get_available_services_info(entry)
            if config.sorted:
                v_services.sort()
            if v_services and not config.grid: v_services.insert(0, '(Available Service Names)')
        except:
            pass
        
        if config.grid:
            if v_services:
                return [(i,) for i in services] + [('',), ('Available Service Names',)] + [(i,) for i in v_services]
            else:
                return [(i,) for i in services]
        else:
            if v_services:
                v = "\n" *2 + "\n".join(v_services)
            else:
                v = ""
            #return "\n".join(services) + (("\n" *2 + "\n".join(v_services)) if v_services else "")
            return "\n".join(services) + v
    
    def get_struct_name(self, entry, config):
        name = entry.type.getName().strip("[]")
        if config.grid:
            struct_name = ((name, ),)
        else:
            struct_name = '(Struct Name)\n%s' % name
        return struct_name
    
    def get_struct_info(self, entry, config):
        try:
            txt = self.engine.get_struct_info(entry)
            if config.abbrev:
                abbr_old = mytools_Mri.values.ABBROLD
                abbr_new = mytools_Mri.values.ABBRNEW
                txt[:] = [(i[0], 
                    i[1].replace(abbr_old, abbr_new),
                    i[2], i[3]) for i in txt]
            if config.sorted:
                try:
                    txt.sort(key=operator.itemgetter(0))
                except:
                    _items = [(item[0], item) for item in txt]
                    _items.sort()
                    txt = [item for (key, item) in _items]
            
            if config.grid:
                return [(t[0], t[1], t[2], '', t[3]) for t in txt]
            else:
                if config.show_labels:
                    txt.insert(0, ('(Name)', '(Value Type)', '(Value)', '(AccessMode)'))
                mnlen = max([len(x[0]) for x in txt])
                mtlen = max([len(x[1]) for x in txt])
                mvlen = max([len(x[2]) for x in txt])
                if mnlen < 12: mnlen = 12
                if mtlen < 16: mtlen = 16
                return ''.join(['%s  %s  %s %s\n' % (
                    t[0].ljust(mnlen), t[1].ljust(mtlen), t[2].ljust(mvlen), t[3]) for t in txt])
        except Exception as e:
            print(("get_struct_info: " + str(e)))
        return "error"
    
    def get_struct_sequence_info(self, entry, config):
        """create information about sequence of structs."""
        from mytools_Mri import Entry
        try:
            if entry.target is None:
                return 'void'
            if isinstance(entry.target, tuple) and len(entry.target) == 0:
                if config.grid:
                    return (("empty", "", "", "", ""),)
                else:
                    return "empty"
            n = entry.type.getName().count('[]')
            l = list(range(len(entry.target)))
            b = entry.target[:]
            if n > 1:
                for i in range(n -1):
                    l, b = get_elements(l, b)
            elements = []
            
            if len(entry.target) > 0:
                elements = [('(%s)' % m, self.engine.get_struct_info(self.engine.create(self, "", t))) 
                                    for t, m in zip(b, l)]
                
            if config.abbrev:
                abbr_old = mytools_Mri.values.ABBROLD
                abbr_new = mytools_Mri.values.ABBRNEW
                elements[:] = [
                    (i[0], [(j[0], j[1].replace(abbr_old, abbr_new), 
                        j[2], j[3]) for j in i[1]]) for i in elements]
            
            if config.grid:
                data = []
                adata = data.append
                for t in elements:
                    adata((t[0], '', '', '', ''))
                    #adata((i[0], i[1], i[2], '', i[3]) for i in t[1])
                    for i in t[1]:
                        adata((i[0], i[1], i[2], '', i[3]))
                return data
            else:
                length = [(max([len(x[0]) for x in element[1]]), 
                           max([len(x[1]) for x in element[1]]), 
                           max([len(x[2]) for x in element[1]]))
                                for element in elements]
                mnlen = max([x[0] for x in length])
                mtlen = max([x[1] for x in length])
                mvlen = max([x[2] for x in length])
                if mnlen < 12: mnlen = 12
                if mtlen < 16: mtlen = 16
            
                if config.show_labels:
                    elements.insert(0, ('', [('(Name)', '(Value Type)', '(Value)', '(AccessMode)')]))
                return "\n".join(["%s\n%s" % (t[0], 
                        "\n".join(["%s  %s  %s  %s" % (
                            i[0].ljust(mnlen), i[1].ljust(mtlen), 
                            i[2].ljust(mvlen), i[3]) for i in t[1]]
                        )) for t in elements]).lstrip()
        except Exception as e:
            print(("get_struct_sequence_info: " + str(e)))
        return ''
    
    
    def get_sequence_info(self, entry, config):
        if config.grid:
            return tuple(self.multi_array_string(entry, grid=True))
        else:
            return "\n".join(self.multi_array_string(entry))
    
    def multi_array_string(self, entry, ctype="", grid=False):
        value = entry.target
        type_name = entry.type.getName()
        n = type_name.count('[]')
        if ctype == '':
            ctype = type_name.strip('[]')
        if grid:
            if n == 1:
                format = "(%03d)"
            else:
                format = "(%s)"
        else:
            if n == 1:
                format = "(%03d) = %s"
            else:
                format = "(%s) = %s"
        
        l = range(len(value))
        b = value[:]
        if n > 1:
            for i in range(n -1):
                l,b = get_elements(l,b)
        txt = []
        if ctype == 'string':
            if grid:
                txt = [(format % m, t, "", "", "") for t,m in zip(b,l)]
            else:
                txt = [format % (m,t) for t,m in zip(b,l)]
        elif ctype in ['num', 'long', 'double', 'float', 'hyper', 'short']:
            if grid:
                txt = [(format % m, t, "", "", "") for t,m in zip(b,l)]
            else:
                txt = [format % (m,t) for t,m in zip(b,l)]
        elif ctype == 'enum':
            if grid:
                txt = [(format % m, t.value, "", "", "") for t,m in zip(b,l)]
            else:
                txt = [format % (m,t.value) for t,m in zip(b,l)]
        elif ctype == 'byte':
            try:
                if grid:
                    txt = [(format % m, hex(t), "", "", "") for t,m in zip(b,l)]
                else:
                    txt = [format % (m, hex(t)) for t,m in zip(b,l)]
            except:
                if grid:
                    txt = [(format % m, hex(ord(t)), "", "", "") for t,m in zip(b,l)]
                else:
                    txt = [format % (m,hex(ord(t))) for t,m in zip(b,l)]
        elif ctype == 'type':
            if grid:
                txt = [(format % m, t.typeName, "", "", "") for t, m in zip(b,l)]
            else:
                txt = [format % (m,t.typeName) for t,m in zip(b,l)]
        else:
            if grid:
                txt = [(format % m, t, "", "", "") for t, m in zip(b,l)]
            else:
                txt = [format % (m,t) for t,m in zip(b,l)]
        #return '\n'.join(txt)
        
        if len(txt) == 0:
            if grid:
                txt = (("empty", "", "", "", ""),)
            else:
                txt = ("empty",)
        return txt


def get_elements(labels, values):
    a = []
    l = []
    for j in range(len(values)):
        p = labels[j]
        d = values[j]
        for i in range(len(d)):
            a.append(d[i])
            l.append("%03d,%03d" % (p,i))
    return (l, a)

from mytools_Mri import CancelException


class ExtendedInfo(Info):
    """ Supports to get or set property value. """
    
    def make_single_value(self, name, type_name, type_class, doc=None, add_doc=None):
        """  """
        elements = ((name, type_class.value),)
        try:
            text = "%s %s" % (type_name, name)
            if add_doc: text += "\n" + add_doc
            # ToDo add information about enum if type_class is ENUM
            state, results = self.dlgs.dialog_elemental_input(
                elements, 'input value', text, doc)
        except Exception as e:
            print(e)
        if not state: raise CancelException("canceled.")
        result = results[0]
        value = result.value
        if type_class == TypeClass.ANY:
            type_class = TypeClassGroups.get_type_class(result.value_type)
            type_name = result.value_type
            if value_type == "ENUM":
                type_name, value = self.engine.split_enum_name(result.value)
        return self.engine.get_value(value, type_name, type_class)
        
    
    def get_arguments(self, method):
        """used for callback to get argument."""
        if not method: raise Exception('illeagal method.')
        p_infos = method.getParameterInfos()
        n_infos = len(p_infos)
        
        method_name = method.getName()
        if n_infos == 0:
            return ()
        elif n_infos == 1:
            if method_name in ('getByIndex', 'getByName', 'getAccessibleChild', 'getByIdentifier'):
                state = False
                try:
                    state, arg, ttype, key = self.get_arguments_for_special_methods(method)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                if state:
                    return (arg, )
        
        # check all arguments
        for param in p_infos:
            if not param.aMode == ParamMode.IN:
                raise Exception('unable to get arguments from input.')
        state = 0
        try:
            method_args = []
            elements = []
            for param in p_infos:
                arg = '%s %s %s' % (
                    self.engine.get_mode_string(param.aMode), param.aType.Name, param.aName)
                elements.append((arg, param.aType.getTypeClass().value))
                method_args.append(arg)
            state, results = self.dlgs.dialog_elemental_input(
                elements, 'input arguments', "%s(\n\t%s\n )" % (method_name, ", \n\t".join(method_args)), 
                (method.getDeclaringClass().getName(), method_name))
        except Exception as e:
            print(e)
        
        if not state: raise CancelException("canceled.")
        args = []
        for param, result in zip(p_infos, results):
            type_class = param.aType.getTypeClass()
            if type_class in (TypeClass.INTERFACE, TypeClass.STRUCT, TypeClass.SEQUENCE):
                args.append(result.value)
            else:
                type_name = param.aType.getName()
                value_type = result.value_type
                value = result.value
                if type_class == TypeClass.ANY:
                    type_class = TypeClassGroups.get_type_class(value_type)
                    if value_type == "ENUM":
                        type_name, value = self.engine.split_enum_name(value)
                else:
                    type_class = param.aType.getTypeClass()
                args.append(
                    self.engine.get_value(value, type_name, type_class))
        return args
    
    def get_arguments_for_special_methods(self, method):
        """ """
        target = self.main.current.target
        method_name = method.Name
        if method_name == 'getByIndex':
            n = target.getCount()
            selected = self.dlgs.dialog_select(tuple(range(n)))
            if selected != None:
                ttype = target.getElementType()
                return (True, long(selected), ttype, "%s(%s)" % (method_name, selected))
        elif method_name == 'getByName':
            names = target.getElementNames()
            selected = self.dlgs.dialog_select(names)
            if selected != None:
                ttype = target.getElementType()
                return (True, selected, ttype, "%s(\"%s\")" % (method_name, selected))
        elif method_name == 'getAccessibleChild':
            n = target.getAccessibleChildCount()
            selected = self.dlgs.dialog_select(tuple(range(n)))
            if selected != None:
                return (True, long(selected), None, "%s(%s)" % (method_name, selected))
        elif method_name == 'getByIdentifier':
            ids = target.getIdentifiers()
            selected = self.dlgs.dialog_select(tuple([str(i) for i in ids]))
            if selected is not None:
                ttype = target.getElementType()
                return (True, long(selected), ttype, "%s(%s)" % (method_name, selected))
        return (False, None, None, None)

