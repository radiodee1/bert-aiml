# Contents

* `aiml_consume.py` - This file runs the stripped down AIML v1.0 interpreter using the BERT transformer for selecting the proper output. This file has several run time flags that allow you to copy all of the loaded `pattern` style strings. It also has an option for doing some simple output recording and stat calculation.

* `aiml_run_example.py` - This file runs the AIML v1.0 interpreter that is associated with the python-aiml library and does not use BERT.

* `maze_make_aiml.py` - This file uses the files in the `maze` directory to create an aiml file that, when using an aiml interpreter, plays a simplified version of a text adventure.

* `.env` - This file is used by the `aiml_consume.py` file to configure several BERT options.

# Usage

* cd into `./virtualenv/`
* source file with `. ./do_make_virtualenv_setup36.sh` (notice that there is a leading period before the shell script name!)
* cd into `../src`
* execute `./aiml_consume.py --raw-pattern`
* split output.txt file with `split -l500 output.txt output.` (notice that there is a trailing period!)
* count outputs with `./aiml_consume.py --count < output.aa`