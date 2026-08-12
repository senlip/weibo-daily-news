# 微博每日新鲜事

每天北京时间 08:00 自动抓取微博实时热搜榜，生成 HTML 报告并通过 GitHub Pages 发布，手机随时可看。

## 访问

- 报告入口: https://senlip.github.io/weibo-daily-news/

## 文件说明

- `weibo_hot_cloud.py`: 云端爬虫（零第三方依赖，直接调用微博热搜 API）
- `.github/workflows/daily.yml`: GitHub Actions 每日定时任务
- `reports/`: 生成的每日报告（HTML + JSON）

## 说明

- 报告数据为抓取时刻的微博热搜快照，仅作信息整理用途
