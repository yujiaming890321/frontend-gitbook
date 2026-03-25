# bunyan

a simple and fast JSON logging library for node.js services

```js
var bunyan = require('bunyan');
var log = bunyan.createLogger({name: "myapp"});
log.info("hi");
```
