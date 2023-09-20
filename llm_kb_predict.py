#!/usr/bin/env python
# -*- coding:utf-8 _*-
"""
"""
import pandas as pd
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from llm_predict import LLM_PREDICTOR
from data_preprocess import DataPreprocess
from config import maxlen, topk, PROMPT_TEMPLATE, threshold, dir_path, embedding_path, feature_extract_prompt, \
    excel_prefix_prompt, text_prefix_prompt, llm_path
from ir.search_file_name import Search
from ir.search_content import Search as SearchContent
from ir.es_config import Config
from ir.es_update import Es_Update

"""
1.抽取关键词，依据关键词检索文档；
2.将相关文档存储为向量形式；
3.依据QUERY检索固定的向量
4.将固定向量相邻的文本类型串起来，同时作为prompt的一部分；
5.chatglm2问答
"""


# 中文Wikipedia数据导入示例：
class LLM_KB():
    def __init__(self, embedding_path):  # , llm_path):
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_path,
                                                model_kwargs={'device': "cpu"},
                                                encode_kwargs={'normalize_embeddings': True})
        # self.llm_predictor = LLM_PREDICTOR(llm_path)
        # print(self.embeddings.embed_query("你试试额"))
        self.es_update = Es_Update("filename")
        self.config = Config()
        self.search_name = Search(self.config, "filename")
        self.dp = DataPreprocess(maxlen=maxlen)

    def vector_store(self, files, vs_path, ):
        vector_store = FAISS.from_documents(files, self.embeddings)
        vector_store.save_local(vs_path)

    def vector_retrieval(self, query, vs_path):
        vector_store = FAISS.load_local(vs_path, self.embeddings)
        related_docs_with_score = vector_store.similarity_search_with_score(query, k=topk)

        return related_docs_with_score

    def get_history_text(self, doc_chunk, doc_bag):
        final_text = doc_chunk[0]["page_content"]
        metadata = doc_chunk[0].metadata
        type = metadata.split("@type")[-1]
        idx = int(metadata.split("@id")[1].split("@type")[0])
        while doc_bag[idx - 1][0].metadata.split("@type")[-1] == type:
            pre_txt = doc_bag[idx - 1][0]["page_content"]
            final_text = pre_txt + final_text
            idx -= 1
        idx = int(metadata.split("@id")[1].split("@type")[0])
        while doc_bag[idx + 1][0].metadata.split("@type")[-1] == type:
            post_txt = doc_bag[idx - 1][0]["page_content"]
            final_text += post_txt
            idx += 1
        return final_text, type

    def generate_prompt(self, related_doc, TYPE, query: str, prompt_template: str = PROMPT_TEMPLATE,
                        preprompt="") -> str:
        if TYPE == "excel":
            preprompt = "根据以下表格信息："
        elif TYPE == "text":
            preprompt = "根据以下文本信息："

        prompt = preprompt + prompt_template.replace("{question}", query).replace("{context}", related_doc)
        return prompt

    def llm_feature_extract(self, query, prompt_template=feature_extract_prompt):
        response, history = self.llm_predictor.predict(prompt_template + query)
        response = response.split("\n")
        name = response[0].split("：")[-1]
        time = response[1].split("：")[-1]
        return name, time

    def llm_chat(self, prompt):
        response, history = self.llm_predictor.predict(prompt)

        return response

    def es_result(self, key_word, query):
        final_result = [query]
        temp_query1 = key_word.replace("公司名称：", "_").replace("日期：", "_").replace(" ", "")
        query1 = []
        for unit in temp_query1.split("_"):
            if unit:
                query1.append(unit)
        query1 = "".join(query1)
        for unit in query1:
            query = query.replace(unit, "")
        # print("query1", query1, query)
        # 找到对应的文件
        if query1:
            time.sleep(1)
            result = self.search_name.searchAnswer(query1)[0][0]
            print(self.es_update.file_name_idx[result], result)
            # 对应的文件写入es
            # result = "锦江酒店2019年年度报告"
            questions = self.es_update.update_content(self.es_update.file_name_idx[result], result)

            # query检索
            search_content = SearchContent(self.config, index_name=result)
            print("query",query)
            result2 = search_content.searchAnswer(query)
            flag = 0
            for unit in result2:
                if unit[2] in ["excel", "text"]:

                    chunk_info = self.dp.document_chunk_idx(questions, unit)
                    if unit[2] == "excel":
                        prompt = excel_prefix_prompt + \
                                 PROMPT_TEMPLATE.replace("{question}", query).replace("{context}", chunk_info)
                    elif unit[2] == "text":
                        prompt = text_prefix_prompt + \
                                 PROMPT_TEMPLATE.replace("{question}", query).replace("{context}", chunk_info)
                    flag += 1
                    print(prompt + "\n")
                    # response = self.llm_chat(prompt)
                    final_result.append(prompt)
                if flag == 2:
                    break
        else:
            prompt = query
            final_result.append(prompt)
        return final_result


if __name__ == '__main__':
    import json

    # 找出关键词：
    # key_word = []
    llm_chain = LLM_KB(embedding_path=embedding_path)  # , llm_path=llm_path)
    #
    # # print(llm_chain.es_result("的法定代表人是谁？"))
    # with open("test_questions.json", encoding="utf8") as f:
    #     data = f.readlines()
    #     data = [json.loads(k.strip()) for k in data]
    # submit = open(r"result/submit_0809.json","w",encoding="utf8")
    # for unit in data:
    #     result = llm_chain.llm_feature_extract(unit["question"])
    #     unit["key_word"] = result
    #     submit.write(json.dumps(unit, ensure_ascii=False) + "\n")

    # 基于关键词和原句子进行索引：
    import time

    with open("keyword/submit_0809.json", encoding="utf8") as f:
        data = f.readlines()
        data = [json.loads(k.strip()) for k in data]
    while True :
        num=input("input num ")
        kw = data[int(num)]["key_word"]
        query1 = data[int(num)]["question"]
        print("query1", query1)
        # time.sleep(1)
        result = llm_chain.es_result(kw, query1)
        print(result)
    # print(llm_chain.es_result(kw, query))
    # while True:
    #     query1 = input("请输出")
    #     result = llm_chain.search_name.searchAnswer(query1)[0][0]
    #     print(result)
