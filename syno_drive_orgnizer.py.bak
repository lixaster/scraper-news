from synology_drive_api.drive import SynologyDrive
import os
from utils_func import load_config, path_join, setup_logging
import requests


class SynoDriveOrgnizer:
    def __init__(self, config_path="config/secret.yaml"):
        self.logger = setup_logging()
        self.config_nas = load_config(config_path)
        self.remote_root_folder = "/mydrive/新闻文档爬取与合并/"

    @staticmethod
    def try_connect(url):
        try:
            response = requests.get(url, timeout=3)
            return response.status_code == 200
        except:
            return False

    def find_available_nas(self):
        for addr_info in self.config_nas.get("nas_address", []):
            addr = addr_info.get("address")
            port = addr_info.get("port", 5000)
            is_https = addr_info.get("https", False)
            url = f"{'https' if is_https else 'http'}://{addr}:{port}"
            if SynoDriveOrgnizer.try_connect(url):
                self.logger.debug(f"Synology Drive连接成功: {url}")
                return addr, port, is_https
        self.logger.error("没有可用的Synology Drive地址")
        return None

    def gen_starred_folder_path(
        self, remote_folder_path, starred_folder_name, data_items
    ):
        starred_folder_path = path_join(remote_folder_path, starred_folder_name)
        if not any(item["display_path"] == starred_folder_path for item in data_items):
            try:
                self.synd.create_folder(starred_folder_name, remote_folder_path)
                self.logger.info(f"文件夹创建成功: {starred_folder_path}")
            except Exception as e:
                self.logger.error(f"创建文件夹失败: {e}")
                return None
        return starred_folder_path

    def move_star_files(self):
        remote_folder_names = ["hubeigov", "renmin"]
        starred_folder_name = "加星"
        for folder_name in remote_folder_names:
            remote_folder_path = path_join(self.remote_root_folder, folder_name)
            data = self.synd.list_folder(remote_folder_path)
            data_items = data["data"]["items"]
            # 确保加星文件夹存在
            starred_folder_path = self.gen_starred_folder_path(
                remote_folder_path, starred_folder_name, data_items
            )
            if not starred_folder_path:
                continue

            for item in data_items:
                if item.get("starred") and item.get("type") == "file":
                    try:
                        self.synd.move_path(item["display_path"], starred_folder_path)
                        self.logger.info(
                            f"移动文件成功: {os.path.basename(item['display_path'])} -> 【{os.path.relpath(starred_folder_path, self.remote_root_folder)}】"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"移动文件失败: {e}，文件: {item['display_path']}"
                        )

    def run_test(self):
        nas_info = self.find_available_nas()
        if not nas_info:
            return
        nas_addr, nas_port, is_https = nas_info
        with SynologyDrive(
            self.config_nas.get("nas_username"),
            self.config_nas.get("nas_password"),
            nas_addr,
            https=is_https,
            dsm_version="7",
            port=nas_port,
        ) as self.synd:
            obj = self.synd.list_folder(self.remote_root_folder)
            self.synd.create_folder("456", f"{self.remote_root_folder}")
            # 保存到json文件
            import json

            with open("debug/files.json", "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=4)

    def run(self):
        """必须通过run方法, 否则synd对象无法被正确初始化"""
        try:
            nas_info = self.find_available_nas()
            if not nas_info:
                return
            nas_addr, nas_port, is_https = nas_info
            with SynologyDrive(
                self.config_nas.get("nas_username"),
                self.config_nas.get("nas_password"),
                nas_addr,
                https=is_https,
                dsm_version="7",
                port=nas_port,
            ) as self.synd:
                self.move_star_files()
        except Exception as e:
            self.logger.error(f"处理加星文件夹失败: {e}")


def process_stars_move_api():
    orgnizer = SynoDriveOrgnizer()
    orgnizer.run()


def test():
    orgnizer = SynoDriveOrgnizer()
    orgnizer.run_test()


if __name__ == "__main__":
    test()
