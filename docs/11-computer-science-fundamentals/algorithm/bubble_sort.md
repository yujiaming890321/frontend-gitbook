# bubble

把数组里每一个元素一个接一个的排序

```js
function bubbleSort(arr){
    for(var i=0; i<arr.length-1; i++){
        console.log(i);
        for(var j=0; j<arr.length-i-1; j++){
            if(arr[j] > arr[j+1]){
                var oldVal = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = oldVal;
            }
        }
    }
}
```
