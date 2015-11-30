
# Type Mappings

|UNO Type|OOo Basic|Python|Java|C++|Description|
|----|----|----|----|----|----|
|void|internal type|None|void|void|Empty type, used only as method return type and in any.|
|boolean|Boolean|bool|boolean|sal_Bool|Can be true or false.|
|byte|Integer|long|byte|sal_Int8|Signed 8-bit integer type (ranging from -128 to 127, inclusive).|
|short|Integer|long|short|sal_Int16|Signed 16-bit integer type (ranging from －32768 to 32767, inclusive).|
|unshigned short|internal type|long|short|sal_uInt16|Unsigned 16-bit integer type (deprecated).|
|long|long|long|int|sal_Int32|Signed 32-bit integer type (ranging from －2147483648 to 2147483647, inclusive).|
|unsigned long|internal type|long|int|sal_uInt32|Unsigned 32-bit integer type (deprecated).|
|hyper|internal type|long|long|sal_Int64|Signed 64-bit integer type (ranging from －9223372036854775808 to 9223372036854775807, inclusive).|
|unsined hyper|internal type|long|long|sal_uInt64|Unsigned 64-bit integer type (deprecated).|
|float|Single|float|float|float|IEC 60559 single precision floating point type.|
|double|Double|float|double|double|IEC 60559 double precision floating point type.|
|char|internal type|uno.Char|char|sal_Unicode|Represents individual Unicode characters (more precisely: individual UTF-16 code units).|
|string|String|unicode|java.lang.String|rtl::OUString|Represents Unicode strings (more precisely: strings of Unicode scalar values).|
|type|com.sun.star.<br />reflection.XIdlClass|uno.Type|com.sun.star.<br />uno.Type|com::sun::star::<br />uno::Type|Meta type that describes all UNO types.|
|any|Variant|(uno.Any)|java.lang.Object|com::sun::star::<br />uno::Any|Special type that can represent values of all other types.|

* http://wiki.services.openoffice.org/wiki/Documentation/DevGuide/ProUNO/Professional_UNO
* http://udk.openoffice.org/python/python-bridge.html
