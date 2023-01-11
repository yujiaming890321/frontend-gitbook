# 常用 Array api的用法

## forEach

forEach，对数组的每个元素执行一次给定的函数。

```js
const array1 = ['a', 'b', 'c'];
array1.forEach(element => console.log(element));
```

## fill、map

file，用一个固定值填充一个数组中从起始索引到终止索引内的全部元素
map，创建一个新数组，其结果是该数组中的每个元素是调用一次提供的函数后的返回值

```js
const array1 = [1, 2, 3, 4];
// fill with 0 from position 2 until position 4
console.log(array1.fill(0, 2, 4));
// expected output: [1, 2, 0, 0]

// 生成数组
let array = Array(3).fill(0); // [ 0, 0, 0 ]
array.map((_,i) => i); // [ 0, 1, 2 ]
```

## pop、push

pop，删除掉数组的最后一个元素，并返回该元素的值
push，添加到数组末尾，并返回该数组的新长度

```js
let myFish = ["angel", "clown", "mandarin", "surgeon"];
let popped = myFish.pop(); // surgeon
console.log(myFish); // ["angel", "clown", "mandarin"]

myFish.push('cow');
console.log(myFish); // ["angel", "clown", "mandarin", "cow" ]
```

## shift、unshift

shift，删除数组第一个元素，并返回该元素的值
unshift，将一个或多个元素添加到数组的开头，并返回该数组的新长度

```js
const array1 = [1, 2, 3];
const firstElement = array1.shift(); // 1
console.log(array1); // Array [2, 3]

console.log(array1.unshift(4, 5)); // 4
console.log(array1); // Array [4, 5, 2, 3]
```

## keys、values、entries

keys，返回一个新的Array Iterator对象，该对象包含数组中每个索引的键。
values，返回一个新的 Array Iterator 对象，该对象包含数组每个索引的值。
entries，返回一个新的 Array Iterator 对象，该对象包含数组中每个索引的键值对。

```js
const array1 = ['a', 'b', 'c'];
const iterator = array1.keys();
for (const key of iterator) {
  console.log(key); // 0,1,2
}

const iterator1 = array1.values();

for (const value of iterator1) {
  console.log(value); // a,b,c
}

const iterator2 = array1.entries();
console.log(iterator2.next().value);
// expected output: Array [0, "a"]

console.log(iterator2.next().value);
// expected output: Array [1, "b"]
```

## some、every

some，测试一个数组内是不是至少有1个元素通过某个指定函数的测试
every，测试一个数组内的所有元素是否都能通过某个指定函数的测试

```js
const array = [1, 2, 3];
const even = (element) => element % 2 === 0;
console.log(array.some(even)); // true

const array1 = [1, 30, 39, 29, 10, 13];
const isBelowThreshold = (currentValue) => currentValue < 40;
console.log(array1.every(isBelowThreshold)); // true
```

## find、indexOf

find，返回数组中满足提供的测试函数的第一个元素的值
indexOf，返回在数组中可以找到一个给定元素的第一个索引，如果不存在，则返回-1。

```js
const array1 = [5, 12, 8, 130, 44];
const found = array1.find(element => element > 10);
console.log(found); // 12

const index = array1.indexOf(12);
console.log(index); // 1
const index2 = array1.indexOf(1);
console.log(index2); // -1
```

## filter、concat

filter，创建一个新数组, 其包含通过所提供函数实现的测试的所有元素
concat，用于合并两个或多个数组。此方法不会更改现有数组，而是返回一个新数组

```js
const words = ['spray', 'limit', 'elite', 'exuberant', 'destruction', 'present'];
const result = words.filter(word => word.length > 6);
console.log(result); // ["exuberant", "destruction", "present"]

const array1 = ['a', 'b', 'c'];
const array2 = ['d', 'e', 'f'];
const array3 = array1.concat(array2);
console.log(array3); // ["a", "b", "c", "d", "e", "f"]
```

## reduce

reduce，对数组中的每个元素执行一个由您提供的reducer函数(升序执行)，将其结果汇总为单个返回值。

```js
const array1 = [1, 2, 3, 4];
const initialValue = 0;
// 0 + 1 + 2 + 3 + 4
const sumWithInitial = array1.reduce(
  (previousValue, currentValue) => previousValue + currentValue,
  initialValue
);

console.log(sumWithInitial); // 10
```

## flat

flat，会按照一个可指定的深度递归遍历数组，并将所有元素与遍历到的子数组中的元素合并为一个新数组返回。

```js
const arr1 = [0, 1, 2, [3, 4]];
console.log(arr1.flat()); // [0, 1, 2, 3, 4]

const arr2 = [0, 1, 2, [[[3, 4]]]];
console.log(arr2.flat(3)); // [0, 1, 2, 3, 4]
```

## slice

slice，返回一个新的数组对象，这一对象是一个由 begin 和 end 决定的原数组的浅拷贝（包括 begin，不包括end）。原始数组不会被改变。

```js
const animals = ['ant', 'bison', 'camel', 'duck', 'elephant'];
console.log(animals.slice(2)); // ["camel", "duck", "elephant"]
console.log(animals.slice(2, 4)); // ["camel", "duck"]
console.log(animals.slice(1, 5)); // ["bison", "camel", "duck", "elephant"]
console.log(animals.slice(-2)); // ["duck", "elephant"]
```

## sort

sort，用原地算法对数组的元素进行排序，并返回数组。默认排序顺序是在将元素转换为字符串，然后比较它们的UTF-16代码单元值序列时构建的

```js
const months = ['March', 'Jan', 'Feb', 'Dec'];
months.sort();
console.log(months);
// expected output: Array ["Dec", "Feb", "Jan", "March"]

const array1 = [1, 30, 4, 21, 100000];
array1.sort();
console.log(array1);
// expected output: Array [1, 100000, 21, 30, 4]
```

需要注意sort自定义方法，需要返回数字，不能是 boolean

```js
arr.sort((a, b) => {
  if (a > b) {
    return 1
  } else if ((a = b)) {
    return 0
  } else {
    return -1
  }
})
```

## reverse

reverse，法将数组中元素的位置颠倒，并返回该数组。该方法会改变原数组。

```js
const array1 = ['one', 'two', 'three'];
console.log('array1:', array1); // ["one", "two", "three"]
const reversed = array1.reverse();
console.log('reversed:', reversed); // ["three", "two", "one"]
console.log('array1:', array1); // ["three", "two", "one"]
```