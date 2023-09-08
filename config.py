# -*- coding: utf-8 -*-
# @Time    : 2023/8/3 9:53
# @Author  : huangkai
# @File    : config.py
maxlen = 500
topk = 5
threshold = 0.7
embedding_path = r"D:\代码\pretrained_model\bert-base-chinese"
dir_path = "D:\代码\SMP 2023 ChatGLM金融大模型挑战赛\sample\documents"
llm_path = "chatglm2-int4"
# 基于上下文的prompt模版，请务必保留"{question}"和"{context}"
PROMPT_TEMPLATE = """{context} 

 请问：{question} 请用简洁和专业的来回答以上问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题” ，不允许在答案中添加编造成分，答案请使用中文。"""

feature_extract_prompt = "请抽取下面句子的公司名称和日期，不允许在答案中添加编造成分，格式为“公司名称：\n 日期：”：“{context}”"

excel_prefix_prompt = "根据以下表格信息："
text_prefix_prompt = "根据以下文本信息："
