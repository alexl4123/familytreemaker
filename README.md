familytreemaker
===============

Forked from [familytreemaker](https://github.com/adrienverge/familytreemaker).
New main features: **JSON** support, **ANCESTOR TREE**, mixed **ANCESTOR-FAMILY** tree.



This program creates family tree graphs from simple text files.

The input file format is very simple, you describe persons of your family line
by line, children just have to follow parents in the file. Persons can be
repeated as long as they keep the same name or id. An example is given in the
file `LouisXIVfamily.txt`.


Installation
------------

Simply clone the repo.

This script outputs a graph descriptor in DOT format. To make the image
containing the graph, you will need a graph drawer such as [GraphViz] [1].

[1]: http://www.graphviz.org/  "GraphViz"

Usage
-----

Synapsis:
```
usage: familytreemaker.py [-h] [-a ANCESTOR] [--format {json,old}] [-c]
                          [--tree-type {family,ancestor,family-ancestor}]
                          INPUTFILE

Generates a family tree graph from a simple text file

positional arguments:
  INPUTFILE             the formatted text file representing the family

options:
  -h, --help            show this help message and exit
  -a ANCESTOR           make the family tree from an ancestor (if omitted, the program will try to find an
                        ancestor)
  --format {json,old}   Specify the format
  -c                    Provided --format=old, then with -c you can convert the old format to json format (old format formatted with 4-spaces, not tabs).
  --tree-type {family,ancestor,family-ancestor}
                        Specify the tree type, you can choose between family tree (all descendents of one
                        person),ancestor (all ancestors of one person, specify "-a <PERSON>" explicitly), family-
                        ancestor (both, family and ancestor tree, specify "-a <PERSON>")
```


The sample family descriptor `LouisXIVfamily.txt` is here to show you the
usage. Simply run:
```
$ ./familytreemaker.py -a 'Louis XIV' LouisXIVfamily.json | dot -Tpdf -o LouisXIVfamily.pdf
```
For .png run:
```
$ ./familytreemaker.py -a 'Louis XIV' LouisXIVfamily.txt | dot -Tpng -o LouisXIVfamily.png
```

Modes:
1. family: Normal family tree behavior, prints fron an ancestor all descendents (top-down graph)
2. ancestor: From a person specified with `-a`, prints all ancestors (bottom-up graph)
3. family-ancestor: Prints from a person specified with `-a` all ancestors, and all descendents (top-down, and bottom-up graph)

Person/Ancestor `-a`:
Specify ID or name of person. Multiple (comma separated, e.g., `-a "Name1,Name2") possible for ancestor tree, single one for family tree.
If multiple are specified for a family tree, first one is taken.



For the old format run:
```
$ ./familytreemaker.py -a 'Louis XIV' --format=old LouisXIVfamily.txt | dot -Tpdf -o LouisXIVfamily.pdf
```

It will generate the tree from the infos in `LouisXIVfamily.txt`, starting from
*Louis XIV* and saving the image in `LouisXIVfamily.png`.

Convert from the old format to JSON:
```
./familytreemaker.py -a 'Louis XIV' LouisXIVfamily.txt --format=old -c > LouisXIVfamily.json
```

Examples:
----------

```
./familytreemaker.py LouisXIVfamily.json -a 'LouisXIV' --tree-type=family  | dot -Tpng -o LouisXIVfamily.png
```

You can see the result for the family tree:

![result: LouisXIVfamily.png](/LouisXIVfamily.png)


```
./familytreemaker.py LouisXIVfamily.json -a 'Philippe' --tree-type=ancestor  | dot -Tpng -o PhilippeAncestor.png
```

You can see the result for the ancestor tree:

![result: PhillippeAncestor.png](/PhillippeAncestor.png)


