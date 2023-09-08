#!/usr/bin/env python
# -*- coding: utf-8 -*-



import sys
from elasticsearch import Elasticsearch
sys.path.append('../')
sys.path.append('../utils')
sys.path.append('../../')

from nlp4es8.ir.config import Config
# from utils.logger_config import base_logger


class Search(object):
    def __init__(self,config,index_name):
        # base_logger.info("Searching ...")
        self.config = config
        self.es = self.config.es

        self.index_name=index_name
    def searchAnswer(self, question):

        body = {
            "query": {
                "multi_match": {
                    "query": question,
                    "fields": ["document"],  # 在question字段中匹配查询
                    "type": "most_fields",
                }
            }
        }

        # es相关配置


        res = self.es.search(index=self.index_name, body=body)

        topn = res['hits']['hits']
        print("topn",topn)
        result = []
        for data in topn:

            result.append(
                (
                    data['_source']['document'],
                    data['_source']['idx']
                )
            )
        return result



if __name__ == '__main__':
    index_file_name_config = Config()
    # index_file_name_config.index_name = "filename"
    search_name = Search(index_file_name_config,"filename")

    while True:
        query = input("please input")
        result = search_name.searchAnswer(query)
        for data in result:
            print("question:%s  question_id:%s  " % (data[0], data[1]))
    # index_file_content_config = Config()
    # index_file_content_config.index_name = "中电电机2020年年度报告"
    # search_name = Search(index_file_content_config)
    # while True:
    #     query = input("please input")
    #     result = search_name.searchAnswer(query)
    #     for data in result:
    #         print("question:%s  question_id:%s  " % (data[0], data[1]))
