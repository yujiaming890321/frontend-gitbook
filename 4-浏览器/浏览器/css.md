# css

## 转大写

```css
text-transform: uppercase;
```

## box-shadow

语法：box-shadow: h-shadow v-shadow blur spread color inset;
h-shadow	必需的。水平阴影的位置。允许负值
v-shadow	必需的。垂直阴影的位置。允许负值
blur	可选。模糊距离
spread	可选。阴影的大小
color	可选。阴影的颜色。在CSS颜色值寻找颜色值的完整列表
inset	可选。从外层的阴影（开始时）改变阴影内侧阴影

例子：https://blog.sentry.io/

```js
box-shadow: 0 2px 0 rgb(54 45 89 / 15%), -0.1875rem -0.1875rem 0 0.1875rem #f2b712, 0 0 0 0.375rem #e1567c;
```

## 画梯形

```css
// 梯形朝向哪个方向，哪个方向就是0
border-left: 20px solid transparent;
border-right: 20px solid transparent;
border-bottom: 20px solid red;
border-top: 0;
```