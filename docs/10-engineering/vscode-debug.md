# vscode debugger

在launch.json中会使用到一些预定变量，这里说明一下：

${workspaceRoot}：VSCode中打开文件夹的路径
${workspaceRootFolderName}：VSCode中打开文件夹的路径, 但不包含"/"
${file}：当前打开的文件
${fileBasename}： 当前打开文件的文件名, 不含扩展名
${fileDirname}： 当前打开文件的目录名
${fileExtname} 当前打开文件的扩展名
${cwd}：当前执行目录

## debug for docker

extension install php debug

```json
{
    "version": "0.2.0",
    "configurations": [
        // debug for docker
        {
            "name": "Xdebug for Docker",
            "type": "php",
            "request": "launch",
            "port": 9001,
            "pathMappings": {
                "/usr/share/nginx/": "${workspaceFolder}", //左侧是docker 运行镜像目录，右侧是当前文件夹
            },
            "skipFiles": [
                "${workspaceRoot}/node_modules/**/*.js",
                "<node_internals>/**/*.js"
            ]
        },
    ]
}
```

## debug for node

1. run and debug 中点击 Node.js
2. 然后选择启动命令

## test debug

new javascript debug terminal
run test
