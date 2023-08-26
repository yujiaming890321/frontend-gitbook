# bash

## 查询进程

sudo lsof -i tcp:3002

## 根据PID杀死进程

sudo kill -9 8166

## find 查询

```bash
find ./src/tds-8.1.1 -type f -name "*.ts"
```

## 删除文件夹指定后缀文件

```bash
find ./src/tds-8.1.1 -type f -name "*.ts" -exec rm {} \;
```

## 批量修改文件后缀

```bash
find ./src/tds-8.1.1 -exec {sed -i "s/ts/tss/g" `grep ts -rl ./src/tds-8.1.1`};
```
