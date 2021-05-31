# bert-aiml

The `.env` file should look like this:

```
AIML_DIR=../data/aiml-en-us-foundation-alice/
BATCH_SIZE=128
WORD_FACTOR=-1
MAX_LENGTH=96

## DOUBLE_COMPARE can be 2, 1, or 0

# 2 == just do template comparison
# 1 == do double comparison
# 0 == just do pattern comparison

DOUBLE_COMPARE=2
```

It should go in the `src` folder.