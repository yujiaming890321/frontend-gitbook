# Typescript

## 特殊字符(?, !, !!)

属性或参数中使用 ？：表示该属性或参数为可选项

变量后使用 ！：表示类型推断排除null、undefined

```js
const obj = { flag1: true };
const test1 = !!obj.flag1; // equal const test1 = obj.flag1 || false
consolo.log(test1); // true
const test2 = !!obj.flag2; // equal const test2 = obj.flag2 || false
consolo.log(test2); // false
```
