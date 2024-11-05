# 工作环境安装

[FiraCode字体](https://github.com/tonsky/FiraCode)

https://github.com/tonsky/FiraCode/releases

iterm2
oh my zsh
git
sourcetree
[nvm (node)](https://github.com/nvm-sh/nvm#installing-and-updating) or n

```node
brew install n
```

fnm(windows use)

```node
# 安装 fnm (快速 Node 管理器)
winget install Schniz.fnm
# 配置 fnm 环境
fnm env --use-on-cd | Out-String | Invoke-Expression
# 下载并安装 Node.js
fnm use --install-if-missing 18
# 验证环境中是否存在正确的 Node.js 版本
node -v # 应该打印 `v18.20.4`
# 验证环境中是否存在正确的 npm 版本
npm -v # 应该打印 `10.7.0`
```

nrm --npm镜像源
vscode
fiddle
