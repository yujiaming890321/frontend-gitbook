# Currying 柯里化

实现自动Currying之前，先看看怎么手写Currying的函数, 以add函数为例

```js
// 剪头函数版本
let add = n1 => n2 => n1 + n2
// function版本
function add(n1){
  return function(n2){
    return n1 + n2
  }
}
```

## 优点

### 参数复用

```js
// 正则验证字符串 reg.test(txt);
// 很符合我们写业务代码的习惯
function check(reg, txt) {
    return reg.test(txt);
}
check(/\d+/g, 'test')       //false
check(/[a-z]+/g, 'test')    //true
// curry 后
function curringCheck(reg) {
    return function(txt) {
        return reg.test(txt)
    }
}
// 中间函数， 预先设定规则
var hasNumber = curryingCheck(/\d+/g)
var hasLetter = curryingCheck(/[a-z]+/g)
// 这样，想做哪种检测，直接调用中间函数即可，不需要每次都传入规则
hasNumber('test1')      // true
hasNumber('testtest')   // false
hasLetter('21212')      // false
// es 6 的简便写法, 这里先用稍微用下下面的内容
// 其中， fn 是待 Currying 的函数， curry 是工具函数
let curry = (fn) => (fArg) => (sArg) => fn(fArg, sArg);
```

### 提前确认

```js
// 原代码
var on = function(element, event, handler) {
    if (document.addEventListener) {
        if (element && event && handler) {
            element.addEventListener(event, handler, false);
        }
    } else {
        if (element && event && handler) {
            element.attachEvent('on' + event, handler);
        }
    }
}
// 自执行函数形成闭包
var on = (function () {
    if (document.addEventListener) {
        return function(element, event, handler) {
            if (element && event && handler) {
                element.addEventListener(event, handler, false);
            }
        }
    } else {
        return function(element, event, handler) {
            if (element && event && handler) {
                element.attachEvent('on' + event, handler);
            }
        }
    }
})();
// 换一种写法可能比较好理解一点，上面就是把isSupport这个参数给先确定下来了
var on = function(isSupport, element, event, handler) {
    isSupport = isSupport || documnet.addEventListener;
    if (isSupport) {
        return element.addEventListener(event, handler, false);
    } else {
        return element.attachEvent('on' + event, handler);
    }
}
```

### 延迟运行

```js
Function.prototype.bind = function(context) {
    var _this = this;
    var args = Array.prototype.slice.call(arguments, 1);
    return functon() {
        return _this.apply(context, args)
    }
}
```
