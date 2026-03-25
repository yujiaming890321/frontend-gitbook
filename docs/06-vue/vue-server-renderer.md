# Vue SSR 的实现原理

## 组件基于 Vnode 来实现渲染

VNode 本身是 js 对象，兼容性极强，不依赖当前的执行的环境，从而可以在服务端渲染及原生渲染。虚拟 DOM 频繁修改，最后比较出真实 DOM 需要更改的地方，可以达到局部渲染的目的，减少性能损耗。

## vue-server-renderer

是一个具有独立渲染应用程序能力的包，是 Vue 服务端渲染的核心代码。

本文下面的源码也结合这个包展开，此处不多冗余介绍。

## SSR 渲染架构

![image](https://img2022.cnblogs.com/blog/2347599/202204/2347599-20220401162817792-229011630.png)

## 项目架构

```js
src
├── components
├── App.vue
├── app.js ----通用 entry
├── entry-client.js ----仅运行于浏览器
└── entry-server.js ----仅运行于服务器
```

> app.js 导出 createApp 函数工厂，此函数是可以被重复执行的，从根 Vue 实例注入，用于创建 router，store 以及应用程序实例。

```js
import Vue from 'vue'
import App from './App.vue'
// 导出一个工厂函数，用于创建新的应用程序、router 和 store 实例
export function createApp () {
  const app = new Vue({
    render: h => h(App)
  })
  return { app }
}
```

> entry-client.js 负责创建应用程序，挂载实例 DOM ，仅运行于浏览器。

```js
import { createApp } from './app'
const { app } = createApp()
// #app 为根元素，名称可替换
app.$mount('#app')
```

> entry-server.js 创建返回应用实例，同时还会进行路由匹配和数据的预处理，仅运行于服务器。

```js
import { createApp } from './app'
export default context => {
  const { app } = createApp()
  return app
}
```

## 服务端和客户端代码编写原则

作为同构框架，应用代码编译过程 Vue SSR 提供了两个编译入口，来作为抹平由于环境不同的代码差异。Client entry 和 Server entry 中编写代码逻辑的区分有两条原则

1. 通用型代码 可通用性的代码，由于鉴权逻辑和网关配置不同，需要在 webpack resolve.alias 中配置不同的模块环境应用。
2. 非通用性代码 Client entry 负责挂载 DOM 节点代码，以及三方包引入和具有兼容性库的加载。

Server entry 只生成 Vue 对象。

## 两个编译产物

经过 webpack 打包之后会有两个 bundle 产物

server bundle 用于生成 vue-ssr-server-bundle.json，我们熟悉的 sourceMap 和需要在服务端运行的代码列表都在这个产物中。

```js
// vue-SSR-server-bundle.json
{
  "entry": ,
  "files": {
    A：包含了所有要在服务端运行的代码列表
    B：入口文件
  }
}
```

client Bundle 用于生成 vue-SSR-client-manifest.json，包含所有的静态资源，首次渲染需要加载的 script 标签，以及需要在客户端运行的代码。

```js
// vue-SSR-client-manifest.json
{
  "publicPath": 公共资源路径文件地址,
  "all": 资源列表
  "initial":输出 html 字符串
  "async": 异步加载组件集合
  "modules": moduleIdentifier 和 all 数组中文件的映射关系
}
```

## renderer

是 Vue SSR 的核心代码，值得我们关注的是应用初始化和应用输出。
两个阶段提供了完整的应用层代码编译和组装逻辑。

### 应用初始化

#### 生成 Vue 对象

```js
const Vue = require('vue')
const app = new Vue()
```

#### 生成 renderer

```js
const renderer = require('vue-server-renderer').createRenderer()
// createRenderer 函数中有两个重要的对象：render 和 templateRenderer
function createRenderer (ref) {
  // render: 渲染 html 组件
  var render = createRenderFunction(modules, directives, isUnaryTag, cache);
  // templateRenderer: 模版渲染，clientManifest 文件
  var templateRenderer = new TemplateRenderer({
    template: template,
    inject: inject,
    shouldPreload: shouldPreload,
    shouldPrefetch: shouldPrefetch,
    clientManifest: clientManifest,
    serializer: serializer
  });
```

经过这个过程的 render 和 templateRenderer 并没有被调用，这两个函数真正的调用是在项目实例化 createBundleRenderer 函数的时候，即第三步创建的函数。

#### 创建沙盒 vm，实例化 Vue 的入口文件

```js
var vm = require('vm');
// 调用 createBundleRunner 函数实例对象，rendererOptions 支持可配置
var run = createBundleRunner(
  entry, ----入口文件集合
  files, ----打包文件集合
  basedir,
  rendererOptions.runInNewContext
)
```

在 createBundleRunner 方法的源码到其实举例了一个叫 compileModule 的一个方法
这个方法中有两个函数：getCompiledScript 和 evaluateModule

```js
function createBundleRunner (entry, files, basedir, runInNewContext) {
//触发 compileModule 方法，找到 webpack 编译形成的 code
var evaluate = compileModule(files, basedir, runInNewContext);
}
```

getCompiledScript：编译 wrapper ，找到入口文件的 files 文件名及 script 脚本的编译执行

```js
function getCompiledScript (filename) {
    if (compiledScripts[filename]) {
      return compiledScripts[filename]
    }
    // 在入口文件 files 中找到对应的文件名称
    var code = files[filename];
    var wrapper = NativeModule.wrap(code);
    // 在沙盒上下文中执行构建 script 脚本
    var script = new vm.Script(wrapper, {
      filename: filename,
      displayErrors: true
    });
    compiledScripts[filename] = script;
    return script
  }
```

evaluateModule：根据 runInThisContext 中的配置项来决定是在当前上下文执行还是单独上下文执行。

```js
function evaluateModule (filename, sandbox, evaluatedFiles) {
    if ( evaluatedFiles === void 0 ) evaluatedFiles = {};
    if (evaluatedFiles[filename]) {
      return evaluatedFiles[filename]
    }
    var script = getCompiledScript(filename);
    // 用于判断是在当前的那种模式下面执行沙盒上下文，此时存在两个函数的相互调用
    var compiledWrapper = runInNewContext === false
      ? script.runInThisContext()
      : script.runInNewContext(sandbox);
    // m: 函数导出的 exports 数据
    var m = { exports: {}};
    // r: 替代原生 require 用来解析 bundle 中通过 require 函数引用的模块
    var r = function (file) {
      ...
      return require(file)
    };
   }
```

上述的函数执行完成之后会调用 compiledWrapper.call，传参对应上面的 exports、require、module, 我们就能拿到入口函数。

#### 错误抛出容错和全局错误监听 renderToString: 在没有 cb 函数时做了 promise 的返回，那说明我们在调用次函数的时候可以直接做 try catch 的处理，用于全局错误的抛出容错。

```js
renderToString: function (context, cb) {
    var assign;
    if (typeof context === 'function') {
      cb = context;
      context = {};
    }
    var promise;
    if (!cb) {
      ((assign = createPromiseCallback(), promise = assign.promise, cb = assign.cb));
    }
    ...
    return promise
  },
}
```

renderToStream：对抛错做了监听机制, 抛错的钩子函数将在这个方法中触发。

```js
 renderToStream: function (context) {
    var res = new PassThrough();
    run(context).catch(function (err) {
      rewriteErrorTrace(err, maps);
      // 此处做了监听器的容错
      process.nextTick(function () {
        res.emit('error', err);
      });
    }).then(function (app) {
      if (app) {
        var renderStream = renderer.renderToStream(app, context);
        ...
      }
    }
 }
```

#### 防止交叉污染

Node.js 服务器是一个长期运行的进程，在客户端编写的代码在进入进程时，变量的上下文将会被保留，导致交叉请求状态污染。

因此不可共享一个实例，所以说 createApp 是一个可被重复执行的函数。其实在包内部，变量之间也存在防止交叉污染的能力。

防止交叉污染的能力是由 rendererOptions.runInNewContext 这个配置项来提供的，这个配置支持 true， false，和 once 三种配置项传入。

```js
// rendererOptions.runInNewContext 可配置项如下
  true:
  新上下文模式：创建新上下文并重新评估捆绑包在每个渲染上。
  确保每个应用程序的整个应用程序状态都是新的渲染，但会产生额外的评估成本。
  false:
  直接模式：
  每次渲染时，它只调用导出的函数。而不是在上重新评估整个捆绑包
  模块评估成本较高，但需要结构化源代码
  once:
  初始上下文模式
  仅用于收集可能的非组件 vue 样式加载程序注入的样式。
```

特别说明一下 false 和 once 的场景， 为了防止交叉污染，在渲染的过程中对作用域要求很严格，以此来保证在不同的对象彼此之间不会形成污染。

```js
if (!runner) {
   var sandbox = runInNewContext === 'once'
      ? createSandbox()
      : global;
    initialContext = sandbox.__VUE_SSR_CONTEXT__ = {};
    runner = evaluate(entry, sandbox);
    //在后续渲染中，_VUE_SSR_CONTEXT_uu 将不可用
    //防止交叉污染
    delete sandbox.__VUE_SSR_CONTEXT__;
    if (typeof runner !== 'function') {
      throw new Error(
        'bundle export should be a function when using ' +
        '{ runInNewContext: false }.'
      )
    }
  }
```

#### 应用输出

在应用输出这个阶段中，SSR 将更多侧重加载脚本内容和模版渲染，在模版渲染时在代码中是否定义过模版引擎源码将提供不同的 html 拼接结构。

#### 加载脚本内容

此过程会将上个阶段构造的 reader 和 templateRender 方法实现数据绑定。

templateRenderer：负责 html 封装，其原型上会有如下几个方法， 这些函数的作用如下图。值得一提的是：bindRenderFns 函数是将 4 个 render 函数绑定到用户上下文的 context 中,用户在拿到这些内容之后就可以做内容的自定义组装和渲染。

![image](https://mmbiz.qpic.cn/mmbiz_png/vzEib9IRhZD6XzrBwmrj1hQfHP9Qtb6Haxa2AKPDYdtzEnxWWA0GK3wnjdcG1zzyX8mp8GGAH9yMzOKsegaMaNQ/640?wx_fmt=png&wxfrom=5&wx_lazy=1&wx_co=1)

render: 函数会被递归调用按照从父到子的顺序，将组件全部转化为 html。

![image](https://mmbiz.qpic.cn/mmbiz_png/vzEib9IRhZD6XzrBwmrj1hQfHP9Qtb6HaRGcKib531fZdYd8pKW4eHjicpibJ16cuDohOKtYQzfsvJj9wMCkNfI5iaA/640?wx_fmt=png&wxfrom=5&wx_lazy=1&wx_co=1)

```js
function createRenderFunction (
  modules,
  directives,
  isUnaryTag,
  cache
) {
  return function render (
    component,
    write,
    userContext,
    done
  ) {
    warned = Object.create(null);
    var context = new RenderContext({
      activeInstance: component,
      userContext: userContext,
      write: write, done: done, renderNode: renderNode,
      isUnaryTag: isUnaryTag, modules: modules, directives: directives,
      cache: cache
    });
    installSSRHelpers(component);
    normalizeRender(component);
    // 渲染 node 节点，绑定用户作用上下文
    var resolve = function () {
      renderNode(component._render(), true, context);
    };
    // 等待组件 serverPrefetch 执行完成之后，_render 生成子节点的 vnode 进行渲染
    waitForServerPrefetch(component, resolve, done);
  }
}
```

在经过上面的编译流程之后，我们已经拿到了 html 字符串，但如果要在浏览器中展示页面还需 js, css 等标签与这个 html 组装成一个完整的报文输出到浏览器中， 因此需要模版渲染阶段来将这些元素实现组装。

#### 模版渲染

经过应用初始化阶段，代码被编译获取了 html 字符串，context 渲染需要依赖的 templateRenderer.prototype.bindRenderFns 中绑定的 state, script , styles 等资源。

```js
TemplateRenderer.prototype.bindRenderFns = function bindRenderFns (context) {
  var renderer = this
  ;['ResourceHints', 'State', 'Scripts', 'Styles'].forEach(function (type) {
    context[("render" + type)] = renderer[("render" + type)].bind(renderer, context);
  });
  context.getPreloadFiles = r**erer.ge****：**reloadFiles.bind(renderer, context);
};
```

在具体渲染模版时，会有以下两种情况：

- 未定义模版引擎 渲染结果会被直接返回给 renderToString 的回调函数，而页面所需要的脚本依赖我们通过用户上下文 context 的 renderStyles，renderResourceHints、renderState、renderScripts 这些函数分别获得。

- 定义了模版引擎 templateRender 会帮助我们进行 html 组装

```js
TemplateRenderer.prototype.render = function render (content, context) {
// parsedTemplate 用于解析函数得到的包含三个部分的 compile 对象，
// 按照顺序进行字符串模版的拼接
  var template = this.parsedTemplate;
  if (!template) {
    throw new Error('render cannot be called without a template.')
  }
  context = context || {};

  if (typeof template === 'function') {
    return template(content, context)
  }

  if (this.inject) {
    return (
      template.head(context) +
      (context.head || '') +
      this.renderResourceHints(context) +
      this.renderStyles(context) +
      template.neck(context) +
      content +
      this.renderState(context) +
      this.renderScripts(context) +
      template.tail(context)
    )
  } else {
    ...
  }
};
```

至此我们了解了 Vue SSR 的整体架构逻辑和 vue-server-renderer 的核心代码，当然 SSR 也是有很多开箱即用的脚手架来供我们选择的。
