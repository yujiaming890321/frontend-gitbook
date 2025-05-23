# redux-observable

## setup

```js
// app
import { createStore, applyMiddleware } from 'redux'
import { createEpicMiddleware } from 'redux-observable'
import rootEpic from './fetch-epic'
import rootReducer from './reducer'

const epicMiddleware = createEpicMiddleware()

const store = createStore(rootReducer, applyMiddleware(epicMiddleware))

epicMiddleware.run(rootEpic)

// fetch-epic
import { ajax } from 'rxjs/ajax'
import { ofType } from 'redux-observable'
import { map, mergeMap, tap } from 'rxjs/operators'
import { FETCH_CHARACTERS, fecthCharactersFulfilled } from 'actions'

const fecthCharactersEpic = (action$) => {
    return action$.pipe(
        ofType(FETCH_CHARACTERS),
        mergeMap((action) =>
            ajax.getJSON(ENDPOINT + action.payload.searchTerm)
        ).pipe(
            tap((value) => console.log(value)),
            map((response) => fecthCharactersFulfilled(response.result)),
            takeUntil(
                action$.pipe(
                    tap((value) => console.log('Cancelling!')),
                    ofType(FETCH_CHARACTERS)
                )
            )
        )
    )
}

export default fecthCharactersEpic
```
