# [Why does useEffect run two times](https://flaviocopes.com/react-useeffect-two-times/)

How to fix the useEffect runs twice problem

React 18 released in March 2022 changed the default behavior of useEffect().

I didn’t even realize it at first, reading the React 18 launch post, buried along a lot of new features.

If your application is behaving strangely after updating to React 18, the default behavior of useEffect changed to run it 2 times.

Just in development mode, but this is the mode everyone builds their application on.

And just in strict mode, but that’s now the default for applications built using Vite, create-react-app or Next.js.

There are reasons for this.

It’s not a problem of your code - it’s how things work now in React.

The only way to disable this behavior is to disable strict mode.

Strict mode is important so this is a temporary workaround until you can fix any issue this change introduced.

In Vite, go to src/main.jsx and remove the <React.StrictMode> wrapper component, from:

```js
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

to:

```js
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <App />
)
```

You can do it in Next.js by adding the option

```js
reactStrictMode: false
```

in your next.config.js file.

In create-react-app you can go in your index.js file and remove the StrictMode higher order component, from:

```js
import React, { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';

const rootElement = document.getElementById('root');
const root = createRoot(rootElement);

root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

to:

```js
import React from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';

const rootElement = document.getElementById('root');
const root = createRoot(rootElement);

root.render(
  <App />
);
```
