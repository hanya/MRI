
# Code

Sometimes generated code is not executable without modifications. 
MRI can be called from UNO components, a scripting code, menu entries 
and so on, and MRI does not know how to be called. 
So, it is difficult to generate complete code.

## Code Menu

You can find the Code menu in the Tools menu entry. 
Check in Tools - Code - Code entry to show the code text field. 
The code text field is shown below the information text field and 
it can be resized by the dragging the border. 
Or double click with the right click of your mouse 
at the right bottom corner of the information text field. 
Or push Ctrl + H keys on the information edit.

## Code Type

A few kind of code can be chose from Tools - Code menu.

## Pseud Property

If selected language biding supports pseud-property, 
the code is generated with pseud-property call.

## Notices

MRI tries to get the type of the value from Type information, 
css.reflection.XMethodIdl interface and Reflection API, 
but sometimes there are less-typed values like an Any type of UNO. 
Typically, com.sun.star.beans.PropertyValue struct has string Name value, 
any Value and so on, the value retained by Value element 
is not well defined by the object. 
Sometimes they are defined by the other service like com.sun.star.document.MediaDescriptor etc. 
So, you need to check their type of values taken from any type. 
The same problems are there at methods return any type value.

Sometimes numerical values taken as an Any type values are miss typed.

## Adding New Code Generator

You can add new code generator.

Open the extension installed directory and goto the pythonpath/mytools_Mri/generators directory. 
Make a new code generator according to "code_generator.py" 
file and add new generator definition to "generators.py" file.
New generator will be shown in the Tools - Code menu.

Additional informations about code generators:

* You needs to know type mappings between UNO and your desired language like a listed [Type Mappings](./TypeMappings.md).
* Creation on your desired language like structs, enums, services and so on.
