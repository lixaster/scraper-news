from urllib.parse import urljoin
from browser_hubeigov import HubeigovScraper
import re
from utils_func import setup_logging

# 配置日志
logging = setup_logging()


class HubeigovScraperYear(HubeigovScraper):
    def __init__(self, config, year):
        # 父类初始化
        super().__init__(config)
        self.year = str(year)

    def get_paper_list(self, page):
        paper_list = []
        selector = "div.hbgov-index-bar"
        for url in self.url:
            i = 0
            flag = True
            while flag and i < 50:
                if i != 0:
                    url = urljoin(url, f"index_{i}.shtml")
                i += 1
                soup = self.fetch_page_soup(page, url, selector)
                sub_paper_list = self.parse_paper_list(soup, url)
                if sub_paper_list:  # 如果不是空列表
                    for paper in sub_paper_list:
                        if self.is_year_match(paper["pubtime"]):
                            paper_list.append(paper)
                        else:
                            flag = False
                            break
                else:
                    flag = False

        return paper_list

    def is_year_match(self, pubtime):
        datetime = self.format_date(pubtime)
        match = re.search(r"\d{4}", datetime)
        if match and self.year == match.group():
            return True
        return False


def browser_func(config_path, year):
    scraper = HubeigovScraperYear(config_path, year)
    return scraper.request_data()


if __name__ == "__main__":
    from utils_func import load_config, load_year_from_args

    # 读取 yaml 文件，获取配置信息
    config = load_config()
    year = load_year_from_args()
    browser_func(config, year)
