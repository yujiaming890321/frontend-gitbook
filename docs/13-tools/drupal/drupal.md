# Drupal

Drupal ships with `.htaccess` files that secure the Drupal installation.

Clean URLs—that is, those devoid of question marks, ampersands, or other strange characters—are achieved using Apache’s mod_rewrite component.

[strict coding standards](http://drupal.org/nodes/318)

- 模块 (Module): 用于为 Drupal 网站增加/扩展/修改功能的文件集合（在其它一些 CMS 中也被称为“插件”）
- 主题 (Theme): 用于定义站点外观、视觉风格和交互体验的文件集合，通过切换主题可以变更网站布局和风格。
- 发行版 (Distribution): 出于特定需求而定制的、预装好模块、主题和配置的 Drupal 版本。可以理解为基于 Drupal 制作的各种 CMS。
- 内容类型 (Content Type): 出于不同用途创建的数据载体，例如：

  - 由标题、正文两个字段组成的“文章”
  - 由标题、预览图、价格、商品介绍等字段组成的“商品”

- 字段 (Field): 用于提供某类数据输入、保存和展示的载体，通过向实体添加不同的字段可以实现各种数据存储要求。

- 节点 (Node): 通过内容类型创建出来的具体页面都是节点，如某篇文章、某件商品、某个个人资料。

- 实体 (Entity): 可理解为不同数据类型（字段组合）的统称，例如节点、评论、用户、区块都是不同类型的实体（都可以通过添加字段进行定制）。

- 区域 (Region): Drupal 主题将页面划分为多个区域（如页头、左边栏、主体、右边栏、页脚等），根据不同的页面规则，在不同的区域放置不同的区块，从而实现对页面内容高度灵活的管理和控制。

- 区块 (Block): 放置于区块中的内容块，可以是一段文字、一张图片、一个菜单、一个列表等等。

## User 用户

你处理你网站上的许多用户帐户吗？ Drush可以帮助管理轻松。

您可以使用以下命令创建新用户：

```js
drush user-create username --mail="email@example.com" --password="password"
```

然后终端将显示关于新创建的用户的一些信息。 要删除此用户吗？ 使用以下命令：

```js
drush user-cancel username
```

就这么简单。 想要更改您的密码？ 或任何其他用户的密码？ 运行以下命令：

```js
drush user-password admin --password="new_pass"
```

## Heredoc

1.以<<<End开始标记开始，以End结束标记结束，结束标记必须顶头写，不能有缩进和空格，且在结束标记末尾要有分号 。开始标记和开始标记相同，比如常用大写的EOT、EOD、EOF来表示，但是不只限于那几个，只要保证开始标记和结束标记不在正文中出现即可。

2.位于开始标记和结束标记之间的变量可以被正常解析，但是函数则不可以。在heredoc中，变量不需要用连接符.或,来拼接

```js
$v=2;
$a= <<<EOF
"abc"$v
"123"
EOF;
echo $a; //结果连同双引号一起输出："abc"2 "123"
```

3.heredoc常用在输出包含大量HTML语法d文档的时候。比如：函数outputhtml()要输出HTML的主页。

```js
function outputhtml(){
echo <<<EOT
<html>
<head><title>主页</title></head>
<body>主页内容</body>
</html>
EOT;
}
outputhtml();
```

## hook implementations

- Implements hook_help()

## Implements hook_menu

## [yarml](http://www.ruanyifeng.com/blog/2016/07/yaml.html)

## if

```php
<?php if ($current_country === 'CN'): ?>
<?php endif; ?>
```
