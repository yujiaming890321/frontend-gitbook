# test

AAA 模式：

- 编排（Arrange）
- 执行（Act）
- 断言（Assert）

## 测试用例要面向特性而不是面向实现

测试用例应当保障的永远是对外文档中你承诺给用户的所有特性！

## 你只需要测自己的代码，默认依赖的都是安全的

```javascript
function multiplyThenAdd(a, b) {
  return _.add(a*b, b)
}
const add = jest.spyOn(_, 'add') // 将 loadsh 的 add 方法 mock 掉

multiplyThenAdd(1, 2)

// 表面上只是在获取 add 的调用参数，实际上还确保了 multiplyThenAdd 被调用后一定会调用 add。
// 因为没被调用的话又从何获取调用参数呢？
const [arg1, arg2] = add.mock.calls[0]

expect(arg1).toBe(1 * 2) // 确保参数相乘
expect(arg2).toBe(2) // 确保参数相加
```

测试尽量别依赖 UI 行为、大多数时候确保相应的 UI 触发函数被调用过即可，UI 的变更请信任你依赖的组件会保障。

## 像写文档那样去写用例

```javascript
describe('Form', () => {
  describe('Props', () => {
    test('colon 会控制 label 后面的冒号是否显示', () => {})
    test('component 设置 Form 渲染元素，为 false 则不创建 DOM 节点', () => {})
    // ...
  })
  
  describe('Instance', () => {
    test('getFieldError 可获取对应字段名的错误信息', () => {})
    test('getFieldInstance 获取对应字段实例', () => {})
    // ...
  })
})
```

[Jest](https://jestjs.io/docs/jest-object)

[Enzyme](https://enzymejs.github.io/enzyme/)

[Testing-library](https://testing-library.com/docs/)

[Sinon](https://sinonjs.org/)

## 思考

Testing-library 如何测试 Class 组件 componentDidUpdate 生命周期
解：使用 rerender 修改 props

## recommend

[fix the not wrapped in act warning](https://kentcdodds.com/blog/fix-the-not-wrapped-in-act-warning)