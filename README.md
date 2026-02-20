# Runox 自动续期机器人

每小时第 05 分自动运行，完成续期 + 开机操作。

---

## 📁 文件结构

```
├── .github/
│   └── workflows/
│       └── runox_auto.yml   # GitHub Actions 工作流
├── runox_auto.py            # 主脚本
└── README.md
```

---

## 🚀 部署步骤

### 第一步：Fork 或上传到你的 GitHub 仓库

### 第二步：配置 Secrets（账号密码）

进入仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 名称 | 值 |
|---|---|
| `RUNOX_USERNAME` | 你的 runox 账号（邮箱） |
| `RUNOX_PASSWORD` | 你的 runox 密码 |

> ⚠️ 账号密码存在 Secrets 里，不会出现在代码和日志中，安全！

### 第三步：启用 Actions

进入仓库 → **Actions** → 点击 **"I understand my workflows, go ahead and enable them"**

---

## ⏰ 运行时间

- **自动**：每小时 05 分（`cron: '5 * * * *'`）
- **手动**：Actions 页面点击 **Run workflow** 可立即触发

---

## 📋 执行流程

```
1. 打开 https://runox.io/en/
2. 点击 Log In
3. 输入账号密码
4. 自动过 Cloudflare 人机验证（UC 模式 + PyAutoGUI）
5. 点击 Log In 登录
6. 点击 Manage 按钮
7. 点击 Start / Restore → 续期完成
   └─ 如果没有此按钮 → 打印"未到续期时间"并跳过
8. 点击 Start → 开机
```

---

## 🔍 调试

- 运行失败时，Actions 会自动上传 `debug_*.png` 截图（保留 3 天）
- 进入 Actions → 对应的运行记录 → **Artifacts** 下载截图查看
