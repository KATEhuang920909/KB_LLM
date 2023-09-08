# -*- coding: utf-8 -*-
# @Time    : 2023/8/2 16:35
# @Author  : huangkai
# @File    : data_preprocess.py
from langchain.docstore.document import Document
import os
import json
from tqdm import tqdm
import numpy as np


# 将chunk片段映射到doucument index里面

class DataPreprocess():
    def __init__(self, maxlen):
        self.maxlen = maxlen

    def split_text(self, texts, d_idx, maxlength):
        texts = [Document(page_content=text["inside"][:maxlength],
                          metadata={"from": "doc_idx_" + str(d_idx) + "@text_idx" + str(i) + "@type" + text["type"]})
                 for i, text in
                 enumerate(texts)]
        return texts

    # def document_chunk_idx(self, dir_path):
    #     docs_bag = []
    #     files = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
    #     for i, file in tqdm(enumerate(files)):
    #         with open(file, encoding="utf8") as f:
    #             data = f.readlines()
    #             data = [json.loads(k.strip()) for k in data]
    #             docs = self.split_text(data, i, self.maxlen)
    #             docs_bag.append(docs)
    #     file_bag = [file.split(".")[0] for file in files]
    #     return docs_bag, dict(zip(file_bag, docs_bag)), dict(zip(np.arange(len(file_bag)), file_bag))
    def document_chunk_idx(self, questions, question_chunk):

        idx = question_chunk[0]
        typ = question_chunk[2]
        query = question_chunk[1]
        if typ == "excel":
            flag = 0
            for i in range(idx - 1, 0, -1):
                if questions[i]["type"] == typ:
                    query = questions[i]["document"] + "\n" + query
                else:
                    if (questions[i]["type"] in ["页脚", "页眉"]) or questions[i]["document"].strip() == "":
                        continue
                    else:
                        query = questions[i]["document"] + "\n" + query
                        flag += 1
                        if flag == 2:
                            break
            for i in range(idx + 1, len(questions)):
                if questions[i]["type"] == typ:
                    query = query + "\n" + questions[i]["document"]
                else:
                    if (questions[i]["type"] in ["页脚", "页眉"]) or questions[i]["document"].strip() == "":
                        continue
                    else:
                        break
        elif typ == "text":
            for i in range(idx - 1, 0, -1):
                if questions[i]["type"] == typ:
                    query = questions[i]["document"] + "\n" + query
                else:
                    if (questions[i]["type"] in ["页脚", "页眉"]) or questions[i]["document"].strip() == "":
                        continue
                    else:
                        break
            for i in range(idx + 1, len(questions)):
                if questions[i]["type"] == typ:
                    query = query + "\n" + questions[i]["document"]
                else:
                    if (questions[i]["type"] in ["页脚", "页眉"]) or questions[i]["document"].strip() == "":
                        continue
                    else:
                        break
        return query
