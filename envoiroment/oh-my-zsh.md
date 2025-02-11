# iterm2 + oh-my-zsh

下载安装 iterm2 ，下载安装 oh-my-zsh

## [iterm2](http://iterm2.com/)

iterm2 在官网下载安装即可

### 将iTem2设置为默认终端

iTerm2 -> Make iTerm2 Default Term

### 全局快捷键

preference -> Keys -> Hotkey -> Show/hide iTerm2 with a system-wide hotkey

### [solarized配色](https://github.com/altercation/solarized)

下载后双击 Solarized Dark.itermcolors 和 Solarized Light.itermcolors 就可以把配置文件导入到 iTerm2 里

preference -> profiles -> colors -> color presets 选择刚刚安装的配色主题

### ⌘+Q关闭iTerm 2 时每次弹窗提示问题

iTerm 2 中，进入Preference-General-Closing栏目，将Confirm "Quit iTerm2(⌘Q)" command选项勾选去掉就行

## oh-my-zsh

```node
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

### [agnoster主题](https://github.com/fcamblor/oh-my-zsh-agnoster-fcamblor/)

```node
git clone git@github.com:fcamblor/oh-my-zsh-agnoster-fcamblor.git
```

Run install script to copy theme to your ~/.oh-my-zsh folder

vim 打开 .zshrc

```node
vim ~/.zshrc

ZSH_THEME="agnoster"

source ~/.zshrc
```

### [powerline字体](https://github.com/powerline/fonts)

```node
git clone git@github.com:powerline/fonts.git
```

preference -> Keys -> Text ->

### [自动提示](https://github.com/zsh-users/zsh-autosuggestions)

1. 下载到~/.oh-my-zsh/custom/plugins 路径下

    ```node
    git clone git@github.com:zsh-users/zsh-autosuggestions.git $ZSH_CUSTOM/plugins/zsh-autosuggestions
    ```

2. 用 vim 打开 .zshrc 文件，找到插件设置命令，默认是 plugins=(git) ，我们把它修改为

    ```node
    vim ~/.zshrc
    plugins=(zsh-autosuggestions git)
    source ~/.zshrc
    ```

3. 重新打开终端窗口。

    PS：当你重新打开终端的时候可能看不到变化，可能你的字体颜色太淡了，我们把其改亮一些：

    移动到 ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions 路径下

    ```node
    cd ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions
    ```

    用 vim 打开 zsh-autosuggestions.zsh 文件，修改 ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=10' （ fg=10 在我电脑上显示良好）。

### [语法高亮](https://github.com/zsh-users/zsh-syntax-highlighting)

1. 下载到~/.oh-my-zsh/custom/plugins 路径下

    ```node
    git clone git@github.com:zsh-users/zsh-syntax-highlighting.git $ZSH_CUSTOM/plugins/zsh-syntax-highlighting
    ```

2. 配置.zshrc文件，插入一行。

    ```node
    source ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
    ```

3. source ~/.zshrc

### 卸载oh my zsh

在命令行输入如下命令，回车即可：uninstall_oh_my_zsh
