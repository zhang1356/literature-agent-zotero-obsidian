# 文献检索智能体：朋友使用说明

## 软件用途

文献检索智能体是一个 Windows 本地运行的研究辅助工具。它可以输入研究主题，检索候选论文，进行相关性评分，并把选中的文献保存到 Zotero 和 / 或 Obsidian，同时用本地 SQLite 记录同步历史，避免重复保存。

## 最快使用步骤

1. 解压 `LiteratureAgent_Windows.zip` 到一个普通文件夹，例如桌面或 D 盘。
2. 双击 `setup.bat`，等待依赖安装完成。
3. 双击 `start.bat`。
4. 浏览器打开 `http://localhost:8501` 后，进入“系统设置”。
5. 至少填写 `Obsidian Vault Path`，点击“保存配置”，重启应用。
6. 在“系统设置”点击“测试 Obsidian 路径”。
7. 回到“文献检索”，输入关键词，检索并保存选中文献。

## 只用 Obsidian 的用法

只想生成本地 Markdown 笔记时，只需要配置 Obsidian：

- `Obsidian Vault Path`：你的 Obsidian Vault 根目录。
- `Obsidian Literature Folder`：文献笔记文件夹，默认是 `Literature Notes`。

保存论文时，页面会提示“将仅保存 Obsidian 笔记”。Zotero 未配置不会导致程序崩溃。

## 只用 Zotero 的用法

只想写入 Zotero 时，填写：

- `Zotero Library ID`
- `Zotero Library Type`，个人文库一般选择 `user`
- `Zotero API Key`

API Key 需要有写入权限。保存论文时，页面会提示“将仅写入 Zotero”。Obsidian 未配置时不会生成 Markdown 笔记。

## 没有模型 API 的用法

不配置模型 API 也可以使用。系统会：

- 正常检索候选论文；
- 使用本地启发式规则评分；
- 支持保存到 Obsidian 或 Zotero。

模型 API 只是用于更智能的评分和总结，不是首次使用的必需项。

## 如何测试 Obsidian

1. 进入“系统设置”。
2. 填写并保存 `Obsidian Vault Path` 和 `Obsidian Literature Folder`。
3. 重启应用。
4. 点击“测试 Obsidian 路径”。

测试会检查 Vault 路径是否存在、是否可写，并在 Literature Notes 文件夹写入一个临时文件后删除。成功时会显示“Obsidian 路径可用”。

## 如何测试 Zotero

1. 在 Zotero 账号设置里创建一个有写入权限的 API Key。
2. 在“系统设置”填写 Library ID、Library Type 和 API Key。
3. 保存配置并重启应用。
4. 点击“测试 Zotero 连接”。

测试会读取最近 1 条 Zotero 文献。页面不会显示完整 API Key。

## 如何测试模型 API

1. 在“系统设置”填写 API Key、Base URL 和模型名称。
2. 保存配置并重启应用。
3. 点击“测试模型 API”。

如果失败，通常是 API Key 错误、Base URL 错误、模型名称错误或网络不可用。失败时系统仍会使用启发式评分。

## 如何停止程序

双击 `stop.bat`。它会尝试停止本机 8501 或 8502 端口上的 Streamlit 服务。

## 如何删除本软件

1. 先双击 `stop.bat` 停止程序。
2. 删除解压出来的整个软件文件夹。
3. 如果你不想保留生成的笔记，请自行在 Obsidian Vault 中删除对应的 Literature Notes 文件夹。
4. 如果你写入过 Zotero，请在 Zotero 中手动删除不需要的条目。

## 常见问题

### Python 未安装怎么办

请安装 Python 3.10 或更新版本，并勾选 “Add Python to PATH”。安装后重新双击 `setup.bat`。

### 端口 8501 被占用怎么办

`start.bat` 会优先使用 8501，如果被占用会尝试 8502。也可以先双击 `stop.bat` 后再启动。

### Obsidian 笔记没有生成怎么办

检查 `Obsidian Vault Path` 是否是正确的 Vault 根目录，并使用“测试 Obsidian 路径”确认可写。

### Zotero 保存失败怎么办

检查 Zotero Library ID、Library Type 和 API Key 是否正确，并确认 API Key 具有写入权限。

### API Key 填错怎么办

进入“系统设置”重新填写 API Key 并保存，然后重启应用。

## 隐私说明

- 所有配置默认保存在本机。
- API Key 保存在 `config/user_config.json`。
- 不要把自己的 `config/user_config.json` 发给别人。
- 软件不会主动上传 Obsidian 笔记，除非用户配置了模型 API 并调用分析功能。
- 发布包不应包含 `.env`、`config/user_config.json`、数据库、日志、虚拟环境或测试目录。

## 界面风格说明

本应用采用暖色极简风格，不包含 Claude、Anthropic 或其他第三方品牌资产。
