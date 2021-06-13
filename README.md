# bert-aiml

This is a poorly worded list of reasons for using or working on this project. Ubuntu 21.04 is the development environment.

* The general purpose of this repository is to use BERT and AIML together. 

* Possibly this would allow for the continued use of aiml files in a circumstance where they are considered old or inflexible. 

* Machine learning is most prevalent and proves to be the best tool but aiml files are defined and easily available.

* No training should be done to make this project work.

* The `./src/aiml_consume.py` implements a simple version of aiml 1.0. This file is meant to work on python 3.6. See the `virtualenv` folder for details on installing the python language. This file uses bert to decide which response from the aiml files to use.

* The `./src/aiml_run_example.py` file is used for comparrison, and does not employ bert. It uses the `python-aiml` library.

* Aiml wildcards have been greatly simplified. See below.

# `.env`
The `.env` file should look like this:

```
AIML_DIR=../data/aiml-en-us-foundation-alice/
AIML_FILE=${HOME}/workspace/bert-aiml/src/../aiml/maze.xml
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

It should go in the `src` folder.

Using CUDA, and 'bert-base-uncased', the BATCH_SIZE was 32. This worked fast on a modest gpu. Without the gpu the BATCH_SIZE can be higher. This ends up being slower.


# aiml wildcards

Aiml wildcards are represented by an asterisk. They work, but are limited to the first or last single word in the sentence in question. This is because the number of words in a sentence could possibly not match the number of words in the `pattern` tag.