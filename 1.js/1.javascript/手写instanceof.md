# instanceof

检查目标对象的原型链中是否有与指定对象的原型相同的原型, 通过 === 严格等于来对于两个原型是否相等。

```
function myInstanceof(target, source) {
    let proto = target.__proto__;
    let prototype = source.prototype;
    let queue = [proto];
    // 循环 obj 原型链进行获取 __proto__ 与 prototype 对比
    while(queue.length) {
        let temp = queue.shift();
        if(temp === null) return false;
        if(temp === prototype) return true;
        queue.push(temp.__proto__);
    }
}

// 测试
myInstanceof(new Date(), Date);         // true
myInstanceof({}, Object);               // true
myInstanceof('Jason', Number);          // false
myInstanceof(23, String);               // false
```
