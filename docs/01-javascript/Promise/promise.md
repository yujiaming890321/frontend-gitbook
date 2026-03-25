# Promise

## 执行顺序

    1. Promise 方法体里会先执行，再执行 resolve、reject
    2. 执行 resolve、reject 后会执行 then（如果是reject并且有catch方法，then不执行）
    3. then/catch return的结果是下一个then的输入

## Promise.reject('a').catch 可理解为同步方法
