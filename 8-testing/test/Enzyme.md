# Enzyme

- shallow：浅渲染，可以用 simulate 进行交互模拟
- render：静态渲染，需要测试对子组件进行判断
- mount：完全渲染，可以用 simulate 进行交互模拟，需要测试组件的生命周期。

<details>
<summary>点击查看代码</summary>

```javascript
import { expect } from 'chai';
import React from 'react';
import { mount } from 'enzyme';
import { effects } from 'dva/saga';

const { put } = effects;

describe('Banner', function() {
  const Banner = require('../src/components/Banner');

  it('should render correctly', async function() {
    const wrapper = mount(<Banner dispatch={put}/>);
    // wait async request
    await new Promise((resolve) => setTimeout(resolve, 2000));

    expect(wrapper.state('bannerData')).to.have.lengthOf.at.least(1);
    expect(wrapper.find('.slick-list')).to.have.lengthOf.above(1);
  });
});
```

</details>

## simulate(event, mock)

模拟事件，用来触发事件，event 为事件名称，mock 为一个 event object

```javascript
it('can save value and cancel', () => {
   const value = 'edit'
   const {wrapper, props} = setup({
      editable: true
   });
   wrapper.find('input').simulate('change', {target: {value}});
   wrapper.setProps({status: 'save'});
   expect(props.onChange).toBeCalledWith(value); // onChange调用后，参数为 value
})
```

## find(selector)

根据选择器查找节点，selector 可以是 CSS 中的选择器，或者是组件的构造函数，组件的 display name 等

## at(index)

返回一个渲染过的对象

## contains(nodeOrNodes)

当前对象是否包含参数重点 node，参数类型为 react 对象或对象数组

## text()

返回当前组件的文本内容

## html()

返回当前组件的 HTML 代码形式

## props()

返回`根组件`的所有属性
