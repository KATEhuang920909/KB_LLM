# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     test_LLM
   Author :       huangkai
   date：          2023/9/23
-------------------------------------------------
"""

# from modeling_chatglm import ChatGLMModel
# from tokenization_chatglm import ChatGLMTokenizer

from transformers import AutoModel,AutoTokenizer
class LLM_PREDICTOR():
    def __init__(self, path):
        self.tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        model = AutoModel.from_pretrained(path, trust_remote_code=True).float()
        self.model = model.eval()

    def predict(self, text):
        response, history = self.model.chat(self.tokenizer, text, history=[])
        print(response)


if __name__ == "__main__":
    path = r"D:\code\pretrained_model\chatglm2"
    predictor = LLM_PREDICTOR(path=path)
    while True:
        predictor.predict("经常失眠怎么办？")
