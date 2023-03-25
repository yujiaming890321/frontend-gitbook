# nodejs

## [winston](https://www.npmjs.com/package/winston)

A logger for just about everything.

```js
import { createLogger, format, transports } from 'winston';

const { combine, timestamp, printf, label } = format;

const log = createLogger({
    format: combine(
    timestamp(),
    label({ label: uniqid() }),
    printf((error) => {
        return `Timestamp: ${error.timestamp} Level: ${error.level} Message: ${error.message}`;
    }),
    ),
    transports: [new transports.Console()],
});
```

## nodejs Performance Profiling

We are using Clinic.js and autocannon to profile.

For autocannon commands, check https://github.com/mcollina/autocannon#command-line

Tip: If you installed clinic and autocannon globally on your machine by npm install --global clinic autocannon, you can run scripts like above directly.

### Clinic.js

To learn more about Clinic.js and how to read the chart, you can check at

Clinic.js Bubbleprof: https://clinicjs.org/documentation/bubbleprof/
Clinic.js Doctor: https://clinicjs.org/documentation/doctor/
Clinic.js Flame: https://clinicjs.org/documentation/flame/
