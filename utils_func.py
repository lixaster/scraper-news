import os
import yaml
import sys
import logging
import paho.mqtt.client as mqtt
import time


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    return logging


# 配置日志
logger = setup_logging()


def load_config(config_path="config/config.yaml"):
    if not os.path.exists(config_path):
        logger.error("配置文件不存在！程序退出！{config_path}")
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
            logger.warning("当前系统不支持更改文件所有者！")
    except Exception as e:
        logger.error(f"更改文件所有者失败: {e}")


def load_year_from_args():
    # 解析命令行参数
    args = sys.argv[1:]
    if len(args) > 0 and args[0].isdigit():
        logger.info(f"使用命令行参数指定的年份：{args[0]}")
        return int(args[0])
    else:
        logger.warning("未指定年份，使用默认值2025")
        return 2025


class MQTTClient:
    def __init__(self, host, port, username, password, client_id):
        """
        初始化 MQTT 客户端
        :param host: MQTT 服务器地址
        :param port: MQTT 服务器端口
        :param username: MQTT 用户名
        :param password: MQTT 密码
        :param client_id: 客户端ID，如果为None则自动生成
        """
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

        if username and password:
            self.client.username_pw_set(username, password)

        # 设置回调函数
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        # 连接状态
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc, properties):
        """连接回调函数"""
        if rc == 0:
            self.connected = True
            logger.info(f"已连接到 MQTT 服务器 {self.host}:{self.port}")
        else:
            self.connected = False
            logger.error(f"连接 MQTT 服务器失败，返回码：{rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties):
        """断开连接回调函数"""
        self.connected = False
        if rc != 0:
            logger.warning(f"与 MQTT 服务器断开连接，返回码：{rc}")
        else:
            logger.info("已断开与 MQTT 服务器的连接")

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        """发布消息回调函数"""
        logger.debug(f"消息已发布，消息ID：{mid}")

    def connect(self):
        """连接到 MQTT 服务器"""
        try:
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"连接 MQTT 服务器时发生错误：{e}")
            raise

    def disconnect(self):
        """断开与 MQTT 服务器的连接"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()

    def publish(self, topic, payload, qos=0, retain=False):
        """
        发布消息到指定主题
        :param topic: 主题
        :param payload: 消息内容
        :param qos: 服务质量等级 (0, 1, 2)
        :param retain: 是否保留消息
        :return: 消息ID
        """
        if not self.connected:
            self.connect()
            # 等待连接成功
            for _ in range(10):  # 最多等待10次
                if self.connected:
                    break
                time.sleep(0.5)
            if not self.connected:
                raise RuntimeError("无法连接到 MQTT 服务器")
            
        try:
            result = self.client.publish(topic, payload, qos, retain)
            result.wait_for_publish()
            if result.rc == 0:
                logger.info(f"{payload} 消息已发布到 {topic}")
            else:
                logger.error(f"{payload} 消息发布失败，返回码：{result.rc}")
            return result.mid
        except Exception as e:
            logger.error(f"发布消息时发生错误：{e}")
            raise

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


def mqtt_publish(topic="nas_cmd/execute", payload=""):
    """
    使用默认配置发布 MQTT 消息
    :param topic: 主题
    :param payload: 消息内容
    """
    config = load_config(config_path="config/secret.yaml")
    mqtt_config = config.get("mqtt", {})
    host = mqtt_config.get("host", "localhost")
    port = mqtt_config.get("port", 1883)
    username = mqtt_config.get("user", None)
    password = mqtt_config.get("pass", None)
    client_id = mqtt_config.get("client_id", None)
    with MQTTClient(host, port, username, password, client_id) as client:
        client.publish(topic, payload)


if __name__ == "__main__":
    print(load_config())
    # mqtt_publish(payload="test")
