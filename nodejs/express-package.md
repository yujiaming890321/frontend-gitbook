# express 相关插件

## nodemon

nodemon is a tool that helps develop Node.js based applications by automatically restarting the node application when file changes in the directory are detected.

```js
nodemon ./server.js localhost 8080
```

## body-parser

Node.js body parsing middleware.

Parse incoming request bodies in a middleware before your handlers, available under the req.body property.

```js
var express = require('express')
var bodyParser = require('body-parser')

var app = express()
app.use(bodyParser.json({ limit: '32kb' }))
```

## cookie-parser

Parse Cookie header and populate req.cookies with an object keyed by the cookie names. 
Optionally you may enable signed cookie support by passing a secret string, which assigns req.secret so it may be used by other middleware.

```js
var express = require('express')
var cookieParser = require('cookie-parser')

var app = express()
app.use(cookieParser())

app.get('/', function (req, res) {
  // Cookies that have not been signed
  console.log('Cookies: ', req.cookies)

  // Cookies that have been signed
  console.log('Signed Cookies: ', req.signedCookies)
})
```

## express-pprof-middleware

Express middleware that exposes pprof endpoints for easy profiling

```js
const pprof = require('express-pprof-middleware');

const app = express();
app.use(pprof);
```
