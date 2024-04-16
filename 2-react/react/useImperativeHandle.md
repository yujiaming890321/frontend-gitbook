# useImperativeHandle

## 子传父实例

```js
// 子组件
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

// 父组件
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
