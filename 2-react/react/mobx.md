# mobx

创建可以被观察的对象，创建有观察能力的组件

## 无状态管理，monorepo 多技术栈的场景可以提取公共逻辑，使用 mobx 做状态管理

## decorator 装饰器

```js
function decoratorName(target, key, descriptor){
    //...
}

Object.defineProperty(Person.pretotype, 'fullName', {
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

_if you add properties to an object after you pass it to observable(), those new properties will not be observed._
use a Map(), if you're going to be adding keys later on.

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

```js
import { action, observable, computed } from 'mobx'

class PizzaCalculator {
    @observable number = 0
    @observable slicesPerPerson = 2
    @observable slicesPerPie = 8

    @computed get slicesNeeded() {
        return this.number * this.slicesPerPerson
    }
    @computed get pieNeeded() {
        return Math.ceil(this.slicesNeeded / this.slicesPerPie)
    }

    @action addGuest() {
        this.number++
    }
}
```

## mobx-react

```js
// index.ts
import { Provider} from 'mobx-react'

ReactDom.render(<Provider itemStore={store}><App /></Provider>)

// app.ts
import { inject, observer } from 'mobx-react'

const App = () => {
    const PackedItems = inject('itemList')(
        observer(({itemList}) => {
            return <Items title="Packed items" items={itemList.packedItems} />
        })
    )

    return (
        <PackedItems />
    )
}

// item.ts
import { inject } from 'mobx-react'

@inject('itemList')
const NewItem = ({ itemList }) => {
    return
}
```
