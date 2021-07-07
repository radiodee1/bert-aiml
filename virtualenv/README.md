## Virtual Environment

You need to install python3.7, or 3.6, or build it yourself before launching the virtual environment scripts. You might need `libffi-dev`.

Files in this folder:
* `do_make_virtualenv_setup36.sh` -- run once to add virtualenv to the installed packages... or simply `source` this file.

These files probably work best if run with `source`. Type `deactivate` to exit the virtualenv.

## Building Python3.6

Make sure that `~/.local/bin` is on your path variable.

```
sudo apt-get install libssl-dev libbz2-dev libffi-dev libsqlite3-dev sqlite3 zlib1g-dev python3-pip # other dev packages may be required
wget --no-check-certificate  https://www.python.org/ftp/python/3.6.13/Python-3.6.13.tgz
tar xvzf Python-3.6.13.tgz 
cd Python-3.6.13
./configure --enable-optimizations --enable-loadable-sqlite-extensions
sudo make 
sudo make altinstall
```


## Setup file:
This is the contents of the setup python 3.6 file. Make sure that `~/.local/bin` is on your path variable.
Run these commands without the `sudo` or `--user` options.

```
python3.6 -m pip install virtualenv
python3.6 -m pip install virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
mkdir -p $WORKON_HOME
export VIRTUALENVWRAPPER_PYTHON=$(which python3.6)
source $(which virtualenvwrapper.sh)

mkvirtualenv chatbot36 --python $(which python3.6)
```

## Environment File For Testing
This is a version of the file called `.env` and the contents are below. These contents are especially important for testing using the input/output redirection.

```
AIML_DIR=../data/aiml-en-us-foundation-alice/
AIML_FILE=./bot.aiml
BATCH_SIZE=32
WORD_FACTOR=-1
MAX_LENGTH=32

## SRAI_LITERAL can be 0 or 1 ##

SRAI_LITERAL=1

## DOUBLE_COMPARE can be 2, 1, or 0 ##

# 2 == just do template comparison
# 1 == do double comparison, include weights
# 0 == just do pattern comparison

DOUBLE_COMPARE=0

## CUDA can be 0 or 1 ##

CUDA=1

## BERT_MODEL can be 0 or 1 ##

# 0 == bert-base-uncased
# 1 == bert-large-uncased

BERT_MODEL=0

WEIGHT_PATTERN=1.0

WEIGHT_TEMPLATE=0.5
```