import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from base_scraper import BaseScraper


class RenminScraper(BaseScraper):
    def __init__(self, sub=""):
        # 父类初始化，获得url、save_folder
        self.source_name = "renmin" + sub
        super().__init__()
        self.base_url = self.get_base_url(self.url)

    def run(self):
        return self.retrieve_paper()

    def get_base_url(self, url):
        if isinstance(url, list):
            url = url[0]
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/"

    def get_paper_list(self):
        if type(self.url) == str:
            self.url = [self.url]
        paper_list = []
        try:
            for url in self.url:
                soup = self.fetch_page_soup(url)
                category = self.parse_categories(soup)
                sub_paper_list = self.parse_paper_list(soup, category)
                if sub_paper_list:  # 如果不是空列表
                    paper_list.extend(sub_paper_list)
            return paper_list
        except Exception as e:
            self.logger.error(f"get_paper_list()运行过程出错：{str(e)}")
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

    def parse_categories(self, soup):
        div_header = soup.find("div", class_="header").find("div", class_="item")
        span_tags = div_header.find_all("span") if div_header else []
        return [span.find("a").text.strip() for span in span_tags]

    def parse_paper_list(self, soup, category_list):
        div_main = soup.find("div", class_="leftItem")
        div_items = div_main.find_all("div", class_="item")
        paper_list = []

        for i, item in enumerate(div_items):
            category = category_list[i] if i < len(category_list) else "Unknown"
            li_tags = item.find_all("li")
            for li in li_tags:
                if i_tag := li.find("i"):
                    pubtime = i_tag.text.strip()
                else:
                    pubtime = re.search(r"\d{4}-\d{2}-\d{2}", li.get_text()).group()

                a_tag = li.find("a")
                title = (
                    a_tag.text.strip().replace(f"（{category}）", "") if a_tag else ""
                )
                href = urljoin(self.base_url, a_tag["href"]) if a_tag else ""
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
            div = soup.find("div", class_="rm_txt_con cf")

            p_elements = [
                child for child in div.children if child.name == "p" and child.string
            ]
            # 可能出现没有直接子元素的p标签
            if not p_elements:
                p_elements = [
                    p for p in div.find_all("p") if p.string and p.string.strip()
                ]

            return p_elements

        except Exception as e:
            self.logger.error(f"get_paper_info()运行过程出错：{str(e)}")
            return []

    def extract_and_write_paragraphs(self, doc, p_elements):
        for p in p_elements:
            if content := p.find(string=True, recursive=False):
                paragraph = self.format_paragraph(doc)
                run = self.format_paragraph_font(paragraph)
                run.text = content.replace("　　", "").strip()


def browser_func():
    scraper = RenminScraper()
    return scraper.run()


if __name__ == "__main__":
    browser_func()
