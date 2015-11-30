
# User Interface

The MRI window has some controls and the menubar.

## Controls

### MRI Window
You can resize the MRI window. And you can use multiple MRI windows at a time. MRI can change initial position and inilial size of MRI window, use Configuration Button for this purpose. See Configuration section in detail.

### Menubar
You can access to some functions from menu entries. Each entry is described in Menubar section.

### Scope Listbox
Select an item from scope list you want to take a kind of information about the current target.

<!-- {{Bookmark|hid/mytools.Mri:list_category|Scope list box}} -->

<!-- {{aHelp|mytools.Mri:list_category|hidden|Information category}} -->

### Implementation Name Text Field
This control is placed at the bottom part of the window. This edit box shows ImplementationName of the target.

<!-- {{Bookmark|hid/mytools.Mri:edit_in|Implemenation Name Field}} -->

<!-- {{aHelp|mytools.Mri:edit_in|hidden|Implementation name of the current target}} -->

### Object Type Name Text Field
Object type indicates the type of the target. This value is taken from com.sun.star.reflection.CoreReflection service.

<!-- {{Bookmark|hid/mytools.Mri:edit_type|Object type field}} -->

<!-- {{aHelp|mytools.Mri:edit_type|hidden|Type name of the target}} -->

### History Listbox
History Listbox have a list of targets. Histories are updated when you call properties or methods returns an object. You can change the target using this listbox.

<!-- {{Bookmark|hid/mytools.Mri:list_hist|History listbox}} -->

<!-- {{aHelp|mytools.Mri:list_hist|hidden|Targets histories}} -->

### Go Back Button
Show previous target form the history now selected.

<!-- {{Bookmark|hid/mytools.Mri:btn_back|Go Back Button}} -->

<!-- {{aHelp|mytools.Mri:btn_back|hidden|Go back to the previous target}} -->

### Go Forward Button
Show previous target form the history now selected.

<!-- {{Bookmark|hid/mytools.Mri:btn_forward|Go Forward Button}} -->

<!-- {{aHelp|mytools.Mri:btn_forward|hidden|Go to the next target}} -->

### Search Text Edit
You want to search text inside the information edit.

<!-- {{Bookmark|hid/mytools.Mri:edit_search|Search field}} -->

<!-- {{aHelp|mytools.Mri:edit_search|hidden|Search text}} -->

### Search Button
Start searching from ending of the cursor position of the information edit.

<!-- {{Bookmark|hid/mytools.Mri:btn_search|Search Button}} -->

<!-- {{aHelp|mytools.Mri:btn_search|hidden|Start to search}} -->

### Open IDL Reference Button
Open the IDL Reference page according to the selected scope. If you want to use this button to open IDL Reference, see Configuration section and configure the settings. If Properties or Methods scope is selected and selection begins "." in information edit, MRI ascribes a selected text connected with "com.sun.star". If Methods scope selected and not selected in information edit, IDL reference page of the interface of a method shown in carret line. A carret line text is used as IDL Reference page if Interfaces or Services scope is selected. You may not to select texts that you want to open the page of IDL Reference.

<!-- {{Bookmark|hid/mytools.Mri:btn_ref|Open IDL Reference Button}} -->

<!-- {{aHelp|mytools.Mri:btn_ref|hidden|Push to open IDL Reference}} -->

### Information Edit
All information about the target shown here. Double click a line of the displayed text, you can get property value if Properties scope selected or invoke method and get its return value if Methods scope selected. A font name and a character size used in this edit can be changed using Configuration button. See Configuration section. If this control is focused on, some shortcut keys are used. See Shortcut Keys section about them.

<!-- {{Bookmark|hid/mytools.Mri:edit_info|Information Edit}} -->

<!-- {{aHelp|mytools.Mri:edit_info|hidden|Information of the target}} -->

### Information Label
MRI shows information here.

<!-- {{Bookmark|hid/mytools.Mri:label_status|Information Label}} -->

<!-- {{aHelp|mytools.Mri:label_status|hidden|Status}} -->

### Code Edit
Code is shown on this area. The type of code can be chose from Tools - Code.

<!-- {{Bookmark|hid/mytools.Mri:edit_code|Code Edit}} -->

<!-- {{aHelp|mytools.Mri:edit_code|hidden|Shows piece of code}} -->

### Splitter
Double-click on this control to show/hide code edit.

<!-- {{Bookmark|hid/mytools.Mri:splitter|Splitter}} -->

<!-- {{aHelp|mytools.Mri:splitter|hidden|Splitter for code edit}} -->

### index button
This button provides shortcut to call getByIndex method if the current target supports com.sun.star.container.XIndexAccess interface.

<!-- {{Bookmark|hid/mytools.Mri:btn_index|Index Button}} -->

<!-- {{aHelp|mytools.Mri:btn_index|hidden|Shortcut to getByIndex method.}} -->

### name button
This button allows you to call getByName method directory if com.sun.star.container.XNameAccess interface is supported by the target.

<!-- {{Bookmark|hid/mytools.Mri:btn_name|Name Button}} -->

<!-- {{aHelp|mytools.Mri:btn_name|hidden|Shortcut to getByName method.}} -->

## Menubar

Descriptions of the menubar of the MRI window.

### File Menu
#### New
 Creates a new document and its model object is opened as a target for MRI.
#### Output
Makes a document about information of current target.
#### Rename
Changes title name of the current MRI window.
#### Diff
Compare two object about property values.

### Tools Menu
States of these checkable options in Tools menu are stored in the settings (see [Configuration](./Configuration.md) section).
#### Sort A-z
When this menu checked, information lines are sorted by A-Z, a-z order.
#### Abbreviated
If this menu checked, "com.sun.star." is replaced with "." (comma). For example, 
"com.sun.star.lang.XComponent" is shown like ".lang.XComponent". 
#### Show Labels
If checked this menu entry, labels are displayed in the infromation edit.
#### Code
Code generation menu. See [Code](./Code.md).
#### Configuration...
If you want to set your IDL Reference directory and your browser path, choose this entry. Configuration dialog opens when this menu is selected. And you can set initial position and size of MRI window. Configuration of MRI is described in Configuration section.

### Targets Menu
The Desktop, ServiceManager, new service and new structs are accessed directly as a target from this menu entries. And all frames attached to Desktop are accessed too.## Desktop## If you select Desktop entry, new instance of com.sun.star.frame.Desktop service is created as a target.
#### ServiceManager
If ServiceManager entry is selected, com.sun.star.lang.XMultiComponentFactory interface is taken as a taraget from default context.
#### Services
If you select this entry, dialog box having the edit control is open and input a service name that you want to instantiate as a target.
#### Structs
You can create new struct as a target like the service.
#### Frames
General application frames are attached using append method of 
com.sun.star.frame.XFrames interface accessed through getFrames method 
of com.sun.star.frame.XFramesSupplier interface supported by 
com.sun.star.frame.Desktop service. We can access to frames contained 
into its frames container through the Desktop. And we have no way to access 
to frames are not appended to its container. Child frames are accessed 
through its parent frames container. So, MRI can access frames attached to the Desktop.
When you select a frame from menu entries, MRI tries to get it as a target. 
If the frame that you selected is not exist, MRI fails to get it. 
These entries are updeated automatically when you select the Targets menu.
If you select a name from this list, MRI gets frame object having it from Desktop. 
After you select a frame object, the target is com.sun.star.frame.XFrame interface. 
If you want to see its model object, choose Controller property and next 
Model property of its controller (or use getController method and getModel method). 
See about how to get values of the target, Properties subsection.

### Mode Menu
This menu depends on only the property scope is selected. These Get and Set entries 
are radio type items.
#### Get
If Get mode selected, property values are got from the target and MRI shows them.
#### Set
Properties having numerical, string or boolean type value can be set their value.

### Window
Window changer like a normal Window menu of the general OpenOffice.org document window.

### Macros Menu
This menu shows macro entries.

### Help Menu
Help about MRI.
#### MRI Help
Open this help file.
#### What's This?
Show extended tool tip of the control.
#### About MRI
About MRI and its version information.
