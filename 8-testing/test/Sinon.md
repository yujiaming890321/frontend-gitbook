# Sinon

Sinon 是用来辅助我们进行前端测试的，在我们的代码需要与其他系统或者函数对接时，它可以模拟这些场景，从而使我们测试的时候不再依赖这些场景。

Sinon 有主要有三个方法辅助我们进行测试：

- spy
- stub
- mock

## [spy](https://sinonjs.org/releases/v13/spies/)

> A test spy is a function that records arguments, return value, the value of this and exception thrown (if any) for all its calls. There are two types of spies: Some are anonymous functions, while others wrap methods that already exist in the system under test.

spy 生成一个间谍函数，它会记录下函数调用的参数，返回值，this 的值，以及抛出的异常。

> A spy call is an object representation of an individual call to a spied function, which could be a fake, spy, stub or mock method.

```
describe('测试Once函数', function () {
  it('传入Once的函数会被调用', function () {
    var callback = sinon.spy();
    var proxy = once(callback);

    proxy();

    assert(callback.called);
  });

  it('对原有函数的spy封装，可以监听原有函数的调用情况', function () {
    const obj={
        func:()=>{
            return 1+1
        }
    }
    sinon.spy(obj,'func')

    obj.func(3);

    assert(obj.func.calledOnce)
    assert.equal(obj.func.getCall(0).args[0], 3);
  });
})
```

## [Stub](https://sinonjs.org/releases/v13/stubs/)

> Test stubs are functions (spies) with pre-programmed behavior.
> They support the full test spy API in addition to methods which can be used to alter the stub’s behavior.
> As spies, stubs can be either anonymous, or wrap existing functions. When wrapping an existing function with a stub, the original function is not called.

stubs 是具有预编程行为的函数。

stubs 支持完整的 spy API，还可以用来改变函数的行为。

stubs 可以是匿名的，也可以是包装现有函数的。用 stubs 包装现有函数时，不会调用原始函数。

### When to use stubs

    1. Control a method’s behavior from a test to force the code down a specific path. Examples include forcing a method to throw an error in order to test error handling.

    从测试中控制方法的行为，以强制代码沿着特定路径运行。例如，为了测试错误处理，强制方法抛出错误。

    2. When you want to prevent a specific method from being called directly (possibly because it triggers undesired behavior, such as a XMLHttpRequest or similar).

    当您希望防止直接调用特定方法时（可能是因为它触发了不希望的行为，例如XMLHttpRequest或类似行为）。

```
it('对原有函数的stub封装，可以监听原有函数的调用情况,以及模拟返回', function () {
    const obj={
        func:()=>{
           console.info(1)
        }
    }
    sinon.stub(obj,'func').returns(42)

    const result = obj.func(3); // 原函数func的内容确实没有被执行，因为没有打印1。

    assert(obj.func.calledOnce)
    assert.equal(obj.func.getCall(0).args[0], 3);
    assert.equal(result, 43);
});
```

## [Mock](https://sinonjs.org/releases/v13/mocks/)

> Mocks (and mock expectations) are fake methods (like spies) with pre-programmed behavior (like stubs) as well as pre-programmed expectations.
> A mock will fail your test if it is not used as expected.

Mocks 是 stubs 和 spy 的集合。

如果未按预期使用，模拟将无法通过测试。

### When to use mocks?

Mocks should only be used for the method under test. In every unit test, there should be one unit under test.

模拟只能用于测试中的方法。在每个单元测试中，都应该有一个单元在测试中。

If you want to control how your unit is being used and like stating expectations upfront (as opposed to asserting after the fact), use a mock.

如果你想控制你的单元是如何被使用的，并且喜欢预先陈述期望（而不是事后断言），可以使用模拟。

### When to not use mocks?

Mocks come with built-in expectations that may fail your test.

Mocks 带有内置的预期，可能会让你的测试失败。

Thus, they enforce implementation details. The rule of thumb is: if you wouldn’t add an assertion for some specific call, don’t mock it. Use a stub instead.

因此，它们强制执行实施细节。经验法则是：如果你不想为某个特定的方法调用添加断言，改用 stub 。

In general you should have no more than one mock (possibly with several expectations) in a single test.

一般来说，在一次测试中，你不应该有超过一个 mock（可能有几个期望）。

Expectations implement both the spies and stubs APIs.

期望实现 spy 和 stubs API。
