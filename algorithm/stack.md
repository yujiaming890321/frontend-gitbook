# stack 栈

```js
class Stack {
  items;

  constructor() {
    this.items = [];
  }

  push: (item: any) => void = (item) => {
    this.items.push(item);
  }; 

  pop: () => any = () => {
    return this.items.pop();
  }; 

  peek: () => any = () => {
    return this.items[this.items.length - 1];
  }; 

  isEmpty: () => boolean = () => {
    return this.items.length === 0;
  };

  size: () => number = () => {
    return this.items.length;
  };

  clear: () => void = () => {
    this.items = [];
  };
}
```
