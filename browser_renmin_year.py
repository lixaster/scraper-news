from urllib.parse import urljoin
from browser_renmin import RenminScraper
import re
from utils_func import setup_logging

# 配置日志
logging = setup_logging()


class RenminScraperYear(RenminScraper):
    def __init__(self, year):
        # 父类初始化
        super().__init__()
        self.year = str(year)

    def parse_paper_list(self, soup, category_list):
        div_main = soup.find("div", class_="leftItem")
        div_items = div_main.find_all("div", class_="item")
        paper_list = []

        for i, item in enumerate(div_items):
            category = category_list[i] if i < len(category_list) else "Unknown"
            sub_category_href = self.get_sub_category_href(item)
            while True:
                soup = self.fetch_page_soup(sub_category_href)
                sub_item = soup.find("div", class_="leftItem").find(
                    "div", class_="item"
                )
                paper_list.extend(self.get_sub_paper_list(sub_item, category))

                next_page_link = soup.find("td", attrs={"align": "right"}).find(
                    "a", string="下一页"
                )
                if next_page_link:
                    sub_base_url = sub_category_href.rsplit("/", 1)[0]
                    sub_category_href = f"{sub_base_url}/{next_page_link["href"]}"
                else:
                    break

        return paper_list

    def get_sub_paper_list(self, item, category):
        paper_list = []
        li_tags = item.find_all("li")
        for li in li_tags:
            if i_tag := li.find("i"):
                pubtime = i_tag.text.strip()
            else:
                pubtime = re.search(r"\d{4}-\d{2}-\d{2}", li.get_text()).group()

            if not pubtime.startswith(self.year):
                break

            a_tag = li.find("a")
            title = a_tag.text.strip().replace(f"（{category}）", "") if a_tag else ""
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

    def get_sub_category_href(self, item):
        try:
            # 找到更多按钮的href，即h3下的a标签的href
            sub_category_href = item.find("h3").find("a")["href"].strip()
            return sub_category_href
        except Exception as e:
            self.logger.error(f"get_sub_category_href()运行过程出错：{str(e)}")
            return None


def browser_func(year):
    scraper = RenminScraperYear(year)
    return scraper.run()


if __name__ == "__main__":
    from utils_func import load_year_from_args

    year = load_year_from_args()
    browser_func(year)
