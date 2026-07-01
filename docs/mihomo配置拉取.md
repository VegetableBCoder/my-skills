# Mihomo配置拉取

## 准备

* 安装mihomo
* 安装mihomo-web控制台

## 说明

* mihomo的管理页面是不能直接传远程地址给mihomo内核的, 只能下载了文件然后让内核去加载配置
* 你的vpn服务提供商提供的订阅地址不一定做了跨域允许操作, mihomo界面上填写订阅地址下载文件会CORS错误
* 所以写一个脚本直接下载配置然后调mihomo内核加载配置

## 参考脚本

```
#!/bin/sh
# mihomo 订阅更新脚本
# 用法: mihomo-update <订阅地址>
# 功能: 拉取订阅 → 适配本地端口/面板 → 覆盖配置 → 触发 reload

CONF_DIR=/etc/mihomo
CONF_FILE=$CONF_DIR/config.yaml
BACKUP_FILE=$CONF_DIR/config.yaml.bak
TMP_FILE=/tmp/mihomo-sub.yaml
API="http://127.0.0.1:9090"
CTRL_PORT=9090
UI_DIR=/etc/mihomo/ui

# 参数检查
if [ -z "$1" ]; then
    echo "用法: $0 <订阅地址>"
    echo "示例: $0 'https://sub.example.com/xxx?clash=1'"
    exit 1
fi

SUB_URL="$1"
echo "订阅地址: $SUB_URL"

# 1. 拉取订阅
echo "=== 拉取订阅 ==="
if ! wget -q -O "$TMP_FILE" "$SUB_URL"; then
    echo "错误: 订阅拉取失败"
    exit 1
fi
SIZE=$(wc -c < "$TMP_FILE")
if [ "$SIZE" -lt 100 ]; then
    echo "错误: 订阅内容过小（${SIZE}字节），可能无效"
    cat "$TMP_FILE"
    exit 1
fi
echo "已拉取，大小: ${SIZE} 字节"

# 2. 备份当前配置
if [ -f "$CONF_FILE" ]; then
    cp "$CONF_FILE" "$BACKUP_FILE"
    echo "已备份旧配置 → $BACKUP_FILE"
fi

# 3. 适配本地配置
echo "=== 适配本地配置 ==="
# external-controller 改为 9090
sed -i "s/^external-controller:.*/external-controller: 0.0.0.0:${CTRL_PORT}/" "$TMP_FILE"
# 确保 external-ui 存在（若订阅无此字段则追加到 external-controller 行后）
if ! grep -q "^external-ui:" "$TMP_FILE"; then
    sed -i "/^external-controller:/a external-ui: ${UI_DIR}" "$TMP_FILE"
fi
echo "端口: ${CTRL_PORT}，面板: ${UI_DIR}"

# 4. 配置语法测试
echo "=== 配置测试 ==="
if ! /usr/local/bin/mihomo -d "$CONF_DIR" -f "$TMP_FILE" -t >/dev/null 2>&1; then
    echo "错误: 配置测试失败，已保留旧配置"
    /usr/local/bin/mihomo -d "$CONF_DIR" -f "$TMP_FILE" -t 2>&1 | tail -5
    rm -f "$TMP_FILE"
    exit 1
fi
echo "配置测试通过"

# 5. 覆盖配置
cp "$TMP_FILE" "$CONF_FILE"
rm -f "$TMP_FILE"
echo "配置已更新 → $CONF_FILE"

# 6. 触发 reload
echo "=== 重载配置 ==="
if wget -qO- "$API" >/dev/null 2>&1; then
    # API 可达，热重载
    wget -qO- --header="Content-Type: application/json" \
        --post-data='{"path":"'"$CONF_FILE"'"}' \
        "$API/config?force=true" >/dev/null 2>&1
    echo "已热重载"
else
    # API 不可达，重启服务
    echo "API 不可达，重启服务..."
    mihomo-ctl restart
fi

# 7. 验证
echo "=== 验证 ==="
sleep 2
if wget -qO- "$API/version" >/dev/null 2>&1; then
    VER=$(wget -qO- "$API/version")
    echo "API: $VER"
    PCOUNT=$(wget -qO- "$API/proxies" 2>/dev/null | grep -o '"name"' | wc -l)
    echo "代理条目: $PCOUNT"
    echo "订阅更新完成"
else
    echo "警告: API 无响应，检查日志: /var/log/mihomo.log"
fi
```