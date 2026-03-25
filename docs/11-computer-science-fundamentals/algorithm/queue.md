# Queue 队列

```js
class Queue {
  items;

  constructor() {
    this.items = [];
  }

  enqueue: (element: any) => void = (element: any) => {
    return this.items.push(element);
  };

  dequeue: () => any = () => {
    return this.items.shift();
  };

  front: () => any = () => {
    return this.items[0];
  };

  isEmpty: () => boolean = () => {
    return this.items.length === 0;
  };

  size: () => number = () => {
    return this.items.length;
  };
}

```
