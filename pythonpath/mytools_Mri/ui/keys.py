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
import os.path

# Default keys. [command, mod, key]
default_keys = [
    ["execute", 0, 1280], 
    ["opennew", 3, 1280], 
    ["next", 4, 1027], 
    ["previous", 4, 1026], 
    ["properties", 2, 527], 
    ["methods", 2, 524], 
    ["interfaces", 2, 520], 
    ["services", 2, 530], 
    ["ref", 2, 529], 
    ["search", 2, 517], 
    ["selectline", 2, 528], 
    ["selectword", 2, 534], 
    ["sort", 2, 533], 
    ["abbr", 2, 513], 
    ["pseud_prop", 2, 526], 
    ["code", 2, 519], 
    ["contextmenu", 2, 521], 
    ["index", 2, 532], 
    ["name", 2, 525], 
    ["gridcopy", 2, 514]
]

class KeyConfigLoader(object):
    """ Loads key configuration. """
    
    KEYS = None
    CONFIG = "$(user)/config/mrikeys.pickle"
    
    def __init__(self, ctx):
        self.ctx = ctx
    
    def _create_service(self, name):
        return self.ctx.getServiceManager().createInstanceWithContext(
            name, self.ctx)
    
    def get_key_config_path(self):
        ps = self._create_service("com.sun.star.util.PathSubstitution")
        url = ps.substituteVariables(self.CONFIG, True)
        return uno.fileUrlToSystemPath(url)
    
    def load(self):
        data = None
        path = self.get_key_config_path()
        if os.path.exists(path):
            f = None
            try:
                try:
                    import cPickle as pickle
                except:
                    import pickle as pickle
                f = open(path, "rb")
                data = pickle.load(f)
            except:
                pass
            if f: f.close()
        return data
    
    def construct_keys(self, data=None):
        if KeyConfigLoader.KEYS and data is None:
            return KeyConfigLoader.KEYS
        if data is None:
            data = self.load()
        if data is None:
            data = default_keys
        # {(modifires, key): command}
        keys = {}
        for key in data:
            keys[(key[1], key[2])] = key[0]
        KeyConfigLoader.KEYS = keys
        return KeyConfigLoader.KEYS
