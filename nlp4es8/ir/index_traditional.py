#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

sys.path.append('../')
sys.path.append('../utils')

import warnings

warnings.filterwarnings("ignore")

from ir.config import Config
from elasticsearch import helpers
import pandas as pd
from utils.args import FLAGS
# from utils.data_helper import Data
from utils.logger_config import base_logger


class Index(object):
    def __init__(self):
        base_logger.info("Indexing ...")

    @staticmethod
    def data_convert():
        base_logger.info("convert sql data into single doc")

        questions = {}
        embeddings = {}
        # 获取原始数据
        corpus = pd.read_csv('../data/corpus.tsv', sep='\t',header=None)
        print(corpus.head())
        # embedding 数据
        with open("../data/doc_embedding") as f:
            for line in f:
                sp_line = line.strip('\n').split("\t")
                index, embedding = sp_line
                embedding = embedding.split(',')
                embedding = [float(k) for k in embedding]
                embeddings[int(index)] = embedding

        # print(int(index))
        # print(embeddings[0])
        for key, value in corpus.iterrows():
            if not (value[1] or value[2].strip()):
                continue
            # print(value[0])
            questions[value[0]] = {'document': value[1], 'embedding': embeddings[value[0]]}

        return questions


    @staticmethod
    def create_index(config):
        base_logger.info("creating %s index ..." % config.index_name)
        request_body = {
            # 设置索引主分片数，每个主分片的副本数，默认分别是5和1
            "settings": {
                "number_of_shards": 5,
                "number_of_replicas": 1
            },
            "mappings": {

                "properties": {
                    "doc_id": {
                        "type": "long",
                        "index": "false"
                    },
                    "document": {
                        "type": "text",
                        "analyzer": "index_ansj",
                        "search_analyzer": "query_ansj",
                        "index": "true"
                    },
                    "embedding": {
                        "type": "array",
                        "index": "true"
                    },
                }
            }
        }

        try:
            # 若存在index，先删除index
            config.es.indices.delete(index=config.index_name, ignore=[400, 404])
            res = config.es.indices.create(index=config.index_name, body=request_body)

            base_logger.info(res)
            base_logger.info("Indices are created successfully")
        except Exception as e:
            base_logger.warning(e)


    @staticmethod
    def bulk_index(questions, bulk_size, config):
        base_logger.info("Bulk index for question")
        count = 1
        actions = []
        for question_index, question in questions.items():
            action = {
                "_index": config.index_name,
                "_id": question_index,
                "_source": question
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
            base_logger.info("Bulk index: %s" % str(count))


if __name__ == '__main__':
    config = Config(FLAGS.env)
    index = Index()
    index.create_index(config)
    questions = index.data_convert()
    print(questions[3])

    index.bulk_index(questions, bulk_size=10000, config=config)
