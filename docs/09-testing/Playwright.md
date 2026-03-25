# Playwright

## install

```js
pnpm create playwright@latest -- --ct
pnpm i playwright -D
```

## test

\*.spec.ts

```js
import {test, expect} from '@playwright/experimental-ct-vue'
import Counter from './Counter.vue'

test("title", async({mount}) => {
    const component = await mount(Counter)
    // 断言
    await expect(component.getByTestId("count")).toContainText("0")
    // 点击
    await component.getByRole("button", {name: "increase"}).click()
    // 快照
    await expect(component).toHaveScreenshot()
})

// 更新快照
pnpm test-ct --update-snapshots
// trace
pnpm test-ct --trace on
// codegen
npx playwright codegen http://localhost:5175/
```
