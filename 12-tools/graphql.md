# Graphql

## Query

### server

schema 定义了所有可能的类型和操作，并且充当客户端和服务器之间的契约

!非空

root 是一个用于处理客户端请求的实际对象，它包含了所有的处理函数

```js
const schema = buildSchema(`
  type Query {
    hello: String!
  }
`)
const root = {
    hello: () => {
        return 'hello world!'
    },
}

app.use(
    '/graphql',
    graphqlHTTP({
        schema,
        root,
        graphiql: true,
    })
)
```

#### schema

```js
const schema = new GraphQLSchema({
    query: new GraphQLObjectType({
        name: 'Query',
        fields: {
            hello: {
                type: GraphQLString,
                resolve: () => 'Hello world!',
            },
        },
    }),
})
```

### client

```js
let query = /* GraphQL */ `
    query RollDice($dice: Int!, $sides: Int) {
        rollDice(numDice: $dice, numSides: $sides)
    }
`

fetch('/graphql', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
    },
    body: JSON.stringify({
        query,
        variables: { dice, sides },
    }),
})
```

## Mutation

mutation {}
