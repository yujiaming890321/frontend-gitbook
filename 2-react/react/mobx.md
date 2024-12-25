# mobx

## 无状态管理，monorepo 多技术栈的场景可以提取公共逻辑，使用 mobx 做状态管理

## decorator 装饰器

```js
function decoratorName(target, key, descriptor){
    //...
}

Object.defineProperty(Person.pretotype, 'fullname', {
    get: funciont() {
        return this.firstName + ' ' + this.lastName
    }
})
```

demo:

```js
import { observable, autorun } from 'mobx'

const input = document.getElementById('text-input')
const textDisplay = document.getElementById('text-display')
const loudDisplay = document.getElementById('text-display-upper')

const text = observable({
    value: 'Hello world',
    get uppercase() {
        return this.value.toUpperCase()
    },
})

input.addEventListener('keyup', (event) => {
    text.value = event.target.value
})

autorun(() => {
    textDisplay.textContent = text.value
    loudDisplay.textContent = text.uppercase
})
```

## observable 观察者

```js
const onChange = (oldValue, newValue) ={
    // Tell Mobx that this value has changed.
}

const observable = (value) => {
    return {
        get() {return value}
        set(newValue) {
            onChange(this.get(), newValue)
            value = newValue
        }
    }
}

const extendObservable = (target, source) => {
    source.keys().forEach(key => {
        const wrappedInObservable = observable(source[key])
        Object.defineProperty(target, key, {
            set: value.set
            get: value.get
        })
    })
}
```

demo:

```js
import { decorate, observable, autorun } from 'mobx'
import { observer } from 'mobx-react'

class Count {
    value = 0
    increment = () => {
        this.value++
    }
    decrement = () => {
        this.value--
    }
}

decorate(Count, {
    value: observable,
})
```
