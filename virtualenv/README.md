## Virtual Environment

You need to install python3.7, or 3.6, or build it yourself before launching the virtual environment scripts. You might need `libffi-dev`.

Files in this folder:
* `do_make_virtualenv_setup36.sh` -- run once to add virtualenv to the installed packages... or simply `source` this file.

These files probably work best if run with `source`. Type `deactivate` to exit the virtualenv.

## Building Python3.7

This formula seems to work for Python3.6 also. Make sure that `~/.local/bin` is on your path variable.

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
This is the contents of the setup python 3.6 file. 
You may have to run these commands without the `sudo` or `--user` options.

```
sudo pip3 install --user virtualenv
sudo pip3 install --user virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
mkdir -p $WORKON_HOME
export VIRTUALENVWRAPPER_PYTHON=$(which python3.6)
source $(which virtualenvwrapper.sh)

mkvirtualenv chatbot36 --python $(which python3.6)
```