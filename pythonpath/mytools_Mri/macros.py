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
import os
import os.path
import types

import mytools_Mri.tools
import mytools_Mri.values


class ModuleEntry(object):
    """ Keeps file name and module. """
    def __init__(self, name, module):
        """ Instantiate new entry with the file name and module. """
        self.name = name
        self.module = module


class Macros(object):
    """ Manages list of macros and execute macros. """
    
    EXTENSION = ".py"
    MACROS = "macros"
    EXT_MACROS_DIR = None
    USER_MACROS_DIR = None
    
    FILE_NAMES = None
    MODULES = {}
    
    EXTENSION_CONTEXT = "extension"
    USER_CONTEXT = "user"
    
    def __init__(self, main):
        self.main = main
        self.loaded = False
        if Macros.EXT_MACROS_DIR is None:
            Macros.EXT_MACROS_DIR = uno.fileUrlToSystemPath(
                mytools_Mri.values.MRI_DIR + "/" + self.MACROS)
        if Macros.USER_MACROS_DIR is None:
            self.set_user_dir(main.config.macros)
    
    def is_loaded(self):
        """ Check macros have been loaded. """
        return self.loaded
    
    def set_user_dir(self, url):
        """ Change user's directory. """
        if url.startswith("$"):
            ctx = self.main.ctx
            url = ctx.getServiceManager().createInstanceWithContext(
                "com.sun.star.util.PathSubstitution", ctx).\
                    substituteVariables(url, True)
        Macros.USER_MACROS_DIR = uno.fileUrlToSystemPath(url)
    
    def clear(self):
        """ Clear and reset. """
        Macros.FILE_NAMES = None
        Macros.MODULES = {}
        self.loaded = False
    
    def get_macro_names(self):
        """ Get macro file names. """
        try:
            if Macros.FILE_NAMES is None:
                Macros.FILE_NAMES = self.reload()
            self.loaded = True
            return Macros.FILE_NAMES
        except Exception as e:
            print(e)
    
    def reload(self):
        """ Try to load file names from repositories. """
        ext = self.EXTENSION
        names = []
        
        def search_repository(a, repo):
            if os.path.exists(repo):
                items = os.listdir(repo)
                for item in items:
                    if item.endswith(ext):
                        a.append(os.path.join(repo, item))
        
        search_repository(names, Macros.EXT_MACROS_DIR)
        search_repository(names, Macros.USER_MACROS_DIR)
        return names
    
    def get_functions(self, file_name):
        """ Load the file and try to get fnction names from it. 
            First line of the __doc__ is used for menu title.
            Return value is list of [function_name, title, description].
        """
        items = []
        if os.path.exists(file_name):
            mod = self._load_file(file_name)
            if "__all__" in mod.__dict__:
                for name in mod.__dict__["__all__"]:
                    if name in mod.__dict__:
                        fn = mod.__dict__[name]
                        if isinstance(fn, types.FunctionType):
                            _doc = fn.__doc__
                            if _doc is None: _doc = ""
                            lines = _doc.split("\n", 1)
                            if len(lines) > 1:
                                title = lines[0]
                                doc = lines[1]
                            else:
                                title = name
                                doc = _doc
                            items.append(
                                (name, title.strip(), doc.strip()))
                    else:
                        items.append(None)
        return items
    
    def get_function_info(self, file_name, func_name):
        """ Returns list of function informations. """
        item = None
        if os.path.exists(file_name):
            mod = self._load_file(file_name)
            if "__all__" in mod.__dict__ and func_name in mod.__all__:
                fn = mod.__dict__[func_name]
                if isinstance(fn, types.FunctionType):
                    _doc = fn.__doc__
                    if _doc is None: _doc = ""
                    lines = _doc.split("\n", 1)
                    if len(lines) > 1:
                        title = lines[0]
                        doc = lines[1]
                    else:
                        title = func_name
                        doc = _doc
                    item = (func_name, title.strip(), doc.strip())
        return item
    
    def _load_file(self, file_name):
        """ Load the file as a module. """
        name = os.path.basename(file_name)
        if name.endswith(self.EXTENSION) and len(name) > len(self.EXTENSION):
            name = name[0:-len(self.EXTENSION)]
        if not isinstance(name, str):
            name = name.encode("utf-8")
        mod = type(os)(name)
        with open(file_name, "r") as f:
            code = compile(f.read(), name + self.EXTENSION, "exec")
        exec(code, mod.__dict__)
        entry = ModuleEntry(file_name, mod)
        Macros.MODULES[file_name] = entry
        return mod
    
    def get_function(self, file_name, func_name, context=None):
        """ Get function object specified. """
        if context:
            if context == self.EXTENSION_CONTEXT:
                file_name = os.path.join(self.EXT_MACROS_DIR, file_name)
            elif context == self.USER_CONTEXT:
                file_name = os.path.join(self.USER_MACROS_DIR, file_name)
        if not file_name in Macros.MODULES:
            self._load_file(file_name)
        entry = Macros.MODULES[file_name]
        mod = entry.module
        return mod.__dict__[func_name]
    
    def execute(self, file_name, func_name, context=None, *args):
        """ Execute specified macro. """
        fn = self.get_function(file_name, func_name, context)
        if isinstance(fn, types.FunctionType):
            return func(self.main, *args)
        raise Exception("Illegal value: %s" % str(fn))

