# babel

```js
babel src --out-dir dist --extensions .ts --copy-files --no-copy-ignored --ignore **/__tests__,**/__integration_tests__
```

## tsc vs babel

babel 是单文件编译的，每个文件处理方式都一样。
tsc 是多文件一起编译的，因为在编译过程中会解析模块语法，去做类型推导和检查。

babel 不会解析 ts 类型，所以 namespace合并、const enum 这种需要解析类型内容的就不支持。

编译 ts 代码用 babel 更好，需要类型检查单独跑 tsc --noEmit。
