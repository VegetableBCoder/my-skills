---
name: everything-file-search
description: everything是一个全局文件检索工具, 可以通过文件名检索windows系统内任意位置的文件. 当你知道用户本地的文件名部分或全名, 无论是否确定其存放目录, 需要进行文件检索时, 请使用此工具进行快速全局文件检索
---

# Everything 使用说明

## 命令格式

| 类别   | 选项                                 | 说明            | 示例                                         | 
|------|------------------------------------|---------------|--------------------------------------------|
| 搜索   | -r, -regex                         | 正则表达式搜索       | es -r "report.*202[5-6]"                   |
|      | -p, -match-path                    | 匹配完整路径        | es -p invoice                              |
|      | -path                              | 限制搜索目录范围      | es -p "D:\tmp\test1" zh_node.txt           |
|      | -i                                 | 要求文件名大小写必须匹配  | es -i uvx.exe                              |
| 结果控制 | -n, -max-results                   | 显示返回条数        | es -n 20 uvx.exe                           |
|      | -o                                 | 从第几个结果开始显示    | es -n 10 -o 10 uvx.exe                     |
| 排序   | -sort size/dm/name                 | 按大小/修改时间/名称排序 | es -sort size -n 10 uvx.exe                |
|      | -sort-ascending / -sort-descending | 升序/降序         | es -sort dm -sort-descending -n 10 uvx.exe |
| 导出   | -export-csv                        | 导出为csv表格      |                                            |
|      | -export-txt                        | 导出为纯文本        |                                            |

## 注意事项

* 搜索报错有可能是everything主进程没有启动, 需要根据命令执行结果确定是否提醒用户启动everything
* 使用时需要注意检索可能会出现一次匹配很多文件名的情况, 不确定返回的文件数量时尽量限制每次返回的文件个数
* 复杂搜索建议用双引号包裹搜索文本
* 支持 Everything 全部搜索语法（如 dm:>2025-01-01、size:>100mb 等）
* 输出可管道到其他命令
* 错误码 8 表示 Everything 未运行
