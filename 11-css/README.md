# css

## dotted-bg

```css
.replicant-dotted-bg {
    --color-ct-bg: #111;
    --color-ct-dotted-grid: #393c41;
    --dotted-bg: radial-gradient(var(--color-ct-dotted-grid) 1px,transparent 0);
    --dotted-bg-gradient: linear-gradient(180deg,transparent 0%,var(--color-ct-bg) 100%);
    background-image: var(--dotted-bg);
    background-position: -20px -9px;
    background-size: 20px 20px;
    z-index: 0;
    :before {
        background-image: var(--dotted-bg-gradient);
        bottom: 0;
        content: "";
        left: 0;
        position: absolute;
        right: 0;
        top: 0;
        z-index: -1;
    }
}
```

```html
<div class="replicant-dotted-bg"></div>
```
