# graphql-yoga

```js
import { GraphQLSchema, GraphQLObjectType } from 'graphql';
import { applyMiddleware } from 'graphql-middleware';
import { createYoga } from 'graphql-yoga';

const businessResolver = (_, args, context) => {
  const { txId } = context;
  const { id } = args;
  return async () => {
    //   ...
    return true
  }
};

const BusinessQueryType = new GraphQLObjectType({
  name: 'BusinessQueryType',
  fields: {
    business: {
      type: GraphQLBoolean,
      resolve: businessResolver,
    },
  },
});

const query = new GraphQLObjectType({
  name: 'Query',
  fields: {
    business: {
      type: BusinessQueryType,
      resolve: () => ({}),
    },
  },
});

const schema = new GraphQLSchema({
  query,
});

const graphQLYoga = createYoga({
  schema: applyMiddleware(schema, permissions),
  context: contextConfig,
  graphiql: !isProduction,
  graphqlEndpoint: '/graphql',
  plugins,
});
```
