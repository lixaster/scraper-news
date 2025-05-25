import os
import yaml
import sys
import logging
import paho.mqtt.client as mqtt

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    return logging


# 配置日志
logging = setup_logging()

# 配置文件路径
CONFIG_PATH = "config/config.yaml"


def load_config(config_path=CONFIG_PATH):
    if not os.path.exists(config_path):
        logging.error("配置文件不存在！程序退出！")
        logging.error(f"配置文件路径：{CONFIG_PATH}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# 定义一个函数，用于拼接路径
def path_join(*args):
    # 使用os.path.join把路径拼接起来，并把路径中的反斜杠替换成斜杠
    return os.path.join(*args).replace("\\", "/")


def mkdirs_with_owner(folder_path, owner_uid=1027, owner_gid=100):
    # 创建目录，并设置目录的拥有者
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        # 更改文件所有者
        change_file_owner(folder_path, owner_uid, owner_gid)


def change_file_owner(path, owner_uid=1027, owner_gid=100):
    # 更改文件所有者，仅在Linux系统下有效
    try:
        chown = getattr(os, "chown", None)
        if chown:
            chown(path, owner_uid, owner_gid)
        else:
            logging.warning("当前系统不支持更改文件所有者！")
    except Exception as e:
        logging.error(f"更改文件所有者失败: {e}")


def load_year_from_args():
    # 解析命令行参数
    args = sys.argv[1:]
    if len(args) > 0 and args[0].isdigit():
        logging.info(f"使用命令行参数指定的年份：{args[0]}")
        return int(args[0])
    else:
        logging.warning("未指定年份，使用默认值2025")
        return 2025


if __name__ == "__main__":
    print(load_config())
