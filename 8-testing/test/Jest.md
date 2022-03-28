# Jest mock

[when to use jest.fn, jest.mock or jest.spyOn](https://jestjs.io/docs/mock-functions)

- Use fn when mocking a function
- Use mock when mocking a module
- Use spyOn when you want to observe things about a real module or function

jest.fn creates Jest spy with no implementation.
jest.spyOn replaces a method or property accessor with Jest spy, which implementation defaults to original one and can be changed to anything, including a stub.

```
jest.spyOn(Date, 'now').mockImplementation(...);
```

%stmts 是语句覆盖率（statement coverage）
%Branch 逻辑分支覆盖率（branch coverage）
%Funcs 函数覆盖率（function coverage）
%Lines 行覆盖率（line coverage）

## jest.fn(implementation)

[jest-object](https://jestjs.io/docs/jest-object)、[mock-function-api](https://jestjs.io/docs/mock-function-api)中查找

返回一个全新没有使用过的 mock function，这个 function 在被调用的时候会记录很多和函数调用有关的信息，是创建 Mock 函数最简单的方式，如果没有定义函数内部的实现，jest.fn()会返回 undefined 作为返回值。

<details>
<summary>点击查看代码</summary>

```
describe('测试jest.fn()调用', () => {
  let mockFn = jest.fn();
  let result = mockFn(1, 2, 3);

  // 断言 mockFn 的执行后返回 undefined
  expect(result).toBeUndefined();
  // 断言 mockFn 被调用
  expect(mockFn).toBeCalled();
  // 断言 mockFn 被调用了一次
  expect(mockFn).toBeCalledTimes(1);
  // 断言 mockFn 传入的参数为 1, 2, 3
  expect(mockFn).toHaveBeenCalledWith(1, 2, 3);
})

```

</details>

jest.fn()所创建的 Mock 函数还可以设置返回值

<details>
<summary>点击查看代码</summary>

```

describe('测试 jest.fn()返回固定值', () => {
  let mockFn = jest.fn().mockReturnValue('default');
  // 断言 mockFn 执行后返回值为 default
  expect(mockFn()).toBe('default');
})

test('测试 jest.fn()内部实现', () => {
  let mockFn = jest.fn((num1, num2) => {
  return num1 \* num2;
})
// 断言 mockFn 执行后返回 100
expect(mockFn(10, 10)).toBe(100);
})

```

</details>

### mockReturnValue()

模拟返回结果。指定返回内容
函数内的参数就是要 返回的值

```

const func = jest.fn()
func.mockReturnValue('dell')
// func 函数调用，return 'dell'

```

### mockReturnValueOnce()()

mockReturnValue 执行返回多次，mockReturnValueOnce 只会执行返回一次

```

const func = jest.fn()
func.mockReturnValueOnce('dell')

```

### mockImplementation()()

可以理解为 mockReturnValue()的底层写法
可以在方法内书写过程

```

const func = jest.fn()
func.mockImplementation(() => {
    return 'dell'
})

```

## jest.mock(moduleName, factory, options)

用来 mock 一些模块或者文件

## jest.spyOn(object, methodName)

返回一个 mock function，和 jest.fn 相似，但是能够追踪 object[methodName]的调用信息，类似 Sinon

## [expect.objectContaining(object)](https://jestjs.io/zh-Hans/docs/expect#expectobjectcontainingobject)

预期返回一个 object 格式的对象

```
 expect(onPress).toEqual(
    // { x: number, y: number }
    expect.objectContaining({
      x: expect.any(Number),
      y: expect.any(Number),
    }),
  );
```
