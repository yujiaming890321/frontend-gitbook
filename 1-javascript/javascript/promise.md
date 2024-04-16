# Promise

```javascript
export const promiseAllObject = async <
  O extends Record<string, Promise<any> | any>,
  R extends { [K in keyof O]: Awaited<O[K]> },
>(
  object: O,
): Promise<R> => {
  return zipObject(keys(object), await Promise.all(values(object))) as R;
};

promiseAllObject({a: new Promise(), b: new Promise()})
```
