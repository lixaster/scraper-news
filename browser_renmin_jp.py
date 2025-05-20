from urllib.parse import urljoin
import re
from browser_renmin import RenminScraper


class RenminJpScraper(RenminScraper):
    def __init__(self):
        # 父类初始化，获得url、save_folder
        super().__init__(sub="_jp")

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
            self.logger.error(f"get_paper_info()运行过程出错：{str(e)}")
            return []


def browser_func():
    scraper = RenminJpScraper()
    return scraper.run()


if __name__ == "__main__":
    browser_func()
