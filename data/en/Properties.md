
# Properties

You can see properties' information of UNO objects.

When you select Properties scope, information of the current target object is shown.

## Looking at Property Information

Properties are listed every line in the information edit.

|Name|Type|Value|Info.|Attr.|
|----|----|----|----|----|
|CharFontName|string|Times New Roman|Maybevoid|
|AvailableServiceNames|[]string| -SEQUENCE-|Pseud|ReadOnly|

In the case of CharFontName property, type of its value is "string", value is "Times New Roman", no Info., property value is "Maybevoid".

Next AvailableServiceNames property has "[]string" type value means a sequence of string type value. Its value is shown like "-SEQUENCE-" means -type- value can not be converted to string. Its Info. column shows "Pseud" describing this property is a pseud property (see below about pseud property).

## Pseud Property

Pseud property is very depends on the implementation of the binding of the language which you use to write a macro.

There are two types of properties. One is normal property. And another is mapped by the introspection and these properties are called "pseud property". 
For example getArgs method is maped to Args property and it is pseud property. Pseud properties do not have their entries in com.sun.star.beans.XPropertySet interface, therefore, you can not to get these property values through XPropertySet interface (getPropertyValue and setPropertyValue methods can not use to get these property values).

If getXXX method and setXXX method is there, XXX pseud-property is readable and writable. If only getXXX method is supported, it it read-only and only setXXX method is supported, it is just write-only.

Pseud property is created from method having prefix like get, set and is.

MRI uses XPropertySet interface of the target to get its property values, therefore, values of pseud properties are not able to get. However pseud properties are used frequently in codes. Therefore MRI calls the base method of the pseud property when you call a pseud property in the convenient purpose.

If you want to know about Attribute well, see com.sun.star.beans.PropertyAttribute constants group. 

In the case of a property having a string type value, CR and LF are replaced by "\r" and "\n". And long texts are abbreviated.

## Special Notations

Sometimes MRI shows special notations in the type, value and information of a property.

In the type information, these notation is used.

|Type|Description|
|----|----|
|[]type|Sequence of value type|

These notations are shown in the value information.

|Value|Description|
|----|----|
|""|Empty string.|
| -void|No value.|
| -UPPERCASE-|Value could not be converted to the string type.|
| -Error-|Error raised during to get its value.|

Pseud or other information are there and listed in the table below.

|Information|Description|
|----|---|
|Pseud|Pseud property.|
| -----|Its value could not to get|
|Ignored|Listed in the ignored list of properties.|
|Attr.|Attribute of an interface.|

## Getting Property Values

Set the mode to "Get" from the Mode menu of the MRI window and double click a line shows a name of a property that you want to get its value. MRI shows values according to the type class of the properties.

## Setting Property Values

If mode is set to "Set", you can set a property value having numerical, string, enum or boolean type value.

When you double click a line, the property is not read-only and it has numerical, string, enum or boolean value, the dialog box is shown. Input a new value of the property in its edit box. A inputted value is converted to appropriate type value for the property.

Boolean type value is converted in this rule, 0 or false: False, 1 or true: True and others: False (string type notation is compared in its lowercase).

If the property is pseud property, the method corresponds to the property is called. See Methods Needing Arguments section about calling a method.

When you set a property value, MRI reloads the information of the property and tries to keep the carret position and scrolled value of the information edit.

## Modifier Keys

You can get or set property values by double clicking on the information edit. You can use Ctrl and Alt keys as modifire key.

|Key|Description|
|----|----|
|Ctrl|Suppress actions caused by double clickings.|
|Alt|Temporary, change the mode Get to Set or Set to Get.|
