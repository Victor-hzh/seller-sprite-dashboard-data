# SellerSprite Dashboard Data

这是卖家精灵看板的独立数据仓库，与原有 Amazon Best Sellers 网站仓库完全分开。

## 数据目录

每次更新按日期保存：

```text
data/source/YYYY-MM-DD/*.xlsx
```

每个日期目录包含当次下载的30份站点与品类榜单数据，以及采集清单（如有）。

## 安全说明

本仓库只保存榜单数据，不保存卖家精灵账号密码、Chrome登录信息、运行环境或自动化程序的敏感文件。
