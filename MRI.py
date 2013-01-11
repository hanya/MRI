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

IMPLE_NAME = "mytools.Mri"

def create(ctx, *args):
    try:
        import mytools_Mri.component
        return mytools_Mri.component.create(IMPLE_NAME, ctx, *args)
    except Exception as e:
        print(e)

# Registration
import unohelper
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(
    create, IMPLE_NAME, (IMPLE_NAME,),)

