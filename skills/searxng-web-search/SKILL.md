---
name: searxng-web-search
description: searchxng是一个聚合多种搜索引擎的元搜索引擎, 此工具提供了对searchxng的访问能力. 当需要需要访问即时信息如新闻等信息时请使用此工具; 当需要联网检索内容但不确定访问的网页地址时请使用此工具。
---

# SearXNG Web 搜索工具

## 搜索引擎支持情况

### 可用的搜索引擎

* 搜索引擎分类

| name    | code    |
|---------|---------|
| 通用      | general |
| 网页      | web     |
| 科学      | science |
| 新闻      | news    |
| IT / 技术 | it      |
| 代码仓库    | repos   |

* 搜索引擎列表

| engine           | 所属categories | 备注              |
|------------------|--------------|-------------------|
| google           | general, web | 需注意 Google 反爬风险 |
| bing             | web          |                   |
| yahoo            | web          |                   |
| baidu            | web          |                   |
| arxiv            | science      |                   |
| google scholar   | science      |                   | 
| semantic scholar | science      | AI学术论文            |
| bing news        | news         |                   | 
| duckduckgo news  | news         |                   | 
| google news      | news         |                   |
| askubuntu        | it           | Ubuntu Q&A        |
| docker hub       | it           | Docker Hub 镜像仓库  |
| gentoo           | it           | Gentoo Linux Wiki | 
| stackoverflow    | it           |                   |
| github           | it,repos     |                   |
| huggingface      | repos        |                   | 
| ollama           | repos        | Ollama 模型         |

## 使用说明

### 使用此 skill 时，推荐按以下流程操作：

1. **可选**：先用 `suggest` 子命令获取搜索建议，优化搜索词; 一般不需要搜索建议, agent自行推理确定搜索词即可
2. **执行**：用 `search` 子命令执行搜索，结果写入输出文件
    * 根据搜索需求类型确定搜索业务类型(category), 如果没有合适的category, 降级到web/general这样的通用搜索引擎
    * 如果选择的category下没有合适的搜索引擎, 比如要搜寻python安装包, 但是it/repos下面都没有pypi, 就需要降级到网页搜索
3. **读取**：使用 Read 工具读取输出 JSON 文件获取完整结果
4. **深入**：如需查看某条结果的完整内容，使用 `webfetch` 工具获取页面内容

## 脚本位置

脚本文件夹`scripts`与当前 SKILL.md 位于同一目录，路径为 `scripts\searxng_search.py`。

Agent 调用时，使用相对于项目根目录的路径：

```bash
python .claude/skills/searxng-web-search/scripts/searxng_search.py <子命令> [参数...]
```

## 两个子命令

### 子命令 1：获取搜索建议（suggest）

通过 SearXNG 的 `autocompleter` 接口获取搜索词补全建议，结果直接输出 JSON 到 stdout。

**命令格式：**

```bash
python .claude/skills/searxng-web-search/scripts/searxng_search.py suggest "<搜索词>"
```

**参数：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `query` | 是 | 搜索词（位置参数） |

**示例：**

```bash
python .claude/skills/searxng-web-search/scripts/searxng_search.py suggest "SpringBoot"
```


### 子命令 2：执行搜索（search）

通过 SearXNG 执行 Web 搜索，返回聚合多个搜索引擎的结果。

**命令格式：**

```bash
python .claude/skills/searxng-web-search/scripts/searxng_search.py search "<搜索词>" [选项...]
```

**参数：**

| 参数 | 必填 | 说明                                                         |
|------|------|------------------------------------------------------------|
| `query` | 是 | 搜索词（位置参数）                                                  |
| `-o`, `--output` | 否 | 输出 JSON 文件路径（默认写入系统临时目录）                                   |
| `-p`, `--pageno` | 否 | 页码，从 1 开始（默认 1）                                            |
| `-c`, `--categories` | 否 | 搜索分类code，多个用逗号分隔                                           |
| `-e`, `--engines` | 否 | 搜索引擎，多个用逗号分隔（如 `google,bing,baidu`）                        |
| `-t`, `--time_range` | 否 | 时间范围：`none` / `day` / `week` / `month` / `year`（默认 `none`） |
| `-s`, `--safesearch` | 否 | 安全搜索级别：0=关闭 1=中等 2=严格                                      |
| `-n`, `--top` | 否 | stdout 摘要展示前 N 条（默认 10；完整结果始终写入文件）                         |



**示例：**

```bash
# 基本搜索
python .claude/skills/searxng-web-search/scripts/searxng_search.py search "Python asyncio tutorial"

# 指定引擎 + 最近一周的结果
python .claude/skills/searxng-web-search/scripts/searxng_search.py search "Python asyncio" -e bing,baidu -t week

# 自定义输出路径，只显示前 5 条摘要
python .claude/skills/searxng-web-search/scripts/searxng_search.py search "Python asyncio" -o ./search_result.json -n 5
```

**结果对象字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `url` | string | 结果链接 |
| `title` | string | 结果标题 |
| `content` | string | 结果摘要 / 内容片段 |
| `engine` | string | 来源引擎名称 |
| `engines` | array | 所有返回此结果的引擎列表 |
| `positions` | array | 在各引擎中的排名 |
| `score` | number | 相关性得分（越高越相关） |
| `category` | string | 结果分类（general / it / news / videos 等） |
| `publishedDate` | string\|null | 发布日期 |
| `parsed_url` | array | 解析后的 URL 片段 |
| `img_src` | string | 相关图片地址 |
| `thumbnail` | string | 缩略图地址 |

---

## 故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `无法连接 SearXNG 服务` | 本地 SearXNG 未启动 | 请启动 localhost:8888 的 SearXNG 服务 |
| HTTP 500+ 错误 | SearXNG 内部错误 | 查看 SearXNG 日志排查 |
| 结果为空 | 搜索词无匹配或引擎全部不可用 | 检查 `unresponsive_engines` 字段，尝试调整搜索词或指定引擎 |
| 自动补全结果为空 | autocomplete 后端未配置 | 这是正常现象，不影响搜索功能 |