# ErrorBoundary

```js
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    // 在子组件抛出错误后，更新 state 以显示降级 UI。
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // 在此上报错误到监控系统（如 Sentry）
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>页面渲染异常，请尝试刷新</h1>;
    }
    return this.props.children;
  }
}

// 使用方式
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

PureComponent 是 React.Component 的优化版本，通过浅比较 props/state 减少渲染次数。

虽然技术上可以用 PureComponent 实现 Error Boundary，但不推荐，因为：

- 性能优化无关：Error Boundary 通常不需要频繁重新渲染。
- 潜在问题：浅比较可能阻止错误状态更新后的渲染。

函数组件无法使用 getDerivedStateFromError 或 componentDidCatch