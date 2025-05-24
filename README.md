# 爬取新闻
## 爬取湖北省新闻
采用playwright的firefox浏览器自动化工具，爬取湖北省新闻网的新闻。
## 爬取人民网新闻
采用requests库爬取人民网新闻。
## 合并docx文件
采用python-docx库合并docx文件。

## 一次性运行代码
1. 爬取2024年的所有新闻数据
```bash
python browser_hubeigov_year.py 2024
python browser_renmin_year.py 2024
```
2. 归档文章--合并
```bash
python archive_docx.py combine [nobreak]
```
3. 归档文章--移动
```bash
python archive_docx.py move
```
4. 归档文章--加星
```bash
python archive_docx.py stars
```

## synology drive api
> 使用 synology_drive_api 库，实现在 Synology NAS 上移动加星文件到指定文件夹  
> 依赖库：pip install synology_drive_api  
> 参考文档：https://github.com/zbjdonald/synology-drive-api

### 参考函数：
> TEST_FOLDER = "/mydrive/新闻文档爬取与合并/hubeigov"
1. 上传：
```python
with open('record.json', 'rb') as file:
   ret_upload = synd.upload_file(file, dest_folder_path=TEST_FOLDER)
```
2. 重命名：
> 'TEST_FOLDER/record.json' to 'TEST_FOLDER/api_create_folder/record.json'
```python
synd.rename_path(f'record2.json', f'{TEST_FOLDER}/record.json')
```
3. 移动：
```python
origin_path = f"{TEST_FOLDER}/record.json"
dest_folder = f"{TEST_FOLDER}/api_create_folder"
synd.move_path(origin_path, dest_folder)
```
4. 创建文件夹：
```python
synd.create_folder('api_create_folder', TEST_FOLDER)
```
