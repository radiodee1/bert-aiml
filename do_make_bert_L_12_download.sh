#!/usr/bin/env bash

export NAME_BERT=uncased_L-12_H-768_A-12

mkdir -p data

cd data
mkdir -p ${NAME_BERT}
cd ${NAME_BERT}
#touch file
#echo ${NAME_BERT} not working
wget https://storage.googleapis.com/bert_models/2020_02_20/${NAME_BERT}.zip

unzip ${NAME_BERT}.zip

#https://storage.googleapis.com/cloud-tpu-checkpoints/bert/keras_bert/wwm_uncased_L-24_H-1024_A-16.tar.gz ## keras
#https://tfhub.dev/tensorflow/bert_en_wwm_uncased_L-24_H-1024_A-16/ ## tf hub
