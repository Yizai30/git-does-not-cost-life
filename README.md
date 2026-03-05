# git-submit

> 🚀 自动重试 git push，直到成功 - 解决 GitHub 网络不稳定问题的终极工具

你是否曾经因为 GitHub 网络不稳定而反复手动重试 `git push`？**git-submit** 来了！它会自动重试直到成功，你只需要运行一次命令，剩下的交给它。

## ✨ 特性

- **♾️ 无限重试** - 持续重试直到推送成功，无需人工干预
- **📈 智能退避** - 指数退避策略（5秒 → 300秒），避免网络拥塞
- **🔔 多渠道通知** - 支持桌面通知、邮件、Webhook
- **💾 状态持久化** - 系统重启或中断后自动恢复
- **🖥️ 跨平台** - Windows、macOS、Linux 全支持
- **📊 结构化日志** - JSON 格式日志，便于调试和分析

## 📦 安装

### 从 PyPI 安装（推荐）

```bash
pip install git-submit
```

### 从源码安装

```bash
git clone https://github.com/Yizai30/git-does-not-cost-life.git
cd git-does-not-cost-life
pip install -e .
```

## 🚀 快速开始

### 1. 初始化配置

```bash
git-submit config init
```

这会在 `~/.git-submit/config.yaml` 创建默认配置文件。

### 2. 推送到 GitHub

```bash
# 基本用法 - 自动重试直到成功
git-submit push

# 查看详细输出
git-submit push --verbose

# Dry run 模式（测试配置）
git-submit push --dry-run
```

### 3. 查看状态

```bash
# 查看当前操作状态
git-submit status

# 查看历史记录
git-submit history

# 清理孤儿状态文件
git-submit cleanup
```

## 💡 使用场景

### 场景 1：日常提交

```bash
# 提交代码
git add .
git commit -m "feat: add new feature"

# 使用 git-submit 推送（自动重试）
git-submit push
```

### 场景 2：推送失败？不用担心！

传统方式：
```bash
$ git push
# 失败... 手动重试
$ git push
# 还是失败... 再试
$ git push
# 终于成功！
```

使用 git-submit：
```bash
$ git-submit push
# 工具自动重试 436 次，历时 24 分钟
✓ Push successful after 436 attempt(s)!
  Duration: 1482.3s
```

### 场景 3：指定远程和分支

```bash
# 推送到特定的远程和分支
git-submit push --remote github --branch develop

# 推送所有分支
git-submit push --all
```

### 场景 4：强制推送

```bash
# 强制推送（需要确认）
git-submit push --force
```

## ⚙️ 配置

配置文件位于 `~/.git-submit/config.yaml`：

```yaml
# 重试设置
retry:
  initial_delay_seconds: 5      # 初始延迟（秒）
  max_backoff_seconds: 300       # 最大退避时间（秒）
  linear: false                   # 是否使用线性退避

# Git 设置
git:
  remote: origin                  # 默认远程
  branch: auto                    # 默认分支（auto = 自动检测）

# 通知设置
notifications:
  desktop:
    enabled: true                 # 启用桌面通知

  email:
    enabled: false                # 启用邮件通知
    smtp_host: smtp.gmail.com
    smtp_port: 587
    username: your-email@gmail.com
    password_env: SMTP_PASSWORD   # 环境变量名
    from_address: your-email@gmail.com
    to_address: your-email@gmail.com

  webhooks:
    - url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 修改配置

```bash
# 编辑配置文件
git-submit config edit

# 验证配置
git-submit config validate

# 查看当前配置
git-submit config show
```

## 📝 命令参考

### push 命令

```bash
git-submit push [OPTIONS]
```

**选项：**
- `--remote <REMOTE>` - 指定远程仓库
- `--branch <BRANCH>` - 指定分支
- `--all` - 推送所有分支
- `--force, -f` - 强制推送
- `--dry-run` - 验证配置但不推送
- `--retry-delay <SECONDS>` - 初始重试延迟
- `--max-backoff <SECONDS>` - 最大退避时间
- `--linear-retry` - 使用线性退避
- `--notify-email` - 启用邮件通知
- `--notify-desktop` - 启用桌面通知
- `--notify-webhook <URL>` - 添加 Webhook URL
- `--no-notify` - 禁用所有通知
- `--verbose, -v` - 详细输出
- `--quiet, -q` - 静默模式
- `--json` - JSON 格式输出
- `--follow, -f` - 实时跟踪日志

### config 命令

```bash
git-submit config <COMMAND>
```

**子命令：**
- `init` - 初始化配置
- `edit` - 编辑配置
- `validate` - 验证配置
- `show` - 显示当前配置

### status 命令

```bash
git-submit status [OPTIONS]
```

**选项：**
- `--orphaned` - 显示孤儿状态文件

### 其他命令

```bash
git-submit history    # 查看操作历史
git-submit cleanup    # 清理孤儿状态文件
git-submit help       # 显示帮助
```

## 🔧 故障排除

### 问题：`git-submit` 命令未找到

**解决方案：**
1. 确认已正确安装：`pip show git-submit`
2. 检查 Python Scripts 目录是否在 PATH 中
3. 尝试使用完整路径或 `python -m git_submit`

### 问题：推送失败，显示 "Git not found"

**解决方案：**
1. 确认已安装 Git：`git --version`
2. 确保 git 在系统 PATH 中
3. Windows 用户：从 https://git-scm.com/ 安装 Git

### 问题：桌面通知不工作

**解决方案：**
- Windows：确保已安装通知支持
- macOS：在系统偏好设置中允许通知
- Linux：确保已安装 `libnotify`

### 问题：邮件发送失败

**解决方案：**
1. 检查 SMTP 配置是否正确
2. 确认环境变量已设置：`export SMTP_PASSWORD=your-password`
3. 对于 Gmail，可能需要使用应用专用密码

## 📊 工作原理

git-submit 使用以下策略确保推送成功：

1. **指数退避算法**：每次失败后，等待时间按指数增长，添加随机抖动
2. **智能错误检测**：区分临时错误（可重试）和永久错误（不可重试）
3. **状态持久化**：每次重试前保存状态，支持中断恢复
4. **异步通知**：推送成功后并发发送多个通知

### 退避策略示例

```
尝试 1: 立即执行
尝试 2: 等待 5 秒
尝试 3: 等待 10 秒
尝试 4: 等待 20 秒
尝试 5: 等待 40 秒
...
尝试 N: 等待 300 秒（最大值）
```

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 仓库链接

- **GitHub**: https://github.com/Yizai30/git-does-not-cost-life
- **Gitee**: https://gitee.com/Yizai30/git-does-not-cost-life

## ⭐ 如果这个项目对你有帮助

请给一个 Star ⭐️ 支持一下！

---

**Made with ❤️ to solve GitHub network instability issues**
