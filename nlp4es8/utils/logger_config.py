import logging  # 引入logging模块
import os.path
import time
# 第一步，创建一个logger
base_logger = logging.getLogger()
base_logger.setLevel(logging.INFO)  # Log等级总开关
# 第二步，创建一个handler，用于写入日志文件
rq = time.strftime('%Y%m%d', time.localtime(time.time()))
log_path = os.path.dirname(os.getcwd()) + '/Logs/'

log_name = log_path + rq + '.log'
if not os.path.exists(log_path):
    os.mkdir(log_path)
logfile = log_name
fh = logging.FileHandler(logfile, )
fh.setLevel(logging.DEBUG)  # 输出到file的log等级的开关
# 第三步，定义handler的输出格式
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
# 第四步，将logger添加到handler里面
base_logger.addHandler(fh)
# 日志
if __name__ == '__main__':

    base_logger.debug('this is a logger debug message')
    base_logger.info('this is a logger info message')
    base_logger.warning('this is a logger warning message')
    base_logger.error('this is a logger error message')
    base_logger.critical('this is a logger critical message')