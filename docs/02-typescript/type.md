# type

## Omit & Pick

Omit = except, Pick = include

## [extends](https://www.typescriptlang.org/docs/handbook/2/generics.html#generic-constraints)

继承的对象一定有指定对象的属性

## [Arrays](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#arrays)

Note that [number] is a different thing; refer to the section on Tuples.

```js
type a = [1,2,3];
type b = a[number]; // 是union，1 | 2 | 3
```

## [keyof](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)

```js
type TupleToObject<T extends readonly any[]> = {
  [P in K]: P; // 是index索引，0123
}
type MyPick<T, K extends keyof T> = {
   [P in K]: T[P];
}
```

T = ['title', 'completed', 'invalid']
K 是 T 的其中一个 key，比如 'invalid'

## [readonly](https://www.typescriptlang.org/docs/handbook/utility-types.html#readonlytype)

## [infer & spread](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#explicit-types)

infer 假设， spread 展开...

```js
type a = [1,2,3]
type b = a extends [infer First, ...infer rest] ? First : never // b = 1
```

## as const

as const = readonly

```js
const a = [1,2,3] as const
const b = [1,2,3]
type a1 = typeof a // readonly [1, 2, 3]
type b1 = typeof b // number[]
```

## PromiseLike

## [Strict Null Checks](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#any-unknown-object-void-undefined-null-and-never-assignability)

严格判断 Null 是否为 true
