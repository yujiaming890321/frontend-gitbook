# [storybook](https://storybook.js.org/)

Storybook is a frontend workshop for building UI components and pages in isolation. Thousands of teams use it for UI development, testing, and documentation. It's open source and free.

## Install

```js
npx storybook@latest init
or
pnpm i storybook@latest -D 后执行 storybook init
```

## Config

.storybook/main.ts
默认收集*.mdx 、*.stories.tsx

```js
const config: StorybookConfig = {
    stories: ['../src/**/*.mdx', '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
    addons: [
        '@storybook/addon-onboarding',
        '@storybook/addon-essentials',
        '@chromatic-com/storybook',
        '@storybook/addon-interactions',
    ],
    framework: {
        name: '@storybook/react-vite',
        options: {},
    },
}
export default config
```

## Story

```js
import type { Meta, StoryObj } from '@storybook/react'
import Component from '../index'

const meta: Meta<typeof Component> = {
    title: '分组标题/组件名称',
    component: Component,
    tags: ['autodocs'],
}

export default meta

type Story = StoryObj<typeof Component>

export const Task1: Story = {
    args: {
        nodeType: 1,
    },
}

export const Task2: Story = {
    args: {
        nodeType: 2,
    },
}
```
