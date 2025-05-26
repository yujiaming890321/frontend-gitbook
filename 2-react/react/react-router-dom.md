# [@react-router](https://reactrouter.com/home)

```js
route("some/path", "./some/file.tsx"),
  // pattern ^           ^ module file
```

## Component(default)

loader、clientLoader、action、clientAction

```js
import type { Route } from "./+types/route-name";

export async function loader() {
  const items = await fakeDb.getItems();
  return { items };
}

export default function MyRouteComponent({
  loaderData,
  actionData,
  params,
  matches,
}: Route.ComponentProps) {
  return (
    <div>
      <h1>Welcome to My Route with Props!</h1>
      <p>Loader Data: {JSON.stringify(loaderData)}</p>
      <p>Action Data: {JSON.stringify(actionData)}</p>
      <p>Route Parameters: {JSON.stringify(params)}</p>
      <p>Matched Routes: {JSON.stringify(matches)}</p>
    </div>
  );
}
```

## Component route

```js
import { Routes, Route } from "react-router";

function Wizard() {
  return (
    <div>
      <h1>Some Wizard with Steps</h1>
      <Routes>
        <Route index element={<StepOne />} />
        <Route path="step-2" element={<StepTwo />} />
        <Route path="step-3" element={<StepThree />} />
      </Routes>
    </div>
  );
}
```

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

### lazy、suspense

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

## nested route

```js
// parent route
route("dashboard", "./dashboard.tsx", [
    // child routes
    index("./home.tsx"),
    route("settings", "./settings.tsx"),
]),
```

this config creates both "/dashboard" and "/dashboard/settings" URLs.
Child routes are rendered through the <Outlet/> in the parent route.

```js
// dashboard.tsx
import { Outlet } from "react-router";

export default function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      {/* will either be home.tsx or settings.tsx */}
      <Outlet />
    </div>
  );
}
```

## root route

app/root.tsx

## layout route & route prefix & index route

Using layout, layout routes create new nesting for their children, but they don't add any segments to the URL.
Using prefix, you can add a path prefix to a set of routes without needing to introduce a parent route file.

```js
export default [
    // renders into the root.tsx Outlet at /
  index("./home.tsx"),
  layout("./marketing/layout.tsx", [
    index("./marketing/home.tsx"),
    route("contact", "./marketing/contact.tsx"),
  ]),
  ...prefix("projects", [
    index("./projects/home.tsx"),
    layout("./projects/project-layout.tsx", [
      route(":pid", "./projects/project.tsx"),
      route(":pid/edit", "./projects/edit-project.tsx"),
    ]),
  ]),
] satisfies RouteConfig;
```

## dynamic segments & optional segments

```js
//route.ts
route("teams/:teamId", "./team.tsx")

// team.tsx
export async function loader({ params }: Route.LoaderArgs) {
  //                           ^? { teamId: string }
}

export default function Component({
  params,
}: Route.ComponentProps) {
  params.teamId;
  //        ^ string
}

route("c/:categoryId/p/:productId", "./product.tsx")
async function loader({ params }: LoaderArgs) {
  //                    ^? { categoryId: string; productId: string }
}

route(":lang?/categories", "./categories.tsx"),
route("users/:userId/edit?", "./user.tsx");

```

## splats

```js
route("files/*", "./files.tsx"),
export async function loader({ params }: Route.LoaderArgs) {
  // params["*"] will contain the remaining URL after files/
}
const { "*": splat } = params;
```

## file route

```js
import { type RouteConfig } from "@react-router/dev/routes";
import { flatRoutes } from "@react-router/fs-routes";

export default flatRoutes({
  ignoredRouteFiles: ["home.tsx"],
}) satisfies RouteConfig;

app/
├── routes/
│   ├── _index.tsx
│   └── about.tsx
└── root.tsx

URL	Matched Routes
/	app/routes/_index.tsx
/about	app/routes/about.tsx
```

### Dot Delimiter

```js
 app/
├── routes/
│   ├── _index.tsx
│   ├── about.tsx
│   ├── concerts.trending.tsx
│   ├── concerts.salt-lake-city.tsx
│   └── concerts.san-diego.tsx
└── root.tsx

URL	Matched Route
/	app/routes/_index.tsx
/about	app/routes/about.tsx
/concerts/trending	app/routes/concerts.trending.tsx
/concerts/salt-lake-city	app/routes/concerts.salt-lake-city.tsx
/concerts/san-diego	app/routes/concerts.san-diego.tsx
```
