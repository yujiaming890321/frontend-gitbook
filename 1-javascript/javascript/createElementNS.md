# createElementNS 创建一个命名空间

```js
    static setAttributes(element, attributes) {
      Object.entries(attributes).forEach((args) => element.setAttribute(...args));
    }

    const buttonArrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    buttonArrow.classList.add('icon', 'right');
    setAttributes(buttonArrow, {
      viewBox: '0 0 30 30',
      xmlns: 'http://www.w3.org/2000/svg',
    });
    const buttonArrowPath = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'path'
    );
    setAttributes(buttonArrowPath, {
      stroke: '#171a20',
      'stroke-width': '2',
      d: 'M10.5 17.5l4.5-4 4.5 4',
      fill: 'none',
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      transform: 'rotate(270 15 15)',
    });
    buttonArrow.append(buttonArrowPath);
    button.append(buttonArrow);

    <button>
        <svg class="icon right" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
            <path stroke="#171a20" stroke-width="2" d="M10.5 17.5l4.5-4 4.5 4" fill="none" stroke-linecap="round" stroke-linejoin="round" transform="rotate(270 15 15)"></path>
        </svg>
    </button>
```
