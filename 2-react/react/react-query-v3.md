# [react-query v3](https://tanstack.com/query/v3)

在使用 Hooks 写组件时，发起异步请求时，不仅需要管理请求状态，而且还需要处理异步数据，为此要多写几个 useState/useEffect 来控制。
而 react-query 正是为此而生，可以方便的管理服务端的状态

## the 5 O'clock rule

the level of abstraction for solving a problem will bubble up until it allows the average developer to stop thinking about the problem

v=f(s), view = function(state)

### 1. basic question

```js
useEffect(() => {
    let igore = false
    const handleFetchPokemon = async () => {
        const res = await fetch(`https://pokeapi.co/api/v2/pokemon/${id}`)
        if (igore) return // change id randomly will not effect the data
        const json = res.json()
        setPokemon(json)
    }
    handleFetchPokemon()
    return () => {
        igore = true
    }
}, [id])
```

### 2. disappear observability

```js
const useQuery = (url) => {
    useEffect(() => {
        let igore = false
        const handleFetchPokemon = async () => {
            const res = await fetch(url)
            if (igore) return // change id randomly will not effect the data
            const json = res.json()
            setPokemon(json)
        }
        handleFetchPokemon()
        return () => {
            igore = true
        }
    }, [id])
}
```

## query fundamental: Provider、Client

```js
cache = new Map()
```

1. how does it know what data to use?

2. how does it know where to get the data from?

Rules: the queryKey must be globally unique, the queryFn must return a Promise

provider cache and client config to children

Client manages queries and cache

```js
import { QueryClient, QueryClientProvider } from 'react-query'

const queryClient = new QueryClient()

function APP() {
    return (
        <QueryClientProvider client={queryClient}>
            <div />
        </QueryClientProvider>
    )
}
```

## Queries

A query is a declarative dependency on an asynchronous source of data that is tied to a `unique key`. A query can be used with any Promise based method (including GET and POST methods) to fetch data from a server. If your method modifies data on the server, we recommend using `Mutations` instead.

To subscribe to a query in your components or custom hooks, call the useQuery hook with at least:

-   A `unique key` for the query
-   A function that returns a promise that:
    -   Resolves the data, or
    -   Throws an error
-   re-try three times by default

```js
import { useQuery } from 'react-query'

function App() {
    const info = useQuery('todos', fetchTodoList)
}
```

The result object contains a few very important states you'll need to be aware of to be productive. A query can only be in one of the following states at any given moment:

-   `isLoading` or `status === 'loading'` - The query has no data and is currently fetching
-   `isError` or `status === 'error'` - The query encountered an error
-   `isSuccess` or `status === 'success'` - The query was successful and data is available
-   `isIdle` or `status === 'idle'` - The query is currently disabled (you'll learn more about this in a bit)

Beyond those primary states, more information is available depending on the state of the query:

-   `error` - If the query is in an isError state, the error is available via the error property.
-   `data` - If the query is in a success state, the data is available via the data property.
-   `isFetching` - In any state, if the query is fetching at any time (including background refetching) isFetching will be true.

For most queries, it's usually sufficient to check for the isLoading state, then the isError state, then finally, assume that the data is available and render the successful state:

```js
function Todos() {
    const { isLoading, isError, data, error } = useQuery('todos', fetchTodoList)

    if (isLoading) {
        return <span>Loading...</span>
    }

    if (isError) {
        return <span>Error: {error.message}</span>
    }

    // We can assume by this point that `isSuccess === true`
    return (
        <ul>
            {data.map((todo) => (
                <li key={todo.id}>{todo.title}</li>
            ))}
        </ul>
    )
}
```

### stale timet vs cache time

data refetch only trigger for stale data.
stale time is for re-fetching.
cache time is for re-used.

### Array as Query key

["key", id]

## PreQuery

```js
import { QueryClient, QueryClientProvider } from 'react-query'

const queryClient = new QueryClient()

queryClient.prefetchQuery(['key', id], fetchTodoList)
```

## isLoading vs isFetching

Even if there is data in the cache, isLoading is false.
Even if there is data in the cache, isFetching is still true.

## Mutations

only run once.

Unlike queries, mutations are typically used to create/update/delete data or perform server side-effects. For this purpose, React Query exports a `useMutation` hook.

```js
function App() {
    const mutation = useMutation((newTodo) => {
        return axios.post('/todos', newTodo)
    })

    return (
        <div>
            {mutation.isLoading ? (
                'Adding todo...'
            ) : (
                <>
                    {mutation.isError ? (
                        <div>An error occurred: {mutation.error.message}</div>
                    ) : null}

                    {mutation.isSuccess ? <div>Todo added!</div> : null}

                    <button
                        onClick={() => {
                            mutation.mutate({
                                id: new Date(),
                                title: 'Do Laundry',
                            })
                        }}
                    >
                        Create Todo
                    </button>
                </>
            )}
        </div>
    )
}
```

A mutation can only be in one of the following states at any given moment:

-   `isIdle` or `status === 'idle'` - The mutation is currently idle or in a fresh/reset state
-   `isLoading` or `status === 'loading'` - The mutation is currently running
-   `isError` or `status === 'error'` - The mutation encountered an error
-   `isSuccess` or `status === 'success'` - The mutation was successful and mutation data is available

Beyond those primary states, more information is available depending on the state of the mutation:

-   `error` - If the mutation is in an error state, the error is available via the error property.
-   `data` - If the mutation is in a success state, the data is available via the data property.

In the example above, you also saw that you can pass variables to your mutations function by calling the `mutate` function with a **single variable or object**.

```js
const CreateTodo = () => {
    const mutation = useMutation((event) => {
        event.preventDefault()
        return fetch('/api', new FormData(event.target))
    })

    return <form onSubmit={mutation.mutate}>...</form>
}
```

### Reset

It's sometimes the case that you need to clear the error or data of a mutation request.

```js
const CreateTodo = () => {
    const [title, setTitle] = useState('')
    const mutation = useMutation(createTodo)

    const onCreateTodo = (e) => {
        e.preventDefault()
        mutation.mutate({ title })
    }

    return (
        <form onSubmit={onCreateTodo}>
            {mutation.error && (
                <h5 onClick={() => mutation.reset()}>{mutation.error}</h5>
            )}
            <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
            />
            <br />
            <button type="submit">Create Todo</button>
        </form>
    )
}
```

### Effects

`useMutation` comes with some helper options that allow quick and easy side-effects at any stage during the mutation lifecycle.

```js
useMutation(addTodo, {
    onMutate: (variables) => {
        // A mutation is about to happen!

        // Optionally return a context containing data to use when for example rolling back
        return { id: 1 }
    },
    onError: (error, variables, context) => {
        // An error happened!
        console.log(`rolling back optimistic update with id ${context.id}`)
    },
    onSuccess: (data, variables, context) => {
        // Boom baby!
    },
    onSettled: (data, error, variables, context) => {
        // Error or success... doesn't matter!
    },
})
```
