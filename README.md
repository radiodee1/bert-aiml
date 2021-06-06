# bert-aiml

The general purpose of this repository is to use BERT and AIML together. Possibly this would allow for the continued use of aiml files in a circumstance where machine learning is most prevalent and proves to be the best tool.

# env
The `.env` file should look like this:

```
AIML_DIR=../data/aiml-en-us-foundation-alice/
BATCH_SIZE=32
WORD_FACTOR=-1
MAX_LENGTH=96

## DOUBLE_COMPARE can be 2, 1, or 0 ##

# 2 == just do template comparison
# 1 == do double comparison
# 0 == just do pattern comparison

DOUBLE_COMPARE=1

## CUDA can be 0 or 1 ##

CUDA=1

## BERT_MODEL can be 0 or 1

# 0 == bert-base-uncased
# 1 == bert-large-uncased

BERT_MODEL=0
```

It should go in the `src` folder.

Using CUDA, the BATCH_SIZE was 32. This worked fast on a modest gpu. Without the gpu the BATCH_SIZE can be higher. This ends up being slower.