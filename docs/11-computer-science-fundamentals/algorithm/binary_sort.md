# binary

将数组分为两部分。取数组中间的值为基准数，比基准数小的放左边，比基准数大的放右边。
利用递归，对小数组、大数组回调分组方法。最后当数组长度只有一的时候，返回的单个数组。层层拼装成新数组，即最后返回的排序好的数组

```js
function binarySort(arr){
    if(arr.length <= 1){
        return arr;
    }
    var middleNumber = arr.splice( Math.floor(arr.length/2), 1 );
    var leftArr = [];
    var reightArr = [];
    for(var i=0; i<arr.length; i++){
        if(parseInt(arr[i])<=middleNumber){
            leftArr.push(arr[i]);
        }else{
            reightArr.push(arr[i]);
        }
    }
    return binarySort(leftArr).concat(middleNumber,binarySort(reightArr))
}
```
