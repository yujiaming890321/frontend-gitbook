# quick

选择数组中某个元素作为“准基数”，将所有小于准基数的元素放在其左边，大于准基数的元素放在其右边，从而将数组划分成左子数组和右子数组，再分别递归左子数组和右子数组。

```js
function swap(arr, a, b) {
    const temp = arr[a];
    arr[a] = arr[b];
    arr[b] = temp;
}

function partition(arr, begin, end) {
    let left = begin, right = end;
    while (left < right){
        //从右往左，先找到小于准基数的元素
        while (left < right && arr[right] >= arr[begin]) right--;
        //从左往右，再找到大于准基数的元素
        while (left < right && arr[left] <= arr[begin]) left++;
        //交换位置，左边是小于准基数的元素，右边是大于准基数的元素
        swap(arr, left, right);
    }
    //循环结束后，交换准基数和左子数的位置
    swap(arr, begin, left);
    //返回准基数位置
    return left
}

function quickSort(arr, begin, end) {
    if(begin >= end) return;
    // 哨兵
    const povit = partition(arr, begin, end);
    // 递归左子数
    quickSort(arr, begin, povit-1); 
    // 递归右子数
    quickSort(arr, povit + 1, end);
    return arr;
}
```
