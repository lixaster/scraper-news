import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from base_scraper import BaseScraper
from utils_func import setup_logging

# 配置日志
logging = setup_logging()


class RenminJpScraper(BaseScraper):
    def __init__(self, config):
        # 父类初始化，获得config、url、save_folder
        self.source_name = "renmin_jp"
        super().__init__(config)
        self.base_url = self.get_base_url(self.url)

    def get_base_url(self, url):
        parsed_url = urlparse(url[0])
        return f"{parsed_url.scheme}://{parsed_url.netloc}/"

    def request_data(self):
        # 父类方法，必须在子类中实现get_paper_list和get_paper_info方法
        return self.retrieve_paper()

    def get_paper_list(self):
        paper_list = []
        for url in self.url:
            soup = self.fetch_page_soup(url)
            category = self.parse_categories(soup)

            sub_paper_list = self.parse_paper_list(soup, category)
            if sub_paper_list:  # 如果不是空列表
                paper_list.extend(sub_paper_list)
            
        return paper_list

    def parse_categories(self, soup):
        # 返回文本
        return (
            soup.find("div", class_="left fl")
            .find("h3", class_="tit", recursive=False)
            .text.strip()
        )

    def parse_paper_list(self, soup, category):

        div_main = soup.find("div", class_="left fl")
        div_items = div_main.find_all("div", class_="list clearfix")
        paper_list = []

        for div_item in div_items:
            title = div_item.find("h3", class_="tit").text.strip()
            span_tag = div_item.find("span", class_="time").text.strip()
            pubtime = re.search(r"\d{4}-\d{2}-\d{2}", span_tag).group()
            href = urljoin(self.base_url, div_item.find("a").attrs["href"])
            paper_list.append(
                {
                    "category": category,
                    "pubtime": pubtime,
                    "href": href,
                    "title": title,
                }
            )
        return paper_list

    def get_paper_info(self, href):
        try:
            soup = self.fetch_page_soup(href)
            div = soup.find("div", class_="w1000 j-d2txt j-d2txt-fanyi clearfix")
            # <h2 class="sub">首次用于地震国际救援！DeepSeek7小时攻克缅甸救灾语言关</h2>
            sub_title = soup.find("h2", class_="sub")
            p_elements = [
                child for child in div.children if child.name == "p" and child.string
            ]
            # 可能出现没有直接子元素的p标签
            if not p_elements:
                p_elements = [
                    p for p in div.find_all("p") if p.string and p.string.strip()
                ]
            p_elements.insert(0, sub_title)
            return p_elements

        except Exception as e:
            logging.error(f"get_paper_info()运行过程出错：{str(e)}")
            return []

    def fetch_page_soup(self, url):
        response = requests.get(url)
        # 解析HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找<meta>标签
        meta_tag = soup.find("meta", attrs={"http-equiv": "content-type"})

        # 如果找到<meta>标签，提取编码信息
        if meta_tag and "content" in meta_tag.attrs:
            content = meta_tag["content"]
            # 从content中提取charset
            charset = content.split("charset=")[-1] if "charset=" in content else None
            if charset:
                response.encoding = charset  # 设置响应编码

        # 设置编码后，需要重新解析HTML
        soup = BeautifulSoup(response.text, "html.parser")
        return soup

    def extract_and_write_paragraphs(self, doc, p_elements):
        for p in p_elements:
            if content := p.find(string=True, recursive=False):
                paragraph = self.format_paragraph(doc)
                run = self.format_paragraph_font(paragraph)
                run.text = content.replace("　　", "").strip()


def browser_func(config):
    scraper = RenminJpScraper(config)
    return scraper.request_data()


if __name__ == "__main__":
    from utils_func import load_config

    # 读取 yaml 文件，获取配置信息
    config = load_config()
    browser_func(config)
