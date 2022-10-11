# Git

## 推送分支到远程，没有则新建

git push origin feature/CNDE-4214

## 推送并跟踪远程分支，没有则新建

The current branch feature/DRO-1503 has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin feature/DRO-1503

## 跟踪远程分支

git branch -u origin/feature/DRO-1216

## git lfs (Large File Storage) 大文件传输

```js
git lfs install
git lfs uninstall
```

## git pull --dedth 1 后拉取分支

```js
// git clone --depth 1 https://github.com/dogescript/xxxxxxx.git
// git fetch --unshallow

git remote set-branches origin 'DEVOPS-3868-pvg16-prd' && 
git fetch --depth 1 origin DEVOPS-3868-pvg16-prd && 
git checkout DEVOPS-3868-pvg16-prd && 
git fetch --unshallow

git stash &&
git remote set-branches origin 'main' && 
git fetch origin main && 
git checkout main &&
git stash pop

git stash &&
git remote set-branches origin 'r/202210_2/alpha_cn' && 
git fetch origin r/202210_2/alpha_cn && 
git checkout r/202210_2/alpha_cn &&
git stash pop
```
