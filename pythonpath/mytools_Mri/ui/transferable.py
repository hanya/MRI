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

import unohelper

from com.sun.star.datatransfer import XTransferable, DataFlavor


class transferable(unohelper.Base, XTransferable):
    """Keep clipboard data and provide them."""
    
    def __init__(self, text):
        df = DataFlavor()
        df.MimeType = "text/plain;charset=utf-16"
        df.HumanPresentableName = "encoded text utf-16"
        self.flavors = [df]
        self.data = [text] #[text.encode('ascii')]
    
    def getTransferData(self, flavor):
        if not flavor: return
        mtype = flavor.MimeType
        for i,f in enumerate(self.flavors):
            if mtype == f.MimeType:
                return self.data[i]
    
    def getTransferDataFlavors(self):
        return tuple(self.flavors)
    
    def isDataFlavorSupported(self, flavor):
        if not flavor: return False
        mtype = flavor.MimeType
        for f in self.flavors:
            if mtype == f.MimeType:
                return True
        return False


def set_clipboard_content(ctx, trans):
    """Set trans to the clipboard."""
    cl = ctx.getServiceManager().createInstanceWithContext(
        "com.sun.star.datatransfer.clipboard.SystemClipboard", ctx)
    if not cl:
        return
    cl.setContents(trans, None)


def set_text_to_clipboard(ctx, text):
    """Set text to the system clipboard."""
    try:
        trans = transferable(text)
        if not trans:
            return
        set_clipboard_content(ctx, trans)
    except Exception as e:
        print(e)

