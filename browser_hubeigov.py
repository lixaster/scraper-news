from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from base_scraper import BaseScraper
from utils_func import setup_logging

# 配置日志
logging = setup_logging()

class HubeigovScraper(BaseScraper):
    def __init__(self, config):
        # 父类初始化，获得config、url或列表、save_folder
        self.source_name = "hubeigov"
        super().__init__(config)
        self.headless_mode = config.get("HEADLESS", False)

    def request_data(self):
        try:
            with sync_playwright() as playwright:
                self.run(playwright)
                return True
        except Exception as e:
            logging.error(f"request_data()运行过程出错：{str(e)}")
            return False

    def run(self, playwright: Playwright):
        browser = None
        context = None
        try:
            logging.info("开始启动playwright...")
            browser = playwright.firefox.launch(headless=self.headless_mode)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(120000)  # 设置超时时间为2分钟
            self.retrieve_paper(page)
        except Exception as e:
            logging.error(f"run()运行过程出错：提前退出playwright。原因：{str(e)}")
        finally:
            if context:
                context.close()
            if browser:
                browser.close()
            logging.info("playwright已关闭。")

    def get_paper_list(self, page):
        paper_list = []
        for url in self.url:
            selector = "div.hbgov-index-bar"
            soup = self.fetch_page_soup(page, url, selector)
            sub_paper_list = self.parse_paper_list(soup, url)
            if sub_paper_list:  # 如果不是空列表
                paper_list.extend(sub_paper_list)
        return paper_list

    def fetch_page_soup(self, page, url, selector=""):
        try:
            page.goto(url)
            if selector:
                page.wait_for_selector(selector)
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            return soup
        except Exception as e:
            logging.error(f"fetch_page_soup()运行过程出错：{str(e)}")
            return None

    def parse_paper_list(self, soup, url):
        category = soup.find("div", class_="hbgov-index-bar").find("a").get_text()
        div_main = soup.find("div", class_="hbgov-bfc-block")
        if not div_main:
            return []

        paper_list = []
        list_elements = div_main.find_all("li") or div_main.find_all(
            "div", class_="right"
        )
        for element in list_elements:
            pubtime = (
                element.find("span" if div_main.find_all("li") else "div").get_text()
                if element.find("span" if div_main.find_all("li") else "div")
                else ""
            )
            # 找出element下的a标签，如果有1个，则执行以下操作，如果有2个，则执行下面的else
            a_tags = element.find_all("a")
            if not a_tags:
                continue

            # 处理附件
            if len(a_tags) >= 2:
                href_attachement = a_tags[1]["href"]
            else:
                href_attachement = None

            href = urljoin(url, a_tags[0]["href"])
            title = a_tags[0].get_text()

            paper_list.append(
                {
                    "category": category,
                    "pubtime": pubtime,
                    "href": href,
                    "title": title,
                    "href_attachement": href_attachement,
                }
            )
        return paper_list

    def extract_and_write_paragraphs(self, doc, p_elements):
        for p in p_elements:
            if "text-align: right" in p.get("style", ""):
                continue
            paragraph = self.format_paragraph(doc)
            # 处理标签
            for content in p.contents:
                run = self.format_paragraph_font(paragraph)

                text = ""
                if content.name is None:
                    text = content
                else:
                    text = content.get_text()
                    if content.name == "strong":
                        run.bold = True

                run.text = text.strip()

    def get_paper_info(self, href, page):
        try:
            soup = self.fetch_page_soup(page, href)
            div = soup.find("div", class_="hbgov-article-content")
            if not div:
                div = soup.find("div", class_="text_record")
            p_elements = div.find_all("p") if div else []
            return p_elements

        except Exception as e:
            logging.error(f"get_paper_info()运行过程出错：{str(e)}")
            return []

    def retrieve_attachement(
        self, page, href_attachement, file_name_attachement, category, datetime
    ):
        try:
            if href_attachement:
                soup = self.fetch_page_soup(page, href_attachement)

                # 相关文件标题
                h1 = soup.find("div", class_="hbgov-article-title").find("h1")
                h1_text = h1.get_text().strip() if h1 else ""
                # 相关文件主体
                div = soup.find("div", class_="hbgov-article-content")
                if not div:
                    div = soup.find("div", class_="text_record")
                p_elements_attachement = div.find_all("p") if div else []

            if p_elements_attachement:
                self.create_docx(
                    file_name_attachement,
                    h1_text,
                    f"{category}-相关文件",
                    datetime,
                    p_elements_attachement,
                )
        except Exception as e:
            logging.error(f"retrieve_attachement()运行过程出错：{str(e)}")


def browser_func(config):
    scraper = HubeigovScraper(config)
    return scraper.request_data()


if __name__ == "__main__":
    from utils_func import load_config

    # 读取 yaml 文件，获取配置信息
    config = load_config()
    browser_func(config)
