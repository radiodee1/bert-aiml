import torch
model = torch.hub.load('huggingface/pytorch-transformers', 'modelForSequenceClassification', 'bert-base-uncased')    # Download model and configuration from S3 and cache.
#model = torch.hub.load('huggingface/pytorch-transformers', 'modelForSequenceClassification', './test/bert_model/')  # E.g. model was saved using `save_pretrained('./test/saved_model/')`
#model = torch.hub.load('huggingface/pytorch-transformers', 'modelForSequenceClassification', 'bert-base-uncased', output_attention=True)  # Update configuration during loading
#assert model.config.output_attention == True

# Loading from a TF checkpoint file instead of a PyTorch model (slower)
#config = AutoConfig.from_json_file('./tf_model/bert_tf_model_config.json')
#model = torch.hub.load('huggingface/pytorch-transformers', 'modelForSequenceClassification', './tf_model/bert_tf_checkpoint.ckpt.index', from_tf=True, config=config)

#https://pytorch.org/hub/huggingface_pytorch-transformers/

#https://huggingface.co/transformers/model_doc/bert.html

print(model.config)