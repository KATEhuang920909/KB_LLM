#!/usr/bin/env python
# -*- coding:utf-8 _*-
"""
"""
from es_config import Config

"""
1.将知识点入库
2.es 检索
"""
from search_content import Search

import json

index_file_content_config = Config()
index_file_content_config.index_name = "kbqa"
search_name = Search(index_file_content_config, "kbqa")
# while True:
#     query = input("please input")
#     result = search_name.searchAnswer(query)
#     print(result[0])
#     for data in result:
#         print("question:%s  question_id:%s  " % (data[0], data[1]))
predict_data = json.loads(open("result/es_baseline.json", encoding="utf8").read())
# predict_data = open("../../data/提交示例.json", encoding="utf8").readlines()
# print(predict_data[2])
# exit()
submission = open("result/es_top20.json", "w", encoding="utf8")
print(predict_data[0])
# exit()
# predict_data = [json.load(k) for k in predict_data]#[:100]
final_result = []
from tqdm import tqdm

for unit in tqdm(predict_data[:-13]):
    query = unit["question"]
    result = search_name.searchAnswer(query)
    temp_final_result = result
    unit["attribute"] = temp_final_result
    final_result.append(unit)
final_result += predict_data[-13:]
submission.write(json.dumps(final_result, ensure_ascii=False))
print(len(submission),len(predict_data))
print(final_result[0])
