from synology_drive_api.drive import SynologyDrive
from utils_func import load_config, path_join, setup_logging
import requests


class MySynd(SynologyDrive):
    """
    Synology Drive 封装类，自动读取配置并连接 NAS。
    用法：with MySynd() as synd:
    """

    def __init__(self, config_path="config/secret.yaml"):
        self._logger = setup_logging()
        self._config_nas = load_config(config_path)
        self._nas_info = self._find_available_nas()
        if not self._nas_info:
            raise Exception("没有可用的Synology NAS")
        nas_addr, nas_port, is_https = self._nas_info
        super().__init__(
            self._config_nas.get("nas_username"),
            self._config_nas.get("nas_password"),
            nas_addr,
            https=is_https,
            dsm_version="7",
            port=nas_port,
        )

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

    def _try_connect(self, url):
        """内部方法，测试NAS地址连通性"""
        try:
            response = requests.get(url, timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def _find_available_nas(self):
        """内部方法，查找可用的NAS地址"""
        for addr_info in self._config_nas.get("nas_address", []):
            addr = addr_info.get("address")
            port = addr_info.get("port", 5000)
            is_https = addr_info.get("https", False)
            url = f"{'https' if is_https else 'http'}://{addr}:{port}"
            if self._try_connect(url):
                self._logger.debug(f"Synology Drive连接成功: {url}")
                return addr, port, is_https
        self._logger.error("没有可用的Synology Drive地址")
        return None


def process_stars_move_api():
    """遍历指定文件夹，将加星文件移动到加星子文件夹"""
    import os
    logger = setup_logging()
    remote_root_folder = "/mydrive/新闻文档爬取与合并/"
    remote_folder_names = ["hubeigov", "renmin"]
    starred_folder_name = "加星"

    def _gen_starred_folder_path(synd, remote_folder_path, starred_folder_name, data_items):
        """确保加星文件夹存在，不存在则创建，返回加星文件夹路径"""
        starred_folder_path = path_join(remote_folder_path, starred_folder_name)
        if not any(item["display_path"] == starred_folder_path for item in data_items):
            try:
                synd.create_folder(starred_folder_name, remote_folder_path)
                logger.info(f"文件夹创建成功: {starred_folder_path}")
            except Exception as e:
                logger.error(f"创建文件夹失败: {e}")
                return None
        return starred_folder_path

    with MySynd() as synd:
        for folder_name in remote_folder_names:
            remote_folder_path = path_join(remote_root_folder, folder_name)
            try:
                data = synd.list_folder(remote_folder_path)
                data_items = data["data"]["items"]
            except Exception as e:
                logger.error(f"获取文件夹内容失败: {e}, 路径: {remote_folder_path}")
                continue

            # 确保加星文件夹存在
            starred_folder_path = _gen_starred_folder_path(
                synd, remote_folder_path, starred_folder_name, data_items
            )
            if not starred_folder_path:
                continue

            for item in data_items:
                if item.get("starred") and item.get("type") == "file":
                    try:
                        synd.move_path(item["display_path"], starred_folder_path)
                        logger.info(
                            f"移动文件成功: {os.path.basename(item['display_path'])} -> 【{os.path.relpath(starred_folder_path, remote_root_folder)}】"
                        )
                    except Exception as e:
                        logger.error(f"移动文件失败: {e}，文件: {item['display_path']}")


def test():
    """示例：列出远程文件夹并保存到本地json"""
    import json

    remote_root_folder = "/mydrive/新闻文档爬取与合并/"
    with MySynd() as synd:
        obj = synd.list_folder(remote_root_folder)
        with open("debug/files.json", "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    test()
