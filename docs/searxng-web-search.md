# SearXNG联网搜索skill安装说明

## 工作

* wsl/docker: 用于运行searxng, 本文使用wsl方式运行
  * 由于docker-desktop在公司环境使用存在法律风险, 16G机器安装一套rancher-desktop/k3s过于吃力, 选择wsl
  * 由于资源有限, 选择了alpine发行版, 没有sudo, 没有curl等不少命令, 
* vpn: 使用bing/google/github/huggingface等搜索都需要科学上网. 建议装在wsl中, windows使用也方便; 也可以直接用windows上安装的vpn提供的代理地址
  * 个人习惯装在wsl上, window clash这些vpn开系统代理会影响浏览器访问, windows用wsl的vpn直接在火狐上设置代理地址即可
* python: 自行按照searxng的版本选择python版本

## 安装 searxng

* 给Agen提供wsl的信息让Agent帮你装就行, 文档暂时未整理

## 配置searxng

* 配置文件贼长, 记得告诉Agent改outgoing部分的proxies, 添加代理地址就行

## 验证searxng可用性

* 访问[聚合搜索地址](http://localhost:8888), 搜索并验证searxng功能运行是否正常, 代理是否正常

## 启停脚本参考

```shell
#!/bin/sh

APP_HOME="/usr/local/searxng/searxng-src"
VENV="/usr/local/searxng/searx-pyenv"
LOG_DIR="/usr/local/searxng/logs"

su - searxng -c "
mkdir -p $LOG_DIR &&
cd $APP_HOME &&
. $VENV/bin/activate &&
nohup python -m searx.webapp \
    > $LOG_DIR/searx.out.log \
    2> $LOG_DIR/searx.err.log \
    < /dev/null &
echo \$! > $LOG_DIR/searx.pid

```

```shell
#!/bin/sh

PID_FILE="/usr/local/searxng/logs/searx.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "PID file not found."
    exit 1
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm -f "$PID_FILE"
    echo "SearXNG stopped."
else
    echo "Process $PID is not running."
    rm -f "$PID_FILE"
fi
```

## 选MCP还是Skill?

### MCP 配置

* 命令: npx -y mcp-searxng
* 参数: { "SEARXNG_URL": "http://localhost:8888" }

### Skill说明

* 一些参数固化到python脚本中, 减少了暴露给模型的categories和engines
* 可以明显缩减上下文长度
