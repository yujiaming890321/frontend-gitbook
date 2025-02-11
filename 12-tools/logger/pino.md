# pino

Very low overhead Node.js logger.

```js
import pino from 'pino'
import { multistream } from 'pino-multi-stream' // one log write to multi platform

class Logger {
  private readonly enableSplunkEnv = isProductionEnv() || isStageEnv()
  private readonly logger = pino()

  private readonly log = (content: object, isError: boolean = false): void => {
    this.logger.info(content)
  }
}
```
