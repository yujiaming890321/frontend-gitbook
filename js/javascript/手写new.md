# new 时发生了什么？


1. 创建一个新的对象 obj;
2. 将这个空对象的**proto**成员指向了 Base 函数对象 prototype 成员对象
3. Base 函数对象的 this 指针替换成 obj, 相当于执行了 Base.call(obj);
4. 如果构造函数显示的返回一个对象，那么则这个实例为这个返回的对象。 否则返回这个新创建的对象

## 简单写法
```javascript
var obj = {};
obj.__proto__ = Base.prototype;
Base.call(obj);
```

## 满分写法
```javascript
function myNew(target){
    let result = {};
    let arg = Array.prototype.slice.call(arguments, 1);
    // 将实例对象的 __proto__ 指向 target.prototype
    Object.setPrototypeOf(result, target.prototype);
    // this 指向实例对象
    target.apply(result, arg);
   return result;
}

// 测试
function User(name, age) {
    this.name = name;
    this.age = age;
}

let user = myNew(User, "Jason", 23);
console.log(user.__proto__ === User.prototype);            // true
```