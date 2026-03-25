# packjson 环境变量常用库

## [cross-env](https://www.npmjs.com/package/cross-env)

配置环境变量

```
{
 "scripts": {
   "build": "cross-env NODE_ENV=production webpack --config build/webpack.config.js"
 }
}
```

## [dotenv](https://www.npmjs.com/package/dotenv)

零依赖模块，从.env 加载配置文件，必须以 REACT_APP 开头

```
"build:dev": "dotenv -e .env.dev -e .env react-app-rewired build",
"build:pre": "dotenv -e .env.pre -e .env react-app-rewired build",
```

## [husky](https://www.npmjs.com/package/husky)

执行 git hooks， v4 与 v7 差异较大，4.3.8 是 packagjson 配置， v7 是文件配件。

## [f2elint](https://www.npmjs.com/package/f2elint)

F2ELint 是《阿里巴巴前端规约》的配套 Lint 工具，包括 Linter 依赖，如 ESLint、stylelint、commitlint、markdownlint 等

## [lint-staged](https://www.npmjs.com/package/lint-staged)

防止错误代码提交

```
"husky": {
    "hooks": {
        "pre-commit": "lint-staged",
        "commit-msg": "commitlint -E HUSKY_GIT_PARAMS"
    }
},
"lint-staged": {
    "*.{js,css,md,ts,tsx}": [
        "prettier --write",
        "git add"
    ]
}
```

## [commitlint](https://www.npmjs.com/package/@commitlint/cli)

检查提交 msg 是否合规

```
// commitlint.config.js
module.exports = {
	extends: ['@commitlint/config-conventional'],
	rules: {
		'type-enum': [
			2,
			'always',
			[
				'feat',
				'fix',
				'docs',
				'style',
				'refactor',
				'test',
				'chore',
				'comment',
				'build',
				'merge',
			],
		],
		'subject-full-stop': [0, 'never'],
		'subject-case': [0, 'never'],
	},
}
```
