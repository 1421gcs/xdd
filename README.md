# Baidu Hot Search Archiver

该仓库提供一个简单的服务，每天定时爬取百度实时热搜榜单，并将结果以 JSON 文件保存。通过 GitHub Actions 的计划任务（schedule）功能，任务会在每天北京时间早上 7 点自动执行，并将最新的数据保存到 `data/` 目录下。

## 功能概览

- 使用 Python 脚本抓取 [百度热搜榜](https://top.baidu.com/board?tab=realtime) 数据。
- 将抓取结果保存为结构化的 JSON 文件，包含排名、标题、摘要、热度值以及详情链接。
- 通过 GitHub Actions 每天定时运行，自动提交更新后的数据文件。

## 本地运行

1. 确保已经安装 Python 3.9 及以上版本。
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

   如果没有 `requirements.txt`，也可以手动安装：

   ```bash
   pip install requests beautifulsoup4
   ```

3. 执行脚本：

   ```bash
   python scripts/fetch_baidu_hotsearch.py
   ```

4. 执行完成后，最新的数据会存储在 `data/baidu-hotsearch-YYYYMMDD.json` 和 `data/latest.json` 中。

## GitHub Actions 工作流

- 工作流文件位于 `.github/workflows/baidu-hotsearch.yml`。
- 触发规则：
  - 每天 UTC 时间 23:00（北京时间 07:00）自动触发。
  - 支持手动触发（workflow_dispatch）。
- 运行流程：
  1. 检出仓库代码。
  2. 安装 Python 及依赖。
  3. 执行爬虫脚本，生成最新数据。
  4. 如果数据发生变化，自动提交并推送。

## 数据文件

- `data/baidu-hotsearch-YYYYMMDD.json`：每日快照，文件名中的日期为北京时间日期。
- `data/latest.json`：始终保存最新一次运行的结果。

## 注意事项

- 爬虫使用公开页面，请遵循目标网站的使用条款，避免频繁请求。
- GitHub Actions 默认使用 UTC 时间，如需调整为其他时区，请修改工作流中的 `cron` 表达式。
- 如需扩展字段或更换数据源，可在 `scripts/fetch_baidu_hotsearch.py` 中进行修改，代码中已添加详细注释便于二次开发。
