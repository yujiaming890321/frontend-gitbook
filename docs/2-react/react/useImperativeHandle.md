# useImperativeHandle

## [https://react.dev/learn/manipulating-the-dom-with-refs#accessing-another-components-dom-nodes](https://react.dev/learn/manipulating-the-dom-with-refs#accessing-another-components-dom-nodes)

## 子传父实例

```js
// 子组件，使用forwardRef封装，使用useImperativeHandle暴露封装的方法
function FancyInputFn(props, ref) {
  const inputRef = useRef();
  useImperativeHandle(ref, () => ({
    focus: () => {
      inputRef.current.focus();
    }
  }));
  return <input ref={inputRef} ... />;
}
FancyInput = forwardRef(FancyInputFn);

// 父组件，通过ref使用子组件方法
const inputRef = useRef(null);

function handleClick() {
  inputRef.current.focus();
}

return (
  <>
    <button onClick={handleClick}>
      Write a comment
    </button>
    <FancyInput ref={inputRef} />
  </>
);
```
