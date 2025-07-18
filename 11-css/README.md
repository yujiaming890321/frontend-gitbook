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

## happy text

```css
.happy-text {
  background: linear-gradient(270deg, #FF5F6D, #FFC371, #c34dbf, #ff4b1f, #ff9068, #16BFFD, #a84dc3, #CB3066, #4CA1AF, #C4E0E5);
  background-size: 2000% 2000%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  -webkit-animation: happyText 30s ease infinite;
  -moz-animation: happyText 30s ease infinite;
  animation: happyText 30s ease infinite;
} 
@-webkit-keyframes happyText {
    0%{background-position:0% 14%}
    50%{background-position:100% 87%}
    100%{background-position:0% 14%}
}
@-moz-keyframes happyText {
    0%{background-position:0% 14%}
    50%{background-position:100% 87%}
    100%{background-position:0% 14%}
}
@keyframes happyText {
    0%{background-position:0% 14%}
    50%{background-position:100% 87%}
    100%{background-position:0% 14%}
}
```
