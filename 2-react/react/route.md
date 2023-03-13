# route

```js
// route.js
{
    path: "/appointment/:action/:uId", 
    component: dynamic({ loader: () => import('./Appointment') })
},

import { useEffect, useState } from 'react';
import { Loader } from '../loadingComponent';
function timeoutDelay (time) {
    return new Promise(resolve => {
        setTimeout(resolve, time);
    });
}
const dynamic = ( { loader, Loading = Loader, delay = 300 } ) => {
    return (props) => {
        const [ Component, setComponent ] = useState(null);
        const [ loadingEnabled, setLoadingEnabled ] = useState(false);
        useEffect(async () => {
            const timer = setTimeout(() => {
                setLoadingEnabled(true);
            }, delay);
            if (process.env.NODE_ENV === 'development') { 
                const num = Math.round(Math.random() * 600);
                await timeoutDelay(num);
            }
            loader().then(res => {
                clearTimeout(timer);
                const LoadedComponent = res.default;
                setComponent(<LoadedComponent {...props} />);
            });
        }, []);
        if (!Component && loadingEnabled) {
            return <Loading show />;
        }
        return <>{Component}</>;
    };
};
export default dynamic;

// Appoint.js
import { useParams } from "react-router-dom";
const Appointment = () => {
    const { uId, action } = useParams();
}
```

## lazy、suspense

```js
import React, { Suspense } from 'react';
const OtherComponent = React.lazy(() => import('./OtherComponent'));
const AnotherComponent = React.lazy(() => import('./AnotherComponent'));
function MyComponent() {
    return (
        <div>
            <Suspense fallback={<div>Loading...</div>}>
                <section>
                    <OtherComponent />
                    <AnotherComponent />
                </section>
            </Suspense>
        </div>
    );
}
```
