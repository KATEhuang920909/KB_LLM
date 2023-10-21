# -*- coding: utf-8 -*-
# @Time    : 2022/3/30 20:43
# @Author  : huangkai
# @File    : search_content.py


import sys

sys.path.append('../')
sys.path.append('../utils')

from es_config import Config


# from utils.logger_config import base_logger
# from utils.args import FLAGS
# from ir.index_hnsw import Index


class Search(object):
    def __init__(self, config, index_name):
        # base_logger.info("Searching ...")
        self.config = config
        self.es = self.config.es

        self.index_name = index_name

    def searchAnswer(self, question, ):
        body = {
            "query": {
                "multi_match": {
                    "query": question,
                    "fields": ["idx_document"],  # 在question字段中匹配查询
                    "type": "most_fields",
                }
            }
        }

        # es相关配置

        res = self.es.search(index=self.index_name, body=body, request_timeout=30, size=self.config.top_n)

        topn = res['hits']['hits']

        result = []
        for data in topn:
            result.append(
                (
                    data['_source']['index'],
                    data['_source']['idx_document'],
                    data['_source']['ori_document']
                )
            )
        return result

        # base_logger.info("ReadTimeOutError may not be covered!")


if __name__ == '__main__':
    import pandas as pd
    import json
    from tqdm import tqdm

    index_file_content_config = Config()
    index_file_content_config.index_name = "kbqa"
    index_file_content_config.top_n = 30
    search_name = Search(index_file_content_config, "kbqa")
    #
    predict_data = open(r"D:\compet\基于通用大模型的知识库问答\KB_LLM\result\qa/test_tuple_extract_qa.json",
                        encoding="utf8").readlines()
    submission = open(r"D:\compet\基于通用大模型的知识库问答\KB_LLM\result\qaes_llm_top20_test_quchong_qa.json", "w",
                      encoding="utf8")
    predict_data = eval("".join([k.strip() for k in predict_data]))
    print(predict_data[0])
    final_result = []

    for unit in tqdm(predict_data):
        query = "".join(unit["attribute"])
        result = search_name.searchAnswer(query)
        temp_final_result = [k[2] for k in result]
        unit["top30"] = temp_final_result
        final_result.append(unit)
    submission.write(json.dumps(final_result, ensure_ascii=False))

    # while True:
    #     query = input("please input")
    #     result = search_name.searchAnswer(query)
    #     # print(result[0])
    #     for data in result:
    #         print("question:%s  idx_document:%s ori_document:%s " % (data[0], data[1], data[2]))

    # train_data = [json.loads(k) for k in open("../../../data/train_sft.json", encoding="utf8")]
    # dev_data = [json.loads(k) for k in open("../../../data/dev_sft.json", encoding="utf8")]
    # train_submission = open("../../../data/train_sft_qa.json", "w", encoding="utf8")
    # dev_submission = open("../../../data/dev_sft_qa.json", "w", encoding="utf8")
    #
    #
    # train_final_result=[]
    # for unit in tqdm(train_data):
    #     query = ",".join(["".join([k.strip() for k in u.split("|||")[:2]]) for u in unit["answer"].split(";")])
    #     result = search_name.searchAnswer(query)
    #     temp_final_result = [k[2] for k in result]
    #     unit["top20"] = temp_final_result
    #     train_final_result.append(unit)
    # train_submission.write(json.dumps(train_final_result, ensure_ascii=False))
    #
    # dev_final_result = []
    # for unit in tqdm(dev_data):
    #     query = ",".join(["".join([k.strip() for k in u.split("|||")[:2]]) for u in unit["answer"].split(";")])
    #     result = search_name.searchAnswer(query)
    #     temp_final_result = [k[2] for k in result]
    #     unit["top20"] = temp_final_result
    #     dev_final_result.append(unit)
    # dev_submission.write(json.dumps(dev_final_result, ensure_ascii=False))

    # data = train_data=json.loads(open("../../../data/data_sft_top20.json",encoding="utf8").read())
    # data_submission = open("../../../data/data_sft_top20_v3.json", "w", encoding="utf8")
    # data_final_result = []
    # for unit in tqdm(data):
    #     query = ",".join(["".join([k.strip() for k in u.split("|||")[:2]]) for u in unit["attribute"]])
    #     result = search_name.searchAnswer(query)
    #     temp_final_result = [k[2] for k in result]
    #     unit["top20"] = temp_final_result
    #     data_final_result.append(unit)
    # data_submission.write(json.dumps(data_final_result, ensure_ascii=False))
