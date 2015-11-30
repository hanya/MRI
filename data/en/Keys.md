
# Shortcut Keys

These shortcut keys can be used in the information edit.

|Keys|Description|
|----|----|
|Enter|Get/Set a value or call a method|
|Alt + LEFT|Go back|
|Alt + RIGHT|Go forward|
|Ctrl + P|Properties scope|
|Ctrl + M|Methods scope|
|Ctrl + I|Interfaces scope|
|Ctrl + S|Services scope|
|Ctrl + R|Open IDL Reference|
|Ctrl + F|Change the focus to the search edit|
|Ctrl + Q|Select a whole current line (only text mode)|
|Ctrl + W|Select the current word (text mode only)|
|Ctrl + A|Select all (text mode only)|
|Ctrl + V|Sort|
|Ctrl + B|Abbreviated|
|Ctrl + H|Show/Hide code field|
|Ctrl + J|Context menu on the grid control|
|Ctrl + U|index short cut|
|Ctrl + N|name short cut|

A few shortcut keys do not work depends on your window environment.

If MRI is in the grid mode, the context menu of the grid control provides few functions.

## Modifier Keys

When you double click the information edit of the MRI window, 
the following keys can be used:

|Modifier|Description|
|----|----|
|Ctrl|Open the object that will be taken by the operation (only interfaces and structs) in new MRI window.|
|Shift|Invalid the double click action.|
|Alt or Ctrl + Shift|Change the mode to do something about properties temporary.|


<!-- {{Bookmark|hid/mytools.Mri:ShortcutKeys|MRI Shortcut Keys}} -->

## Customize Shortcut Keys

Now shotcut keys of MRI can be changed through Tools - Configuration... dialog. Push Shortcut Keys button on the Configuration dialog to open Shortcut Keys dialog which allows to modify shortcut keys.

The settings for configured keys are stored in $(user)/config/mrikeys.pickle. Remove it if you do not need it anymore or if you want to back to all keys to default settings.

### Assign

Choose an entry from the list of commands and move focus in edit box, and then push key combinations. Push Assign button to bind the key to selected command. 

### Delete

Choose an entry in the list of commands and push Delete button on the dialog. Now the edit box is empty, push Assign button to reflect the current value to selected entry.

### Macros

Macro can be executed by to push key combinations. Push Macros button to add new entry for a macro. Macros should be stored under the directory of MRI macros or user's directory of macros, see Configuration page for more information.

Choose a macro entry on Macros dialog which is opened when you push Macros button of Shortcut keys dialog. After that, assign key combination to it according to assign section.

### Default

Push Default button to restore selected entry, and then push Assign button to bind to it.

### Add New

The list of entried allow only one key combination for each entries. If you want to bind the command to another key combination, push Add New button and choose a command to add it as new entry.

If you want to remove added entry, choose it and push Delete button and then push Assign button on the dialog. It will removed at the time to store the settings.

### Store

Push Store button to reflect your new key combinations and to store it in setting file.


