#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ""
__author__ = "yangzl31"
__mtime__ = "2020/05/28"
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""

# 数据预处理

import os
import sys

sys.path.append("../")
sys.path.append("../utils")

import warnings

warnings.filterwarnings("ignore")
import base64
import configparser

import jieba
import jieba.analyse as analyse
# import pymysql
import re
# import emoji
import pandas as pd
import numpy as np
# from bert_serving.client import BertClient
# from utils.args import FLAGS
from utils.logger_config import base_logger

# path setting
curdir = os.path.dirname(os.path.abspath(__file__))
predir = os.path.abspath(os.path.dirname(os.getcwd()))
sys.path.insert(0, os.path.dirname(curdir))

base_logger.info("载入用户词典和停用词")

# 载入用户词典
jieba.load_userdict(FLAGS.user_dict_path)

# 获取停用词
stopwords = [line.strip() for line in open(FLAGS.stopwords_path, "r", encoding="utf-8").readlines()]


# 读取option内容
def get_option_values(option):
    """
    根据传入的section获取对应的value
    :param section: ini配置文件中用[]标识的内容
    :return:
    """

    config = configparser.ConfigParser()
    config.read(FLAGS.config_file)

    option_list = config.options(option)

    return option_list


# 读取配置文件
def get_config_values(section, option):
    """
    根据传入的section获取对应的value
    :param section: ini配置文件中用[]标识的内容
    :return:
    """

    config = configparser.ConfigParser()
    config.read(FLAGS.config_file)

    result = config.get(section=section, option=option)

    return result


# 解码
def safe_b64decode(str):
    length = len(str) % 4

    for i in range(length):
        str = str + "="

    result = base64.b64decode(str)
    result = result.decode()

    return result


# 数据预处理
class DataProcessors(object):

    def __init__(self):
        pass

    # 检测是否包含有标点符号
    def isPunctuation(self, uchar):
        if uchar >= u"\u4e00" and uchar <= u"\u9fa5":  # 汉字
            return False
        if uchar >= u"\u0030" and uchar <= u"\u0039":  # 数字
            return False
        if (uchar >= u"\u0041" and uchar <= u"\u005a") or (uchar >= u"\u0061" and uchar <= u"\u007a"):  # 英文
            return False

        return True

    # def clean_func(self, x):
    #     x = x.strip()
    #     s = re.sub(self.begin_pat, "", x)
    #     s = re.sub(self.end_pat, "", s)
    #     if len(s) == 0:
    #         return x
    #     else:
    #         return s

    # 检测是否为纯标点符号
    def isAllPunctuation(self, sentence):
        for char in sentence:
            if not self.isPunctuation(char):
                return False
        return True

    def text_clean(self, df):

        base_logger.info("导入数据,共%s个,数据清洗执行中......" % df.shape[0])

        # 去除包含空字符串数据
        NONE_Que = (df["question"].isnull()) | (df["question"].apply(lambda x: str(x).isspace()))
        df = df[~NONE_Que]

        # 去除空白字符数据（包含两边空格、制表符、换页符等）
        df["question"] = df["question"].apply(lambda x: x.strip())
        df["question"] = df["question"].apply(lambda x: x.replace("\n", "").replace("\r", ""))

        # 过滤筛选只包含数字的数据
        cond_digit = df["question"].apply(lambda x: x.isdigit())
        df = df[~cond_digit]

        # 过滤只包含标点符号的数据
        cond_punction = df["question"].apply(lambda x: self.isAllPunctuation(x))
        df = df[~cond_punction]

        # 过滤只包含问候类、语气词数据
        hello_pattern = re.compile(r"^(转|有|找)?人工(客服|坐席)?.{1,3}$")
        cond_hello_pattern = df["question"].str.contains(hello_pattern)
        df = df[~cond_hello_pattern]

        # 过滤包含带有脱敏字符的数据
        special_pattern = re.compile(r"(\[.*\])|(\%\%.*\&\&)")
        df["question"] = df["question"].apply(lambda x: re.sub(special_pattern, "", x))

        # 去除表情符号
        df["question"] = df["question"].apply(lambda x: re.sub(":\S+?:", "", emoji.demojize(x)))

        # 去除超链接部分数据
        url_pattern = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        df["question"] = df["question"].apply(lambda x: re.sub(url_pattern, "", x))

        # 去除系统自动回复
        df = df[df["question"].apply(lambda x: True if "【" not in x else False)]

        # 去除空白数据、将替换后NA数据清除
        df.replace(to_replace=r"^\s*$", value=np.nan, regex=True, inplace=True)
        df = df.dropna(axis=0).reset_index(drop=True)

        # 选取字符长度在4~30之间的数据
        df["question_len"] = df["question"].apply(lambda x: len(x))
        df = df[(df.question_len >= 4) & (df.question_len <= 30)]
        df.drop(["question_len"], axis=1, inplace=True)

        base_logger.info("清洗完毕后，数据包含：%s" % len(df))

        return df

    # 分词，剔除无意义词语
    def seg_sentence(self, sentences):

        sentence_seged = jieba.lcut(sentences)

        # load stopwords
        outstr = []
        for word in sentence_seged:
            if word not in stopwords:
                if word != "\t":
                    outstr.append(word)

        return outstr

    # 将每个类别的所有wordlist合并一起
    def merge_words(self, x):
        res = []
        for item in x:
            res.extend(item)
        return res

    # 获取各个类别的关键词
    def get_hot_word(self, words, contexts):
        counts = {}

        # 计算词频
        for word in words:
            counts[word] = counts.get(word, 0) + 1

        # 计算关键词
        textrank = analyse.textrank
        keywords = list(set(textrank(contexts, allowPOS=("nr", "nr1", "nr2", "ns", "n", "vn", "v"), topK=3)))

        # 查找关键词的词频
        results = {}
        for key, value in counts.items():
            if key in keywords:
                results[key] = value

        # 将词频排序
        # results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        return results


# 获取特征向量
class GetFeatures(object):
    def __init__(self):
        # 读取配置文件
        env_list = get_option_values("gpu_server")
        if FLAGS.env not in env_list:
            raise Exception("请输入正确的环境（int/test/prd中的一种）")
        # 获取host地址
        self.host = get_config_values("gpu_server", FLAGS.env)
        self.port = get_config_values("gpu_server", "port")
        self.port_out = get_config_values("gpu_server", "port_out")
        base_logger.info("connect gpu server in: %s" % (self.host))

    # 使用bert提取句向量矩阵
    def get_bert_matrix(self, bert_corpus):

        try:
            bc = BertClient(ip=self.host, port=int(self.port), port_out=int(self.port_out))
            bert_matrix = bc.encode(bert_corpus)
            return bert_matrix
        except Exception as e:
            base_logger.info("Fail to get bert-embedding!! The reason is：%s" % e)


# 数据库操作
# class Data(object):
#     def __init__(self, env):
#
#         # 读取配置文件
#         env_list = get_option_values("mysql_server")
#         if env not in env_list:
#             raise Exception("请输入正确的环境（int/test/prd中的一种）")
#
#         # 获取host地址
#         host = get_config_values("mysql_server", env)
#         base_logger.info("connect mysql server in: %s" % (host))
#
#         # 获取端口
#         port = get_config_values("mysql_database", "port")
#
#         # 获取用户名
#         user = get_config_values("mysql_database", "user")
#
#         # 获取密码
#         passwd_sec = get_config_values("mysql_database", "passwd")
#         passwd = safe_b64decode(passwd_sec)
#
#         # 获取编码
#         charset = get_config_values("mysql_database", "charset")
#
#         db = "tkrobotkdb"
#
#         # self.conn = pymysql.connect(
#         #     host=host,
#         #     port=int(port),
#         #     user=user,
#         #     passwd=passwd,
#         #     db=db,
#         #     charset=charset
#         # )
#
#     # 从数据库获取处理工作池数据
#     def read_data(self, original, start_time, end_time):
#         base_logger.info("==========================处理工作池数据读取开始========================")
#         base_logger.info("查询处理工作池数据......")
#         base_logger.info("查询的产品为：%s" % (original))
#
#         # 查询数据sql
#         sql1 = "select item_id AS question_id, sub_question AS question," \
#                "ai_question_id from workflow_sub_extension where " \
#                "original = %s  and create_time >= %s  and create_time < %s;"
#
#         # 获取连接、光标
#         conn = self.conn
#         cursor = conn.cursor()
#
#         # 查询数据库
#         try:
#             # 检查是否断开, 断开重连
#             conn.ping(reconnect=True)
#
#             cursor.execute(sql1, (original, start_time, end_time))
#             data_all = cursor.fetchall()
#
#             base_logger.info("事务处理成功: 共处理数据：%s" % cursor.rowcount)
#
#             # 保存查询后的数据
#             result = pd.DataFrame(list(data_all), columns=[x[0] for x in cursor.description])
#
#             base_logger.info("==========================处理工作池数据读取完毕========================")
#
#             return result
#         except Exception as e:
#             base_logger.error("事务处理失败，事务回滚！失败原因：%s" % e)
#             base_logger.info("==========================处理工作池数据读取完毕========================")
#         finally:
#             # 关闭游标、事务
#             cursor.close()
#             conn.close()
#
#     # 从数据库获取全量问题
#     def read_all_Question(self):
#         base_logger.info("==========================全量问题数据读取中========================")
#         base_logger.info("查询问题库中所有问题......")
#
#         # 查询数据sql（包含所有子问题）
#         sql = """select
#                 s.id as question_id, s.faq_question_id as primary_question_id, s.sub_question as question
#             FROM  `faq_sub_question` s ,faq_question q
#             WHERE s.`faq_question_id`=q.`id`
#             AND q.deleted = 0 AND q.disabled = 0
#             AND s.deleted =0 AND s.disabled = 0
#
#             UNION ALL
#
#             select
#                 q.id as question_id, q.id as primary_question_id, faq_question as question
#             FROM  faq_question q
#             WHERE q.deleted = 0 AND q.disabled = 0
#
#             """
#
#         # 获取光标
#         # 获取连接、光标
#         conn = self.conn
#         cursor = conn.cursor()
#
#         # 查询数据库
#         try:
#             # 检查是否断开, 断开重连
#             conn.ping(reconnect=True)
#
#             cursor.execute(sql)
#             dataAll = cursor.fetchall()
#
#             base_logger.info("共提取全量数据：%s" % cursor.rowcount)
#
#             # 保存查询后的数据
#             colnames = ["sub_question_id", "primary_question_id", "question"]
#             result = pd.DataFrame(list(dataAll), columns=colnames)
#
#             # 每次打乱数据，确保数据是随机的
#
#             base_logger.info("==========================全量问题数据读取完毕========================")
#
#             return result
#         except Exception as e:
#             base_logger.error("事务处理失败，事务回滚！失败原因：%s" % e)
#             base_logger.info("==========================全量问题数据读取完毕========================")
#         finally:
#             # 关闭游标、事务
#             cursor.close()
#             conn.close()


if __name__ == "__main__":
    # A = "请问，一年共交多少保费？"
    # B = "保费是多少？"

    original = "gwkhys"
    ai_question_id = 8
    start_time = "2020-01-01 00:00:00"
    end_time = "2020-12-30 00:00:00"

    # 获取数据
    data = Data(FLAGS.env)
    dp = DataProcessors()
    dp.seg_sentence()
    # df1 = data.read_all_Question()
    # print(df1.head())
    # 获取数据
    # data = Data(FLAGS.env)
    # sn = "cluster_32"
    # original = "weibao"
    # start_time = "2020-06-01 00:00:00"
    # end_time = "2020-06-05 00:00:00"
    #
    # df = data.read_data(original, start_time, end_time)
    # print(df.head())
    # print(df.dtypes)
    gf = GetFeatures()
    while True:
        query = input("input:\n").split(" ")
        result = gf.get_bert_matrix(query)
        print("result: ", result)
