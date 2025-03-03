# 使用 synology_drive_api 库，实现在 Synology NAS 上移动加星文件到指定文件夹
# 依赖库：pip install synology_drive_api
# 参考文档：https://github.com/zbjdonald/synology-drive-api

# 参考函数：TEST_FOLDER = "/mydrive/新闻文档爬取与合并/hubeigov"
# 1、上传：
# with open('record.json', 'rb') as file:
#    ret_upload = synd.upload_file(file, dest_folder_path=TEST_FOLDER)
# 2、重命名：
# 'TEST_FOLDER/record.json' to 'TEST_FOLDER/api_create_folder/record.json'
# # synd.rename_path(f'record2.json', f'{TEST_FOLDER}/record.json')
# 3、移动：
# origin_path = f"{TEST_FOLDER}/record.json"
# dest_folder = f"{TEST_FOLDER}/api_create_folder"
# synd.move_path(origin_path, dest_folder)
# 4、创建文件夹：
# synd.create_folder('api_create_folder', TEST_FOLDER)

from synology_drive_api.drive import SynologyDrive
import os
from utils_func import load_config, path_join, setup_logging

# 配置日志
logging = setup_logging()

# 读取 yaml 文件，获取配置信息
config_nas = load_config("config/secret.yaml")
NAS_USER = config_nas.get("synology_drive_username")
NAS_PASS = config_nas.get("synology_drive_password")
NAS_IP = config_nas.get("synology_drive_ip")

REMOTE_ROOT_FOLDER = "/mydrive/新闻文档爬取与合并/"


def ensure_starred_folder_exists(
    synd, remote_folder_path, starred_folder_name, data_items
):
    starred_folder_path = path_join(remote_folder_path, starred_folder_name)
    if not any(item["display_path"] == starred_folder_path for item in data_items):
        try:
            synd.create_folder(starred_folder_name, remote_folder_path)
            logging.info(f"文件夹创建成功: {starred_folder_path}")
        except Exception as e:
            logging.info(f"创建文件夹失败: {e}")
            return False
    return True


def move_starred_files(synd, data_items, remote_folder_path):
    starred_folder_name = "加星"
    # 检查加星文件夹是否存在
    if not ensure_starred_folder_exists(
        synd, remote_folder_path, starred_folder_name, data_items
    ):
        return

    starred_folder_path = path_join(remote_folder_path, starred_folder_name)

    # 移动加星文件
    for item in data_items:
        if item.get("starred") and item.get("type") == "file":
            try:
                synd.move_path(item["display_path"], starred_folder_path)
                logging.info(
                    f"移动文件成功: {os.path.basename(item['display_path'])} -> 【{starred_folder_path.replace(REMOTE_ROOT_FOLDER, '')}】"
                )
            except Exception as e:
                logging.info(f"移动文件失败: {e}，文件: {item['display_path']}")


def process_stars_move():
    # default http port is 5000, https is 5001.
    with SynologyDrive(
        NAS_USER, NAS_PASS, NAS_IP, https=False, dsm_version="7"
    ) as synd:
        remote_folder_names = ["hubeigov", "renmin"]
        for folder_name in remote_folder_names:
            remote_folder_path = path_join(REMOTE_ROOT_FOLDER, folder_name)
            data = synd.list_folder(remote_folder_path)
            data_items = data["data"]["items"]
            move_starred_files(synd, data_items, remote_folder_path)


if __name__ == "__main__":
    process_stars_move()
