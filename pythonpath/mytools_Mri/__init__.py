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
import uno

from mytools_Mri import engine, node, values
from mytools_Mri.type import ExtType2, ExtAnyType2
from mytools_Mri.unovalues import MethodConcept, PropertyConcept, \
    PropertyAttribute, ParamMode, TypeClass, TypeClassGroups
from mytools_Mri.config import Config
from com.sun.star.beans import UnknownPropertyException, PropertyVetoException
from com.sun.star.lang import WrappedTargetException, IllegalArgumentException
from com.sun.star.reflection import InvocationTargetException

class CancelException(Exception):
    pass

Entry = engine.Entry
class RootEntry(node.Root):
    pass

import mytools_Mri.web
import mytools_Mri.macros
from mytools_Mri.cg import CGMode, CGType, CodeEntry, CodeGenerator

class MRI(object):
    def __init__(self, ctx, ui_class):
        self.ctx = ctx
        if values.MRI_DIR is None:
            values.set_mri_dir(ctx)
        self.config = Config(ctx)
        self.config.property_only = False
        self.web = mytools_Mri.web.create_IDL_opener(self, self.config, self.config.ref_by_doxygen)
        self.engine = engine.MRIEngine(ctx)
        self.history = RootEntry()
        self.current = self.history
        self.cg = CodeGenerator(self.config.code_type, False, True)
        self.mode = True
        self.open_new = False
        self.macros = mytools_Mri.macros.Macros(self)
        self.ui = ui_class(ctx, self)
    
    def inspect(self, name, target):
        try:
            self.history.code_entry = None
            entry = self.engine.create(self, name, target)
            entry.code_entry = self.code(
                type=CGType.NONE, key=name, 
                value_type=entry.type, args="", parent="ROOT", idl=None)
            self.action_by_type(entry)
        except Exception as e:
            print(e)
            traceback.print_exc()
    
    def code(self, *args, **kwds):
        try:
            if not "parent" in kwds:
                kwds["parent"] = self.current.code_entry
            code_entry = self.cg.add(**kwds)
            if self.mode:
                self.ui.code_updated()
            return code_entry
        except Exception as e:
            print(e)
            traceback.print_exc()
        return None
    
    def set_mode(self, state):
        """ Set mode which broadcast to ui or not. """
        self.mode = not not state
    
    def message(self, message, title=''):
        """shows message."""
        if self.mode:
            self.ui.message(message, title)
    
    def error(self, message, title='Error'):
        """shows error."""
        if self.mode:
            self.ui.error(message, title)
    
    def status(self, message):
        """status message."""
        if self.mode:
            self.ui.status(message)
    
    def update_config(self, store=False):
        """change config."""
        config = self.config
        self.macros.set_user_dir(config.macros)
        self.web.set_browser(config.browser)
        self.web.set_sdk_path(config.sdk_path)
        if store:
            self.config.write()
    
    def change_entry(self, entry):
        if self.open_new:
            self.open_new = False
            self.create_service(
                'mytools.Mri', nocode=True).inspect(entry.target)
        else:
            self.current.append_child(entry)
            self.current = entry
            self.ui.entry_changed(history=True, update=self.mode)
        return entry
    
    def set_current(self, entry):
        self.current = entry
    
    def change_history(self, index=None, entry=None):
        if entry is None:
            entry = self.history.get_history_entry(index)
        #self.set_current(entry)
        if entry != self.history:
            self.current = entry
            self.ui.entry_changed(history=False)
            return True
    
    def get_property_value(self, name):
        entry = self.current
        target = entry.target
        inspected = entry.inspected
        # normal property
        if entry.has_interface("com.sun.star.beans.XPropertySet"):
            psinfo = target.getPropertySetInfo()
            if psinfo and psinfo.hasPropertyByName(name):
                try:
                    value = target.getPropertyValue(name)
                    
                    temp_type = psinfo.getPropertyByName(name).Type
                    if temp_type is None:
                        temp_type = uno.Type("any", TypeClass.ANY)
                    entry = self.engine.create(self, name, value)
                    idl = entry.type
                    ext_type = ExtType2(entry, self.engine, 
                        temp_type.typeName, temp_type.typeClass)
                    entry.type = ext_type
                    entry.code_entry = self.code(
                        type=CGType.PROP ,mode=CGMode.GET, key=name, value_type=entry.type, idl=idl)
                    return self.action_by_type(entry)
                except Exception as e:
                    self.error("Exception, to get property: %s, %s" % (name, str(e)))
                    traceback.print_exc()
                    if self.mode:
                        return
                    else:
                        raise
        # pseud property
        if inspected.hasMethod("get%s" % name, MethodConcept.ALL):
            return self.call_method("get%s" % name, pseud=True)
        elif inspected.hasMethod("is%s" % name, MethodConcept.ALL):
            return self.call_method("is%s" % name, pseud=True)
        elif inspected.hasMethod("set%s" % name, MethodConcept.ALL):
            return self.status("Write only pseud property: %s" % name)
        # interface attributes
        if inspected.hasProperty(name, PropertyConcept.ATTRIBUTES):
            psinfo = inspected.getProperty(name, PropertyConcept.ATTRIBUTES)
            try:
                value = getattr(target, name)
                entry = self.engine.create(self, name, value)
                #temp_type = entry.type
                #if temp_type.getTypeClass() == TypeClass.SEQUENCE:
                ext_type = ExtType2(entry, self.engine, 
                        psinfo.Type.typeName, psinfo.Type.typeClass)
                entry.type = ext_type
                attr_def = self.engine.find_attribute_interface(
                    self.current, name)
                if attr_def is False: attr_def = ""
                entry.code_entry = self.code(
                    type=CGType.ATTR, mode=CGMode.GET, key=name, value_type=entry.type, idl=attr_def)
                return self.action_by_type(entry)
            except Exception as e:
                self.error("Exception, to get attribute: %s, %s" % (name, str(e)))
                traceback.print_exc()
                if self.mode:
                    return
                else:
                    raise
        # XVclWindowPeer
        if entry.has_interface("com.sun.star.awt.XVclWindowPeer"):
            try:
                value = target.getProperty(name)
                
                temp_type = inspected.getProperty(name, PropertyConcept.ALL).Type
                if temp_type is None:
                    temp_type = uno.Type("any", TypeClass.ANY)
                entry = self.engine.create(self, name, value)
                # ToDo code
                return self.action_by_type(entry)
            except Exception as e:
                self.error("Exception, to get %s, %s" % (name, str(e)))
                traceback.print_exc()
                if self.mode:
                    return
                else:
                    raise
    
    def set_property_value(self, name, get_value=None, arg=None, get_args=None):
        entry = self.current
        target = entry.target
        # normal property
        if entry.has_interface("com.sun.star.beans.XPropertySet"):
            psinfo = target.getPropertySetInfo()
            if psinfo.hasPropertyByName(name):
                pinfo = psinfo.getPropertyByName(name)
                if pinfo.Attributes & PropertyAttribute.READONLY:
                    raise Exception("%s read-only property." % name)
                if self.mode:
                    try:
                        old_value = target.getPropertyValue(name)
                        arg = get_value(name, pinfo.Type.typeName, pinfo.Type.typeClass, 
                                ("", ""), "current: " + str(old_value))
                    except CancelException:
                        return
                    except Exception as e:
                        self.status(str(e))
                        return
                try:
                    if self.mode:
                        _arg, _any = self.extract_args(arg)
                        target.setPropertyValue(name, _arg)
                        entry = self.engine.create(self, name, _arg)
                    else:
                        # ToDo any
                        _arg, _any = self.extract_args(arg)
                        target.setPropertyValue(name, _arg)
                        entry = self.engine.create(self, name, _arg)
                    
                    p_type = pinfo.Type
                    ext_type = ExtType2(entry, self.engine, p_type.typeName, p_type.typeClass)
                    entry.type = ext_type
                    entry.code_entry = self.code(
                        type=CGType.PROP, mode=CGMode.SET, key=name, value_type=entry.type, args=arg, idl=entry.type)
                except WrappedTargetException as e:
                    te = e.TargetException
                    self.error("Exception: %s" % te.Message)
                except IllegalArgumentException as e:
                    self.error("Illegal value for %s property." % prop_name)
                except PropertyVetoException as e:
                    self.error("Veto to set the %s property value." % prop_name)
                except UnknownPropertyException as e:
                    self.error("Unknown property! %s" % e)
                except Exception as e:
                    self.error("Exception, to set %s property, %s" % (name, str(e)))
                    traceback.print_exc()
                if self.mode:
                    return True
                else:
                    return None
        elif entry.inspected.hasProperty(name, PropertyConcept.ATTRIBUTES):
            pinfo = entry.inspected.getProperty(name, PropertyConcept.ATTRIBUTES)
            if pinfo.Attributes & PropertyAttribute.READONLY:
                self.status("Attribute %s is readonly." % name)
                raise Exception("%s read-only property." % name)
            if self.mode:
                try:
                    old_value = getattr(target, name)
                    arg = get_value(name, pinfo.Type.typeName, pinfo.Type.typeClass, 
                            ("", ""), "current: " + str(old_value))
                except Exception as e:
                    return
            try:
                if self.mode:
                    setattr(target, name, arg)
                    entry = self.engine.create(self, name, arg)
                else:
                    _arg, _any = self.extract_args(arg)
                    setattr(target, name, _arg)
                    entry = self.engine.create(self, name, _arg)
                
                p_type = pinfo.Type
                ext_type = ExtType2(entry, self.engine, 
                    p_type.typeName, p_type.typeClass)
                entry.type = ext_type
                attr_def = self.engine.find_attribute_interface(
                    self.current, name)
                if attr_def is False: attr_def = ""
                entry.code_entry = self.code(
                    type=CGType.ATTR, mode=CGMode.SET, key=name, value_type=entry.type, args=arg, idl=attr_def)
            except Exception as e:
                print(("Error to set attribute: " + str(e)))
                traceback.print_exc()
            return None
        
        method_name = "set%s" % name
        if not entry.inspected.hasMethod(method_name, MethodConcept.ALL):
            self.status("Property %s is readonly." % name)
            if self.mode:
                return
            else:
                raise AttributeError("Unknown method %s" % name)
        return self.call_method(method_name, get_args=get_args, args=(arg,), pseud=True)
    
    def call_method(self, name, get_args=None, args=None, pseud=False):
        """ Frontend to invoke method. """
        method = self.engine.get_method_info(self.current, name, raw=True)
        if method is None: return
        param_infos = method.getParameterInfos()
        if self.mode:
            if 0 < len(param_infos):
                try:
                    if get_args:
                        args = tuple(get_args(method))
                except CancelException:
                    return
                except:
                    traceback.print_exc()
                    return
            else:
                args = ()
        try:
            return self.invoke_method(method, args, pseud=pseud)
        except Exception as e:
            self.status(str(e))
            traceback.print_exc()
            if self.mode:
                return
            else:
                raise
    
    def extract_args(self, args):
        """ Extract value from Entry instance. """
        _any = False
        if isinstance(args, tuple) or isinstance(args, list):
            a = []
            for arg in args:
                v, __any = self.extract_args(arg)
                a.append(v)
                if __any:
                    _any = True
            return tuple(a), _any
        else:
            if isinstance(args, Entry):
                target = args.get_target()
                extracted, __any = self.extract_args(target)
                if isinstance(target, uno.Any) or __any:
                    _any = True
                return extracted, _any
            else:
                return args, _any
    
    def get_out_param_index(self, idl):
        """ Returns list of out/inout param indexes. """
        params = idl.getParameterInfos()
        if params:
            return [i for i, info in enumerate(params) 
                if info.aMode == ParamMode.OUT or info.aMode == ParamMode.INOUT]
        else:
            return None
    
    def invoke_method(self, method, args, name=None, pseud=False):
        try:
            if not name:
                if args:
                    name = "%s(%s)" % (method.getName(), 
                        ", ".join([str(a) for a in args]))
                else:
                    name = "%s()" % method.getName()
            out_params = self.get_out_param_index(method)
            if self.mode:
                _args, _any = self.extract_args(args)
                value, d = method.invoke(self.current.target, _args)
            else:
                _args, _any = self.extract_args(args)
                if _any:
                    value, d = uno.invoke(method, "invoke", (self.current.target, _args))
                else:
                    value, d = method.invoke(self.current.target, _args)
            
            ret_type = method.getReturnType()
            entry = self.engine.create(self, name, value)
            if ret_type.getTypeClass() == TypeClass.ANY:
                # check the method from container
                if self.engine.check_method_from_container(method):
                    _type = self.current.target.getElementType()
                    ret_type = self.engine.for_name(_type.typeName)
                    # added to solve problem on new configuration
                    if ret_type.getTypeClass() == TypeClass.VOID:
                        ret_type = self.engine.get_type(entry)
            
            entry.type = ret_type
            value_type = ExtAnyType2(entry, self.engine, ret_type.getName(), ret_type.getTypeClass())
            entry.type = value_type
            if pseud:
                code_type = CGType.PSEUD_PROP
            else:
                code_type = CGType.METHOD
            entry.code_entry = self.code(
                    type=code_type, key=method.getName(), 
                    value_type=value_type, args=args, idl=method)
            if out_params:
                param_infos = method.getParameterInfos()
                _d = []
                for i, v in zip(out_params, d):
                    _key = "%s_%s" % (name, i)
                    _entry = self.engine.create(self, _key, v)
                    _entry.type = param_infos[i]
                    type = _entry.type.aType
                    _entry.type = ExtType2(_entry, self.engine, type.getName(), type.getTypeClass())
                    _d.append(_entry)
                    _entry.code_entry = args[i].code_entry
                ret = self.action_by_type(entry)
                return (ret,) + tuple(_d)
            else:
                return self.action_by_type(entry)
        except InvocationTargetException as e:
            te = e.TargetException
            self.error("Method: %s invocation exception.\nError Message: \n%s" % (
                method.getName(), te.Message))
            traceback.print_exc()
        except Exception as e:
            self.error("Method: %s unknown exception.\nError Message: \n%s" % (
                name, str(e)))
            traceback.print_exc()
    
    def get_struct_element(self, name):
        """ Get field value from current struct. """
        entry = self.current
        target = entry.target
        try:
            found = self.engine.find_field(name, self.engine.get_type(entry))
        except:
            return
        try:
            value = getattr(target, name)
            field_type = found.getType()
            if field_type == None:
                field_type = self.engine.reflection.getType(value)
            entry = self.engine.create(self, name, value)
            # ToDo
            ext_type = ExtAnyType2(entry, self.engine, 
                field_type.getName(), field_type.getTypeClass())
            entry.type = ext_type
            entry.code_entry = self.code(
                type=CGType.FIELD, mode=CGMode.GET, key=name, value_type=entry.type, idl=self.engine.get_type(self.current))
            return self.action_by_type(entry)
        except Exception as e:
            print(("Error: get_struct_element, " + str(e)))
            traceback.print_exc()
    
    def set_struct_element(self, name, value=None, get_value=None):
        entry = self.current
        target = entry.target
        try:
            found = self.engine.find_field(name, self.engine.get_type(entry))
        except:
            return
        if self.mode:
            try:
                if get_value:
                    old_value = getattr(target, name)
                    value = get_value(name, found.getType().getName(), found.getType().getTypeClass(), 
                            ("", ""), "current: " + str(old_value))
            except Exception as e:
                print(e)
                return
        try:
            if self.mode:
                _arg, _any = self.extract_args(value)
                setattr(target, name, _arg)
                entry = self.engine.create(self, name, _arg)
            else:
                _arg, _any = self.extract_args(value)
                setattr(target, name, _arg)
                entry = self.engine.create(self, name, _arg)
            field_type = found.getType()
            if field_type == None:
                field_type = self.engine.reflection.getType(value)
            ext_type = ExtType2(entry, self.engine, 
                    field_type.getName(), field_type.getTypeClass())
            entry.type = ext_type
            entry.code_entry = self.code(
                type=CGType.FIELD, mode=CGMode.SET, key=name, value_type=entry.type, args=value, idl=self.engine.get_type(self.current))
        except Exception as e:
            print(("Error: get_struct_element, " + str(e)))
            traceback.print_exc()
    
    def action_by_type(self, entry):
        if entry.target is None:
            if self.mode:
                return self.message("void")
            else:
                return None
        
        type_name = entry.type.getName()
        type_class = entry.type.getTypeClass()
        if not self.mode and type_name in values.IGNORED_INTERFACES:
            return self.error(
                "You can not inspect \n%s \ntype value, sorry." % type_name, 
                "Listed in the IGNORED_INTERFACES list.")
        try:
            if type_class == TypeClass.ANY:
                value_type = ExtAnyType2(entry, self.engine)
                type_name = value_type.getName()
                type_class = value_type.getTypeClass()
            if type_class in TypeClassGroups.NUMERIC:
                self.message(str(entry.target), type_name)
            elif type_class == TypeClass.STRING:
                if entry.target:
                    value = entry.target
                else:
                    value = ""
                self.message(value, type_name)
            elif type_class == TypeClass.BOOLEAN:
                self.message(str(entry.target), type_name)
            elif type_class == TypeClass.INTERFACE:
                self.change_entry(entry)
            elif type_class == TypeClass.STRUCT:
                self.change_entry(entry)
            elif type_class == TypeClass.SEQUENCE:
                self.change_entry(entry) # ToDo
            elif type_class == TypeClass.ENUM:
                self.message("%s.%s" % (type_name, entry.target.value), type_name)
            elif type_class == TypeClass.BYTE:
                self.message("%s" % entry.target, type_name)
            elif type_class == TypeClass.TYPE:
                self.message(entry.target.typeName, type_name)
            elif type_class == TypeClass.VOID:
                self.message("void", type_name)
            elif type_class == TypeClass.CHAR:
                self.message(entry.target.value, type_name)
            else:
                try:
                    self.message(str(entry.target), "unknown type")
                except:
                    self.error("Error: value to string conversion.")
        except Exception as e:
            print(e)
            print(("%s, %s" % (type_name, type_class)))
            traceback.print_exc()
        return entry
    
    def manage_sequence(self, entry, k=None):
        if len(entry.target) == 0:
            self.message("empty sequence")
            return None
        value_type = entry.type
        try:
            c_type = value_type.getComponentType()
        except:
            value_type = self.engine.get_type(entry)
            c_type = value_type.getComponentType()
        
        comp_type = None
        if c_type.getTypeClass() == TypeClass.SEQUENCE:
            comp_type = self.engine.get_component_base_type(value_type)
        type_class = c_type.getTypeClass()
        #if not self.mode:
        value = entry.target[k]
        new_entry = self.engine.create(self, "[%s]" % k, value)
        new_entry.type = c_type
        new_entry.code_entry = self.code(
            type=CGType.ELEMENT, mode=CGMode.GET, key=k, value_type=new_entry.type, idl=new_entry.type)
        
        if type_class == TypeClass.INTERFACE or type_class == TypeClass.ANY:
            self.change_entry(new_entry)
        elif type_class == TypeClass.STRUCT:
            self.change_entry(new_entry)
        elif type_class == TypeClass.SEQUENCE:
            self.change_entry(new_entry)
        else:
            self.action_by_type(new_entry)
        return new_entry
    
    def _get_value(self, args):
        if isinstance(args, tuple):
            return tuple([self._get_value(arg) for arg in args])
        else:
            return args.target if isinstance(args, Entry) else args
    
    # for macros
    def get_component_context(self):
        entry = self.engine.create(self, "XComponentContext", self.ctx)
        entry.code_entry = self.code(
            type=CGType.CONTEXT, key="XComponentContext", value_type=entry.type, idl=entry.type)
        return entry
    
    def assign_element(self, k, value, append=False):
        entry = self.current
        self.code(
            type=CGType.ELEMENT, mode=CGMode.SET, key=k, value_type=entry.type.getComponentType(), idl=entry.type.getComponentType(), args=value, misc=append)
    
    def create_service(self, name, *args, **kwds):
        """
        if args:
            _args, _any = self.extract_args(args)
            if _any:
                obj, d = uno.invoke(self.ctx.getServiceManager(), "createInstanceWithArgumentsAndContext", (name, _args, self.ctx))
            else:
                obj = self.ctx.getServiceManager().\
                createInstanceWithArgumentsAndContext(name, _args, self.ctx)
        else:
        """
        obj = self.ctx.getServiceManager().\
                createInstanceWithContext(name, self.ctx)
        if "nocode" in kwds: return obj
        entry = self.engine.create(self, name, obj)
        entry.code_entry = self.code(
            type=CGType.SERVICE, key=name, value_type=entry.type, 
            args=args, idl=entry.type)
        return entry
    
    # ToDo initial arguments
    def create_struct(self, type_name, *args, **kwds):
        _args, _any = self.extract_args(args)
        struct = uno.createUnoStruct(type_name, *_args)
        if "nocode" in kwds: return struct
        entry = self.engine.create(self, type_name, struct)
        entry.code_entry = self.code(
            type=CGType.STRUCT, key=type_name, value_type=entry.type, idl=entry.type, args=args)
        return entry
    
    # ToDo allows to pass initial values?
    def create_sequence(self, type_name, length, var=None):
        entry = self.engine.create(self, type_name, ())
        entry.target = []
        entry.type = self.engine.for_name(type_name)
        entry.code_entry = self.code(
            type=CGType.SEQ, key=type_name, value_type=entry.type, idl=entry.type, args=length, misc=var)
        return entry
    
    def declare_variable(self, type_name, value):
        entry = self.engine.create(self, type_name, value)
        entry.type = self.engine.for_name(type_name)
        entry.code_entry = self.code(
            type=CGType.VARIABLE, args=value, key=type_name, value_type=entry.type, idl=entry.type)
        return entry

