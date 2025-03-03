# 爬取新闻
## 爬取湖北省新闻
采用playwright的firefox浏览器自动化工具，爬取湖北省新闻网的新闻。
## 爬取人民网新闻
采用requests库爬取人民网新闻。
## 合并docx文件
采用python-docx库合并docx文件。

## 一次性运行代码
### 爬取2024年的所有新闻数据
```python browser_hubeigov_year.py```
```python browser_renmin_year.py```
### 归档文章--合并
```python archive_docx.py combine [nobreak]```
### 归档文章--移动
```python archive_docx.py move```