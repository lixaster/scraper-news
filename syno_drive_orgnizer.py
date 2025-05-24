from synology_drive_api.drive import SynologyDrive
import os
from utils_func import load_config, path_join, setup_logging
import requests


class SynoDriveOrgnizer:
    def __init__(self, config_path="config/secret.yaml"):
        self.logger = setup_logging()
        config_nas = load_config(config_path)
        self.nas_user = config_nas.get("nas_username")
        self.nas_pass = config_nas.get("nas_password")
        self.nas_addr_list = config_nas.get("nas_address", [])
        self.remote_root_folder = "/mydrive/新闻文档爬取与合并/"
        self.synd = None
        self.nas_addr = None  # 选中的地址
        self.nas_port = None
        self.nas_https = None

    @staticmethod
    def try_connect(url):
        try:
            response = requests.get(url, timeout=3)
            return response.status_code == 200
        except:
            return False

    def find_available_nas(self):
        for addr_info in self.nas_addr_list:
            addr = addr_info.get("address")
            port = addr_info.get("port", 5000)
            https = addr_info.get("https", False)
            url = f"{'https' if https else 'http'}://{addr}:{port}"
            if self.try_connect(url):
                self.nas_addr = addr
                self.nas_port = port
                self.nas_https = https
                self.logger.info(f"NAS连接成功: {url})")
                return True
        self.logger.info("没有可用的NAS地址")
        return False

    def ensure_starred_folder_exists(
        self, remote_folder_path, starred_folder_name, data_items
    ):
        starred_folder_path = path_join(remote_folder_path, starred_folder_name)
        if not any(item["display_path"] == starred_folder_path for item in data_items):
            try:
                self.synd.create_folder(starred_folder_name, remote_folder_path)
                self.logger.info(f"文件夹创建成功: {starred_folder_path}")
            except Exception as e:
                self.logger.info(f"创建文件夹失败: {e}")
                return False
        return True

    def move_star_files(self):
        remote_folder_names = ["hubeigov", "renmin"]
        starred_folder_name = "加星"
        for folder_name in remote_folder_names:
            remote_folder_path = path_join(self.remote_root_folder, folder_name)
            data = self.synd.list_folder(remote_folder_path)
            data_items = data["data"]["items"]
            # 确保加星文件夹存在
            if not self.ensure_starred_folder_exists(
                remote_folder_path, starred_folder_name, data_items
            ):
                continue
            starred_folder_path = path_join(remote_folder_path, starred_folder_name)
            for item in data_items:
                if item.get("starred") and item.get("type") == "file":
                    try:
                        self.synd.move_path(item["display_path"], starred_folder_path)
                        self.logger.info(
                            f"移动文件成功: {os.path.basename(item['display_path'])} -> 【{os.path.relpath(starred_folder_path, self.remote_root_folder)}】"
                        )
                    except Exception as e:
                        self.logger.info(f"移动文件失败: {e}，文件: {item['display_path']}")

    def test(self):
        self.logger.info(self.synd.list_folder(self.remote_root_folder))

    def run(self):
        if not self.find_available_nas():
            return
        with SynologyDrive(
            self.nas_user,
            self.nas_pass,
            self.nas_addr,
            https=self.nas_https,
            dsm_version="7",
            port=self.nas_port,
        ) as synd:
            self.synd = synd
            self.move_star_files()


def process_stars_move():
    orgnizer = SynoDriveOrgnizer()
    orgnizer.run()


if __name__ == "__main__":
    process_stars_move()
