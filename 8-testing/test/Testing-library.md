### fireEvent、userEvent

fireEvent.click() 只会发出 onClick 而 userEvent.click() 会发出所有类型的事件

[fireEvent 源码](https://github.com/testing-library/react-testing-library/blob/v12.1.4/src/fire-event.js)

> react-testing-library's version of fireEvent will call dom-testing-library's version of fireEvent.

react 测试库的 fireEvent 版本将调用 dom 测试库的 fireEvent 版本。

> The reason we make this distinction however is because we have a few extra events that work a bit differently.

然而，我们之所以做出这种区分，是因为我们有一些额外的事件，它们的工作方式有点不同。

> React event system tracks native mouseOver/mouseOut events for running onMouseEnter/onMouseLeave handlers

React 事件系统跟踪运行 onMouseCenter/onMouseLeave 处理程序的本机 mouseOver/mouseOut 事件

@link https://github.com/facebook/react/blob/b87aabdfe1b7461e7331abb3601d9e6bb27544bc/packages/react-dom/src/events/EnterLeaveEventPlugin.js#L24-L31

[userEvent 源码](https://github.com/testing-library/user-event/blob/v13.5.0/src/click.ts)

function clickLabel

> clicking the label will trigger a click of the label.control however, it will not focus the label.control so we have to do it ourselves.

点击标签会触发点击`label.control`，但不会聚焦`label.control`，所以我们必须自己做。
