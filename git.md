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
git remote set-branches origin 'r/202210_3/alpha_cn' && 
git fetch origin r/202210_3/alpha_cn && 
git checkout r/202210_3/alpha_cn &&
git stash pop
```

## Git Tricks

### Was my fix in the build of the ticket?

Check out the build locally and check of the commit was in it:

```js
git checkout your-release-branch
git log | grep your-commited-hash
```

If there is no output, the commit is not in it.

### Resolving Automatic merge failure

Steps to fix:

1. Identify([aɪˈdentɪfaɪ] 识别) the the destination([ˌdestɪˈneɪʃn] 目的地;终点) branch that the automerge check from GH Actions tab is failing to merge to (ex:  release/4.15.0)
    You can identify the conflicting release branch by comparing your PR to the other active release branches, you will need to fix the lowest version release branch that has a conflict
        For example if you are blocked by auto merge while trying to merge into release/4.15.0
        First compare your branch to release/4.15.1 and see if there are any merge conflicts
        If there are no merge conflicts move to the release/4.15.2 branch if it exists or check release/4.16.0 branch
        Continue this approach until you find the branch that has conflicts
2. Create a new branch from the identified branch in step 1 - e.g.  git fetch && git checkout release/4.15.0 && git pull && git checkout -b user/<username>/merge-conflict-fix
3. Merge your original PR branch to the new branch -  git merge user/<username>/original-pr-branch
4. Resolve merge conflicts
5. Create a PR from new branch ( user/<username>/merge-conflict-fix ) to the branch identified in step 1
6. Merge upon approval
    If merging to a release/** branch, then your fix will also auto-merge to the other downstream branches (including main) and resolve all conflicts.

### Additional background information for auto merge

The mobile app repo does merge strategy([ˈstrætədʒi] 策略;计策;) is to continuously ([kənˈtɪnjuəsli] 连续不断地) merge lower release branches into higher release branches and finally ending at main

release/4.15.0 → release/4.15.1 → release/4.16.0 → main

To automate([ˈɔːtəmeɪt] 自动化) and manage this process the repo uses Automerger: xxx.

When the auto merge is unable to merge into the downstream branches (higher versions & main) there will be conflicts in the auto-merge check. If a commit that has those auto merge conflicts were to be merged into a branch, that commit and any subsequent([ˈsʌbsɪkwənt] 后来的;随后的) commits would not be able to be merged further down the branch stream, effectively blocking the auto-merging stream. This could cause further([ˈfɜːrðər] 进一步的;更多的) conflicts and if those are handled incorrectly, could jeopardize([ˈdʒepərdaɪz] 危害;危及;) the release schedule and repo health.

### Understanding auto-merge as a visual metaphor

Think of auto-merge as a flowing river, that starts at the next release branch, as the river flows it will hit every branch along the way and finally end in the main branch lake.
Adding a PR into the auto-merge river should start at it's entry point (your targeted release) and it should then flow down to all later releases if there are no problems.
If a conflict were to be introduced into this flow it would act as a sort of dam in the process, blocking the flow for all other PRs on the path.
The best way to fix this is to remove the dam blocking the flow downstream.
Once that dam is removed, all of the river will begin to flow again.
The auto-merge check is a way for us to identify when a PR will create a dam in the process before it happens.
When we know that a dam will be created we can instead go to the problem area and prepare that part of the river (the release branch) to be ready to handle the new change. 

### Fixing a tangled mess

As multiple releases are being worked on, features get added and removed multiple conflicts between multiple release branches can happen.
The best way to get the auto merge pattern working correctly again is starting from the lowest release versions and working to higher ones, and then finally main.
You can follow the steps to fix above for each conflicting release branch simply replace the "release/4.xx.x" version in the "Steps to fix" above with the higher release version, and change "user/<username>/original-pr-branch" to the lower release version.

### Compare two git hashes (e.g. released app builds) without seeing all the godot and generated code

git diff origin/archive/prod/4.5.1/4.5.1-865..origin/archive/prod/4.6.0/4.6.0-877 ':(exclude)__tests__' ':(exclude)android/generated/' ':(exclude)android/godot/src/' ':(exclude)app/model/generated)' ':(exclude)ios/plugins/TMBLE/protobufs'
