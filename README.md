# Solution of Python weekend entry task

## Author: Vera Kumova


This solution is written in __python 3.8__ and contains two python files:
- utils.py
- solution.py

File _utils.py_ contains three auxiliary classes:
- class __InputData()__ for reading an input file and performing some basic checks
- class __Graph()__ for computing all paths from the origin to the destination airport
- class __OutputGetter()__ for computing and printing the output in requested format

File solution.py containg the solution of the task, so the usage is
```bash
python solution.py data.csv BTW REJ --bags=1
```

There are implemented four optional arguments:
- __--bags__: Number of requested bags. Zero by default.
- __--return_flight__: Is it a return flight? False by default.
- __--max_transfer__: Max number of allowed interchange airports. By defalut the number of allowed interchange airports is not limited.
- __--max_layover_time__: Max time in hours for one layover time. The default is six as requested in the assignment.

When __return_flight__ is TRUE, then each possible flight __A -> B__ is followed by a list of all possible return flights __B -> A__. A possible return flight is one that departs at least 24 hours after the arrival of the incoming flight. If there are no possible return flights, then the original flight is not listed either.

For help use
```bash
python solution.py -h
```