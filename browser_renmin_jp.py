import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Optional, Any
from base_scraper import BaseScraper
from utils_func import setup_logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging = setup_logging()


class RenminJpScraper(BaseScraper):
    def __init__(self, config: Dict[str, Any]):
        # 父类初始化，获得config、url、save_folder
        self.source_name = "renmin_jp"
        super().__init__(config)
        self.base_url = self.get_base_url(self.url)
        self.session = self._setup_session()

    def _setup_session(self) -> requests.Session:
        """设置带有重试机制的会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_base_url(self, urls: List[str]) -> str:
        """从URL列表中获取基础URL"""
        if not urls:
            raise ValueError("URL列表不能为空")
        parsed_url = urlparse(urls[0])
        return f"{parsed_url.scheme}://{parsed_url.netloc}/"

    def request_data(self) -> bool:
        """请求数据的主入口"""
        try:
            return self.retrieve_paper()
        except Exception as e:
            logging.error(f"请求数据时发生错误: {str(e)}")
            return False

    def get_paper_list(self) -> List[Dict[str, str]]:
        """获取文章列表"""
        paper_list = []
        for url in self.url:
            try:
                soup = self.fetch_page_soup(url)
                category = self.parse_categories(soup)
                sub_paper_list = self.parse_paper_list(soup, category)
                if sub_paper_list:
                    paper_list.extend(sub_paper_list)
            except Exception as e:
                logging.error(f"处理URL {url} 时发生错误: {str(e)}")
                continue
        return paper_list

    def parse_categories(self, soup: BeautifulSoup) -> str:
        """解析文章分类"""
        try:
            category = (
                soup.find("div", class_="left fl")
                .find("h3", class_="tit", recursive=False)
                .text.strip()
            )
            return category
        except AttributeError:
            logging.error("无法找到文章分类")
            return "未知分类"

    def parse_paper_list(self, soup: BeautifulSoup, category: str) -> List[Dict[str, str]]:
        """解析文章列表"""
        paper_list = []
        try:
            div_main = soup.find("div", class_="left fl")
            div_items = div_main.find_all("div", class_="list clearfix")
            
            for div_item in div_items:
                try:
                    title = div_item.find("h3", class_="tit").text.strip()
                    span_tag = div_item.find("span", class_="time").text.strip()
                    pubtime = re.search(r"\d{4}-\d{2}-\d{2}", span_tag).group()
                    href = urljoin(self.base_url, div_item.find("a").attrs["href"])
                    
                    paper_list.append({
                        "category": category,
                        "pubtime": pubtime,
                        "href": href,
                        "title": title,
                    })
                except Exception as e:
                    logging.error(f"解析文章条目时发生错误: {str(e)}")
                    continue
        except Exception as e:
            logging.error(f"解析文章列表时发生错误: {str(e)}")
        return paper_list

    def get_paper_info(self, href: str) -> List[Any]:
        """获取文章详细信息"""
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
            logging.error(f"获取文章信息时发生错误: {str(e)}")
            return []

    def fetch_page_soup(self, url: str) -> BeautifulSoup:
        """获取页面内容并解析为BeautifulSoup对象"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 设置编码
            soup = BeautifulSoup(response.text, "html.parser")
            meta_tag = soup.find("meta", attrs={"http-equiv": "content-type"})
            
            if meta_tag and "content" in meta_tag.attrs:
                content = meta_tag["content"]
                charset = content.split("charset=")[-1] if "charset=" in content else None
                if charset:
                    response.encoding = charset
                    soup = BeautifulSoup(response.text, "html.parser")
                    
            return soup
        except Exception as e:
            logging.error(f"获取页面 {url} 时发生错误: {str(e)}")
            raise

    def extract_and_write_paragraphs(self, doc: Any, p_elements: List[Any]) -> None:
        """提取并写入段落内容"""
        for p in p_elements:
            try:
                if content := p.find(string=True, recursive=False):
                    paragraph = self.format_paragraph(doc)
                    run = self.format_paragraph_font(paragraph)
                    run.text = content.replace("　　", "").strip()
            except Exception as e:
                logging.error(f"处理段落时发生错误: {str(e)}")
                continue


def browser_func(config: Dict[str, Any]) -> bool:
    """主函数入口"""
    try:
        scraper = RenminJpScraper(config)
        return scraper.request_data()
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        return False


if __name__ == "__main__":
    from utils_func import load_config

    # 读取 yaml 文件，获取配置信息
    config = load_config()
    browser_func(config)
