# Dynamic Programming 动态规划

```js
function knapsack(weights, values, capacity) {
  // 创建一个二维数组
  let dp = new Array(weights.length + 1).fill(0).map(() => new Array(capacity + 1).fill(0));
 
  // 遍历每个物品和背包容量
  for (let i = 1; i <= weights.length; i++) {
    for (let j = 1; j <= capacity; j++) {
      // 如果当前物品的重量大于背包的容量，则不可能装入该物品
      if (weights[i - 1] > j) {
        dp[i][j] = dp[i - 1][j];
      } else {
        // 计算选择当前物品和不选择当前物品的最大价值
        dp[i][j] = Math.max(dp[i - 1][j], dp[i - 1][j - weights[i - 1]] + values[i - 1]);
      }
    }
  }
 
  return dp[weights.length][capacity];
}
 
// 示例使用
const weights = [1, 3, 4]; // 物品的重量
const values = [15, 20, 30]; // 物品的价值
const capacity = 4; // 背包的容量
 
console.log(knapsack(weights, values, capacity)); // 输出最大价值
```
