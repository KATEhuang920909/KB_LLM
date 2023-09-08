# -*- coding: utf-8 -*-
# @Time    : 2023/7/30 20:27
# @Author  : huangkai
# @File    : llm_predict.py

# LLM生成式问答

from transformers import AutoTokenizer, AutoModel


class LLM_PREDICTOR():
    def __init__(self, path):
        self.tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        model = AutoModel.from_pretrained(path, trust_remote_code=True).float()
        self.model = model.eval()

    def predict(self, text):
        response, history = self.model.chat(self.tokenizer, text, history=[])
        print(response)


if __name__ == "__main__":
    path = ""
    predictor = LLM_PREDICTOR(path=path)
    import json

    test_questions = open("test_questions.json", encoding="utf8").readlines()
    llm_result = open("小胡椒_result.json", "w", encoding="utf8")

    result_all = []
    for test_question in test_questions:
        questions = json.loads(test_question)
        result = predictor.predict("下面问题只需要回答不做解释：" + questions["question"])
        questions["answer"] = result
        llm_result.write(json.dumps(questions, ensure_ascii=False) + "\n")
