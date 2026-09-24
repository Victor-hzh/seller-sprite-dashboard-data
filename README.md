# 清洁家电市场数据看板

基于 SellerSprite 榜单 Excel 构建的亚马逊多站点清洁家电数据看板。当前支持美国、英国、德国、法国、意大利、西班牙和日本站，以及除螨仪、布艺清洗机、洗地机、扫地机器人和吸尘器五个品类。

本仓库同时保存网站源码、历史 Excel、统一数据文件和自动构建流程，可直接导入 Vercel。

## 技术栈

- Next.js 16
- React 19
- TypeScript
- Recharts
- Tailwind CSS

## 本地运行

需要 Node.js 22。

```bash
npm ci
npm run dev
```

浏览器打开 `http://localhost:3000`。

## 生产检查

```bash
npm run lint
npm run build
npm run start
```

项目不依赖运行时环境变量，也不需要配置数据库。

## Vercel 部署

1. 在 Vercel 选择 **Add New → Project**。
2. 授权 Vercel 访问 GitHub 仓库 `Victor-hzh/seller-sprite-dashboard-data`。
3. 导入该仓库，Framework Preset 选择 **Next.js**。
4. Root Directory 保持仓库根目录。
5. Build Command 使用 `npm run build`，Install Command 使用 `npm ci`。
6. 点击 **Deploy**。

仓库根目录的 `vercel.json` 已包含构建配置。以后 `main` 分支更新时，Vercel 会自动重新部署。仓库可以保持私有，无需为了 Vercel 改成公开。

## 数据更新流程

网站构建时直接读取：

```text
data/dashboard-data.json
```

历史 Excel 按日期保存在：

```text
data/source/YYYY-MM-DD/*.xlsx
```

向 `data/source` 提交新 Excel 后，`.github/workflows/build-dashboard-data.yml` 会运行 `tools/build_dashboard_data.py`，自动更新 `data/dashboard-data.json` 并提交到 `main`。随后 Vercel 会自动发布新数据。

为避免周度对比缺失，不要删除以前日期的 Excel。

## 日本站预留数据

日本站五个品类已在网页中预留。没有 Excel 时显示为“待接入”；以后加入对应文件并重新生成数据即可启用，不需要再次修改页面。

```text
BSR_JP_Mite-Vacuum_Top50_YYYY-MM-DD.xlsx
BSR_JP_Spot-Cleaner_Top50_YYYY-MM-DD.xlsx
BSR_JP_Wet-Dry-Floor-Washer_Top50_YYYY-MM-DD.xlsx
BSR_JP_Robot-Vacuum_Top50_YYYY-MM-DD.xlsx
BSR_JP_Stick-Vacuum_Top50_YYYY-MM-DD.xlsx
```

## 主要目录

```text
app/                                        页面入口与全局样式
components/                                 看板和界面组件
data/dashboard-data.json                    网站当前统一数据
data/source/                                按日期保存的历史 Excel
tools/                                      Excel 转换脚本与任务配置
.github/workflows/build-dashboard-data.yml  数据自动构建流程
public/                                     网站静态资源
package.json                                依赖与运行命令
vercel.json                                 Vercel 构建配置
```

## 数据安全

仓库不应保存 SellerSprite 账号密码、浏览器登录状态或本机运行环境。若将仓库改为公开，`data/source` 中的原始 Excel 和 `data/dashboard-data.json` 也会对所有人公开。
