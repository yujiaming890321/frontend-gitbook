# scss

## @impoort

@import 'foo';

## @extend

```scss
.c1 {
    font-size: 24px;
    color: green;
}

.c2 {
    @extend .c1;
    color: red;
}
```

## @minin/@include

```scss
@minin couners {
    border-radius: 50%;
}

.button {
    @include corners;
    color: white;
}
```
