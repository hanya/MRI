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

