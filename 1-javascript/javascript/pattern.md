# 正则

## 注意 undefined 问题

/^\w+$/.test(undefined)

https://stackoverflow.com/questions/1085189/why-does-the-javascript-regexp-w-match-undefined

^(?!undefined)[A-Za-z]{2,}$