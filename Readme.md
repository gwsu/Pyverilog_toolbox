Introduction
==============================
Pyverilog_toolbox is Pyverilog based verification/design tool.
Including register map analyzer.
Other feature is intendet to be implemented in the future.


Software Requirements
==============================
* Python (2.7)
* Pyverilog (you can download from https://github.com/shtaxxx/Pyverilog)


License
Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)

Installation

If you want to use Pyverilog as a general library, you can install on your environment by using setup.py. 

If you use Python 2.7,

```
python setup.py install
```

Python 3.x is not tried by author.


Usage
==============================
After install, you can use regmap analyzer by this command.

```
python ra_interface xxxx.v -S config.txt
```


xxxx.v is regmap RTL file.
To analyse register map, config file is needed.

testcode/regmap.v is example of register map RTL file,
and testcode/setup.txt is example of config file.

Analysys result will be output as out.csv.

ex.

```
Write Map		
ADD	1	0
0	TOP.reg0[1]	TOP.reg0[0]
1		TOP.reg1[0]
Read Map		
ADD	1	0
0	TOP.reg0[1]	TOP.reg0[0]
1		TOP.reg1[0]
```

License
==============================

Apache License 2.0
(http://www.apache.org/licenses/LICENSE-2.0)


Copyright and Contact
==============================

Copyright (C) 2015, Ryosuke Fukatani