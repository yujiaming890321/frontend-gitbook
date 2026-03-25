# es13 - ECMA2022

## 声明类的字段

> 到目前为止，在ES规范中，类的字段定义和初始化是在类的构造函数中完成的。但是在新的提案中，类字段可以在类的顶层被定义和初始化

```js
class Point {
   name;
   title;
   size = 1;
}
```

## 私有方法&字段

> 用#前缀来定义类的私有方法和字段。

```js
class Person {
   name;
   #age;
   get #age(){
       return #age;
   }
  $initValue(){
      this.name = '';
      this.#age = 12;
  }
}
```

## 类的静态公共方法和字段

> 在之前的类的字段和私有方法提案的基础上，为JavaScript类增加了静态公共字段、静态私有方法和静态私有字段的特性。

```js
class Enum {
  static collectStaticFields() {
    // Static methods are not enumerable and thus ignored
    this.enumKeys = Object.keys(this);
  }
}
class ColorEnum extends Enum {
  static red = Symbol('red');
  static green = Symbol('green');
  static blue = Symbol('blue');
  static _ = this.collectStaticFields(); // (A)

  static logColors() {
    for (const enumKey of this.enumKeys) { // (B)
      console.log(enumKey);
    }
  }
}
ColorEnum.logColors();

// Output:
// 'red'
// 'green'
// 'blue'
```

## ECMScript 类静态初始化块

> 类静态块提议提供了一种优雅的方式，在类声明/定义期间评估静态初始化代码块，可以访问类的私有字段

```js
class Person {
    static name;
    age;
}
try {
    Person.name = getNameA();
} catch {
    Person.name = getNameB();
}
```

## 检测私有字段

> 当我们试图访问一个没有被声明的公共字段时，会得到未定义的结果，同时访问私有字段会抛出一个异常。
> 我们根据这两个行为来判断是否含有公共字段和私有字段。
> 但是这个建议引入了一个更有趣的解决方案，它包括使用in操作符，如果指定的属性/字段在指定的对象/类中，则返回真，并且也能判断私有字段

```js
class Person {
    name;
    #age;
    get #age(){
        return #age;
    }
    $initValue(){
        this.name = '';
        this.#age = 12;
    }
    static hasAge(person){
        return #gae in person;
    }
}
```

## 正则匹配索引

> 该提案提供了一个新的/d flag，以获得关于输入字符串中每个匹配的开始和索引位置结束的额外信息。

```js
const reg = /test(\d)/g;
const reg2022 = /test(\d)/dg;
const srt = 'test1test2';
const arr = [...str.matchAll(reg)];
const arr2022 = [...str.matchAll(reg2022)];
// arr[0]
// arr2022[0]
```

## 在所有内置的可索引数据上新增.at()方法

> 新增一个新的数组方法，通过给定的索引来获取一个元素。
> 当给定的索引为正数时，这个新方法的行为与使用括号符号的访问相同，但是当我们给定一个负整数的索引时，它就像python的 "负数索引 "一样工作，这意味着at()方法以负整数为索引，从数组的最后一项往后数。
> 所以该方法可以被执行为array.at(-1)，它的行为与array[array.length-1]相同。

```js
const list = [1,2,3,4,5,6];
console.log(list.at(-1)); // 6
console.log(list.at(-2)); // 5
```

## Object.hasOwn(object, property)

> 简单讲就是使用 Object.hasOwn 替代 Object.prototype.hasOwnProperty.call

```js
const person = {name: 'lxm'}
console.log(Object.prototype.hasOwnProperty.call(person, 'name')) // true

console.log(Object.hasOwn(person, 'name')) // true
```

## Error Cause

[proposal-error-cause](https://github.com/tc39/proposal-error-cause) 这一提案，目的主要是为了便捷的传递导致错误的原因，如果不使用这个模块，想要清晰的跨越多个调用栈传递错误上下文信息

```js
sync function doJob() {
  const rawResource = await fetch('//domain/resource-a')
    .catch(err => {
      throw new Error('Download raw resource failed', { cause: err });
    });
  const jobResult = doComputationalHeavyJob(rawResource);
  await fetch('//domain/upload', { method: 'POST', body: jobResult })
    .catch(err => {
      throw new Error('Upload job result failed', { cause: err });
    });
}

try {
  await doJob();
} catch (e) {
  console.log(e);
  console.log('Caused by', e.cause);
}
// Error: Upload job result failed
// Caused by TypeError: Failed to fetch
```