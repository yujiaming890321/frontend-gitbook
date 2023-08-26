# 正则

## 注意 undefined 问题

/^\w+$/.test(undefined)

https://stackoverflow.com/questions/1085189/why-does-the-javascript-regexp-w-match-undefined

^(?!undefined)[A-Za-z]{2,}$

## 配置白名单

```js
function matchWhiteList(string) {
    let whiteList = ["134123456**", "13436556677"];
    let regexList = whiteList.map(pattern => {
        let regex = pattern.replace(/\*/g, '.+')
        reutrn `^${regex}$`
    })
    for (let i = 0; i < regexList.length; i++) {
        const isMatch = string.match(regexList[i]);
        if (isMatch) return true;
    }
    return false;
}
```
