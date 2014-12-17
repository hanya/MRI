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

import uno
try:
    from subprocess import Popen
    def execute(path, url):
        Popen([path, url]).pid
except:
    import os
    try:
        import thread
    except:
        import _thread as thread
    def execute(path, url):
        if os.sep == '\\':
            ctx = uno.getComponentContext()
            systemexecute = ctx.getServiceManager().createInstanceWithContext( 
                    "com.sun.star.system.SystemShellExecute", ctx)
            systemexecute.execute( 
                path, url, 1)
        else:
            thread.start_new_thread(
                lambda path, url: os.system("%s %s" % (path, url)), (path, url)
            )

class Web(object):
    """Open web file in browser."""
    
    def __init__(self, browser):
        self.set_browser(browser)
    
    def set_browser(self, browser):
        """set browser path."""
        self.browser = browser
    
    def open_url(self, url):
        """open url with browser."""
        try:
            execute(self.browser, url)
        except:
            raise
    

class IDL(Web):
    """ Including to support opening IDL document. """
    
    def __init__(self, cast, config):
        self.set_browser(config.browser)
        self.cast = cast
        self.set_sdk_path(config.sdk_path)
    
    def set_sdk_path(self, sdk_path):
        """set sdk directory path."""
        if sdk_path.endswith('/'):
            path = sdk_path
        else:
            path = "%s/" % sdk_path
        self.sdk_path = path
    
    def set_browser(self, browser):
        """set browser path."""
        Web.set_browser(self, uno.fileUrlToSystemPath(browser).replace("\\", '/'))
    
    def open_url(self, url):
        try:
            Web.open_url(self, url)
        except:
            self.cast.error("Fix your browser configuration.")
    
    def open_idl_reference(self, idltarget, word=''):
        """Open IDL Reference."""
        if idltarget:
            if word:
                template = "%sdocs/common/ref/%s.html#%s"
                idlurl = template % (self.sdk_path, idltarget.replace('.', '/'), word)
            else:
                template = "%sdocs/common/ref/%s.html"
                idlurl = template % (self.sdk_path, idltarget.replace('.', '/'))
            
            self.open_url(idlurl)
        else:
            self.cast.status('IDL target was not found.')


class DoxygenIDLRef(IDL):
    """ Link to Doxygen based IDL reference. """
    
    def open_idl_reference(self, idltarget, word=""):
        if idltarget:
            # ToDo support link to anchor
            if word:
                template = "{BASE}docs/idl/ref/{TYPE}{NAME}.html#{ANCHOR}"
                try:
                    type, target = self._get_target(idltarget)
                except Exception as e:
                    self.cast.status("Error: " + str(e))
                    return
                anchor = self._get_anchor(idltarget, word, type)
                idlurl = template.format(BASE=self.sdk_path, 
                    TYPE=type, NAME=target, ANCHOR=anchor)
            else:
                template = "%sdocs/idl/ref/%s%s.html"
                type, target = self._get_target(idltarget)
                idlurl = template % (self.sdk_path, type, target)
            
            self.open_url(idlurl)
        else:
            self.cast.status("IDL target was not found.")
    
    def _get_target(self, idltarget):
        idl_type = self.cast.engine.get_module_type(idltarget)
        if idl_type in ("CONSTANTS", "TYPEDEF"):
            return "namespace", idltarget.replace(".", "_1_1")
        elif idl_type == "ENUM":
            return "namespace", idltarget[0:idltarget.rfind(".")].replace(".", "_1_1")
        return idl_type.lower(), idltarget.replace(".", "_1_1")
    
    def _get_anchor(self, idltarget, word, type):
        import hashlib
        target = idltarget
        if type in ("service", "struct", "exception"):
            pass
        else:
            target = idltarget + "::" + word
        try:
            idl = self.cast.engine.tdm.getByHierarchicalName(target)
        except:
            idl = None
        if idl:
            anchor_value = ""
            idl_type_name = idl.getTypeClass().value
            if idl_type_name == "INTERFACE_METHOD":
                # ret_type namename([mode] type pname)
                idl_ret_type = idl.getReturnType()
                ret_type_name = self._check_type_name(
                    idl_ret_type, idltarget)
                idl_params = idl.getParameters()
                args=[]
                for param in idl_params:
                    mode = ("", "[in]", "[out]", "[inout]")[(1 if param.isIn() else 0) | (2 if param.isOut() else 0)]
                    idl_param_type = param.getType()
                    param_type = self._check_type_name(idl_param_type, idltarget)
                    
                    args.append("{MODE} {TYPE} {NAME}".format(
                        MODE=mode, TYPE=param_type, NAME=param.getName()))
                    
                anchor_value = "{RETURN_TYPE} {NAME}{NAME}({ARGS})".format(
                    RETURN_TYPE=ret_type_name, NAME=word, ARGS=",".join(args))
                
            elif idl_type_name == "INTERFACE_ATTRIBUTE":
                # val_type namename
                idl_value_type = idl.getType()
                type_name = self._check_type_name(idl_value_type, idltarget)
                anchor_value = "{TYPE_NAME} {NAME}{NAME}".format(
                    TYPE_NAME=type_name, NAME=word)
            
            elif idl_type_name == "SERVICE":
                # ToDo constructor can be detected in _check_type_name?
                full_name = "{BASE}.{NAME}".format(BASE=idltarget, NAME=word)
                found = None
                for prop in idl.getProperties():
                    if prop.getName() == full_name:
                        found = prop
                        break
                if found:
                    value_type = self._check_type_name(found.getPropertyTypeDescription(), idltarget)
                    anchor_value = "{TYPE_NAME} {NAME}{NAME}".format(
                        TYPE_NAME=value_type, NAME=word)
            
            elif idl_type_name in ("STRUCT", "EXCEPTION"):
                # ToDo engine.find_declared_module found base class but needs searching here?
                found = None
                for name, member in zip(idl.getMemberNames(), idl.getMemberTypes()):
                    if name == word:
                        found = member
                        break
                if found:
                    type_name = self._check_type_name(found, idltarget)
                    anchor_value = "{TYPE_NAME} {NAME}{NAME}".format(
                        TYPE_NAME=type_name, NAME=word)
                
            return self._get_anchor_md5(anchor_value)
    
    def _check_type_name(self, idl, current):
        type_class_name = idl.getTypeClass().value
        
        if type_class_name in ("INTERFACE", "STRUCT", "EXCEPTION"):
            # If the target value is defined in the same module, 
            # its name can be abbreviated. But there is no way to know 
            # it is really abbreviated or not in the definition.
            # Doxygen uses written format to generate anchor value, 
            # and then no way to make this match with them.
            name = idl.getName()
            #return name.replace(".", "::") # always full format
            if name[0:name.rfind(".")] == current[0:current.rfind(".")]:
                return name[name.rfind(".")+1:]
            else:
                return name.replace(".", "::")
        elif type_class_name == "SEQUENCE":
            inner_type = self._check_type_name(idl.getReferencedType(), current)
            return "sequence< {TYPE} >".format(TYPE=inner_type)
        elif type_class_name in ("ENUM", "TYPEDEF"):
            return idl.getName().replace(".", "::")
        else:
            return idl.getName()
    
    def _get_anchor_md5(self, value):
        """ Generate md5 value in hex from passed value. """
        import hashlib
        h = hashlib.md5()
        h.update(value.encode("utf-8"))
        return "a" + h.hexdigest() # a is prefix by doxygen


def create_IDL_opener(cast, config, doxygen_based=False):
    klass = DoxygenIDLRef if doxygen_based else IDL
    return klass(cast, config)
