# PHP

打印日志 var_dump、print_r

## isset

函数用于检测变量是否已设置并且非 NULL。

```php
if (isset($A->id)) {
    $B->id = $A->id;
}
```

## . 连接符

```php
$suggestions = 'page__' . $wxt_active;
```

## array

```php
$node_admin_paths = array('node/*/edit', 'node/add', 'node/add/*', 'node/*/extend_review_date');
```

### array_merge

```php
array_merge($A, $B);
```

### array_filter

```php
$match = array_filter(
    $array,
    function ($A) use ($B) {
        return $A->getId() == $B;
    }
);
```

### array_pop

```php
array_pop($match);
```

## foreach

```php
foreach ($node_admin_paths as $node_admin_path) {
    if (drupal_match_path(current_path(), $node_admin_path)) {
        $replace_jquery = FALSE;
    }
}
```

## strtotime

将英文文本日期时间解析为 Unix 时间戳

```php
strtotime("+5 hours")
```
