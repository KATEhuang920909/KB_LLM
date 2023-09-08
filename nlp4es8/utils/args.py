#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import tensorflow as tf

# path setting
curdir = os.path.dirname(os.path.abspath(__file__))
predir = os.path.abspath(os.path.dirname(os.getcwd()))
sys.path.insert(0, os.path.dirname(curdir))
# basic path
flags = tf.compat.v1.flags
FLAGS = flags.FLAGS
## Required parameters
####### basic flags #########
flags.DEFINE_string(
    "config_file",
    predir + '/data/dict/config.ini',
    help="The path of all config file."
)
flags.DEFINE_string(
    "label_path",
    predir + '/data/labels.json',
    'basic label json file'
)

flags.DEFINE_string(
    "user_dict_path",
    predir + '/data/dict/userdict.txt',
    'user_dict path for jieba segment'
)

flags.DEFINE_string(
    "stopwords_path",
    predir + '/data/dict/stopwords.txt',
    'stopwords path for jieba segment'
)

flags.DEFINE_string(
    "saved_model_path",
    predir + '/classfier/saved_model/',
    'basic label json file'
)

flags.DEFINE_string(
    "filter_model_path",
    predir + '/utils/filter_models/filter_model.pkl',
    'filter model path for filtering'
)
flags.DEFINE_string(
    "env",
    "test",
    'config excute enviroment address, such as dev、int、test or product'
)



flags.DEFINE_integer(
    "cluster_length",
    50,
    'basic cluster length, if the length less than 50, please do directly'
)

flags.DEFINE_integer(
    "kmeans_cluster_num",
    10,
    'basic cluster num, if the length less than 50, please do directly'
)

flags.DEFINE_integer(
    "kmeans_cluster_batch_size",
    45,
    'the num of minibatch-kmeans batch size'
)

flags.DEFINE_float(
    "singlepass_thres",
    0.7,
    'this is the threshold of signlepass cluster algorithm'
)


