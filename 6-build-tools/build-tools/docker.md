# docker

docker-machine、docker-compose、

## docker-machine

docker-machine是解决docker运行环境问题。

docker技术是基于Linux内核的cgroup技术实现的，在非Linux平台上使用docker技术需要依赖安装Linux系统的虚拟机。

## docker-compose

dcoker-compose主要是解决本地docker容器编排问题。

一般是通过yaml配置文件来使用它，这个yaml文件里能记录多个容器启动的配置信息（镜像、启动命令、端口映射等）

最后只需要执行docker-compose对应的命令就会像执行脚本一样地批量创建和销毁容器。

## docker-swarm

docker-swarm是解决多主机多个容器调度部署得问题。

swarm是基于docker平台实现的集群技术，他可以通过几条简单的指令快速的创建一个docker集群，接着在集群的共享网络上部署应用，最终实现分布式的服务。

swarm技术相当不成熟，很多配置功能都无法实现，只能说是个半成品，目前更多的是使用Kubernetes来管理集群和调度容器。

## [kubernetes](https://kubernetes.io/#)