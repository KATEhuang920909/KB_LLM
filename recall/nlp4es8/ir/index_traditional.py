#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

sys.path.append('../')
sys.path.append('../utils')

import warnings

warnings.filterwarnings("ignore")

from ir.es_config import Config
from elasticsearch import helpers
import pandas as pd
from utils.args import FLAGS
# from utils.data_helper import Data
from utils.logger_config import base_logger


class Index(object):
    def __init__(self, index_name):
        base_logger.info("Indexing ...")
        self.index_name = index_name

    @staticmethod
    def data_convert_v3(file):
        question = {}
        with open(file, encoding="utf8") as f:
            docs = f.readlines()

        for contents in docs:
            idx, content = contents.strip().split("\t")
            question[idx] = {'index': idx,
                             'idx_document': "".join([k.strip() for k in content.split("|||")[:2]]),
                             'ori_document': content}
        return question

    def create_index(self, config):
        base_logger.info("creating %s index ..." % self.index_name)
        request_body = {
            # 设置索引主分片数，每个主分片的副本数，默认分别是5和1
            "settings": {
                "number_of_shards": 5,
                "number_of_replicas": 1
            },
            "mappings": {

                "properties": {
                    "index": {
                        "type": "long",
                        "index": "false"},
                    "idx_document": {
                        "type": "text",
                        # "analyzer": "index_ansj",
                        # "search_analyzer": "query_ansj",
                        "index": "true"
                    },
                    "ori_document": {
                        "type": "text",
                        # "analyzer": "index_ansj",
                        # "search_analyzer": "query_ansj",
                        "index": "true"
                    }
                }
            }
        }

        # print(config.index_name)
        # 若存在index，先删除index
        if config.es.indices.exists(index=self.index_name):
            print(f'{self.index_name}索引存在')
            return "索引存在"
        else:
            res = config.es.indices.create(index=self.index_name, body=request_body)
            # base_logger.info(res)
            print("Indices are created successfully")
            return "创建成功"

    # @staticmethod
    def bulk_index(self, questions, bulk_size, config):
        # base_logger.info("Bulk index for question")
        count = 1
        actions = []
        # print("questions:",questions)
        for index, values in questions.items():
            if count == 100:
                print(values)
            action = {
                "_index": self.index_name,
                "_id": index,
                "_source": values
            }
            actions.append(action)
            count += 1
            if count % 10000 == 0:
                print(count)
            if len(actions) % bulk_size == 0:
                helpers.bulk(config.es, actions)
                actions = []

        if len(actions) > 0:
            helpers.bulk(config.es, actions)
            print("Bulk index: %s" % str(count))


if __name__ == '__main__':
    config = Config()
    index = Index("kbqa")
    index.create_index(config)
    for i in range(9):
        questions = index.data_convert_v3(f"../../../data/kbqa{i}.txt")
        index.bulk_index(questions, bulk_size=10000, config=config)
