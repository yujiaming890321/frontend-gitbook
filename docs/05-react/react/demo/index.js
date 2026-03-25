// 数据
// let count = 0
const queue = []
let index = 0
const useState = (initialState) => {
    queue.push(initialState)

    const update = (state) => {
        // Q：为什么在react中，hooks不能写在判断里？
        // A：因为hooks更新是一个压栈的过程
        queue.push(state)
        index++
    }
    return [queue[index], update]
}
const [count, setCount] = useState(0)

// 事件
window.addEventListener(
    'click',
    () => {
        // count++
        setCount(queue[index] + 1)
        // render()
    },
    false
)

// 渲染
const render = () => {
    console.log('🚀 ~ render')
    // document.body.innerHTML = count
    document.body.innerHTML = queue[index]
}
render()

// reconciler
let prevCount = count
const reconcile = () => {
    // if (prevCount != count) {
    if (prevCount != queue[index]) {
        render()
        prevCount = queue[index]
    }
}

// scheduler
const workloop = () => {
    // render();
    reconcile()
    requestIdleCallback(() => {
        workloop()
    })
}
workloop()
