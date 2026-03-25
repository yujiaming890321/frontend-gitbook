# How to ask good questions? 如何正确的提问?

Asking good questions is a super important skill when writing software. I’ve gotten way better at it over the years (to the extent that it’s something my coworkers comment on a lot). Here are a few guidelines that have worked well for me!

> 在编写软件时，问好问题是一项非常重要的技能。这些年来，我在这方面做得越来越好（在某种程度上，这是我的同事们经常评论的事情）。这里有一些对我很有效的指导方针！

## asking bad questions is ok

I’m actually kind of a big believer in asking dumb questions or questions that aren’t “good”.

> 我其实有点相信问愚蠢的问题或不“好”的问题。

I ask people kind of dumb questions all the time, questions that I could have answered with Google or by searching our codebase.

> 我总是问人们一些愚蠢的问题，这些问题我本可以用谷歌或搜索我们的代码库来回答。

I mostly try not to, but sometimes I do it anyway and I don’t think it’s the end of the world.

> 我大多尽量不这样做，但有时我还是会这样做，我不认为这是世界末日。

So this list of strategies isn’t about “here are all the things you have to do before asking a question, otherwise you are a bad person and should feel bad”, but rather “here are some things that have helped me ask better questions and get the answers I want!”.

> 所以这个策略列表不是关于“在问问题之前，你必须做的所有事情，否则你是一个坏人，应该感到难过”，而是“这里有一些事情帮助我提出了更好的问题，并得到了我想要的答案！”。

If someone is refusing to answer your questions unless they’re “good”, I wrote a different blog post for them to read: How to answer questions in a helpful way

> 如果有人拒绝回答你的问题，除非他们“好”，我写了一篇不同的博客文章供他们阅读：如何以有益的方式回答问题

## what’s a good question?

> 什么是好问题？

Our goal is going to be to ask questions about technical concepts that are easy to answer.

> 我们的目标是提出易于回答的技术概念问题。

I often have somebody with me who has a bunch of knowledge that I’d like to know too, but they don’t always know exactly how to explain it to me in the best way.

> 我经常有一个人和我在一起，他有很多我也想知道的知识，但他们并不总是知道如何以最好的方式向我解释。

If I ask a good series of questions, then I can help the person explain what they know to me efficiently and guide them to telling me the stuff I’m interested in knowing.

> 如果我问一系列好的问题，那么我可以帮助这个人有效地向我解释他们所知道的，并引导他们告诉我我感兴趣的事情。

So let’s talk about how to do that!

> 那么，让我们来谈谈如何做到这一点！

## State what you know

> 陈述你所知道的

This is one of my favorite question-asking techniques! This kind of question basically takes the form

> 这是我最喜欢的提问技巧之一！这类问题基本上采取以下形式

1. State what you understand about the subject so far
2. Ask “is that right?”

> 1.说明到目前为止你对这个主题的理解 2.问“对吗？”

For example, I was talking to someone (a really excellent question asker) about networking recently! They stated “so, what I understand here is that there’s some chain of recursive dns servers…”. That was not correct! There is actually no chain of recursive DNS servers. (when you talk to a recursive DNS server there is only 1 recursive server involved) So them saying their understanding so far made it easy for us to clarify how it actually works.

> 例如，我最近和一个人（一个非常好的提问者）谈论网络相关的问题！他们表示“所以，我在这里理解的是，有一些递归 dns 服务器链……”。这是不对的！实际上没有递归 DNS 服务器链。（当你与递归 DNS 服务器交谈时，只涉及 1 个递归服务器）因此，他们表示，到目前为止，他们的理解使我们很容易澄清它的实际工作原理。

I was interested in rkt a while back, and I didn’t understand why rkt took up so much more disk space than Docker when running containers.

> 不久前，我对 rkt 很感兴趣，我不明白为什么 rkt 在运行容器时比 Docker 占用了更多的磁盘空间。

“Why does rkt use more disk space than Docker” didn’t feel like the right question though – I understood more or less how the code worked, but I didn’t understand why they wrote the code that way.

> “为什么 rkt 比 Docker 使用更多的磁盘空间”并不是一个正确的问题——我或多或少地理解了代码是如何工作的，但我不明白他们为什么这样写代码。

So I wrote this question to the rkt-dev mailing list: Why does rkt store container images differently from Docker?

> 所以我在 rkt-dev 邮件列表中写了这个问题：为什么 rkt 存储容器映像与 Docker 不同？

-   wrote down my understanding of how both rkt and Docker store containers on disk
-   came up with a few reasons I thought they might have designed it the way they did
-   and just asked “is my understanding right?”

> -   写下我对 rkt 和 Docker 如何在磁盘上存储容器的理解
> -   我想到了几个原因，我认为他们可能是按照他们的方式设计的
> -   只是问“我的理解对吗？”

The answer I got was super super helpful, exactly what I was looking for.

> 我得到的答案非常有帮助，正是我想要的。

It took me quite a while to formulate the question in a way that I was happy with, and I’m happy I took the time because it made me understand what was happening a lot better.

> 我花了很长时间才以一种我满意的方式提出这个问题，我很高兴我花了时间，因为这让我更好地理解了发生了什么。

Stating your understanding is not at all easy (it takes time to think about what you know and clarify your thoughts!!) but it works really well and it makes it a lot easier for the person you’re asking to help you.

> 陈述你的理解一点也不容易（思考你所知道的并澄清你的想法需要时间！！），但它真的很有效，它让你请求帮助的人更容易。

## Ask questions where the answer is a fact

> 在答案是事实的地方提问

A lot of the questions I have start out kind of vague, like “How do SQL joins work?”. That question isn’t awesome, because there are a lot of different parts of how joins work! How is the person even supposed to know what I’m interested in learning?

> 我提出的很多问题一开始都有点模糊，比如“SQL 连接是如何工作的？”。这个问题并不可怕，因为连接的工作方式有很多不同的部分！这个人怎么知道我想学什么？

I like to ask questions where the answer is a straightforward fact. For example, in our SQL joins example, some questions with facts for answers might be:

> 我喜欢问那些答案很简单的问题。例如，在我们的 SQL 连接示例中，一些需要事实作为答案的问题可能是：

-   What’s the time complexity of joining two tables of size N and M? Is it O(NM)? O(NlogN) + O(MlogM)?
-   Does MySQL always sort the join columns as a first step before doing the join?
-   I know that Hadoop sometimes does a “hash join” – is that a joining strategy that other database engines use too?
-   When I do a join between one indexed column and one unindexed column, do I need to sort the unindexed column?
-   When I ask super specific questions like this, the person I’m asking doesn’t always know the answer (which is fine!!) but at least they understand the kind of question I’m interested in – like, I’m obviously not interested in knowing how to use a join, I want to understand something about the implementation details and the algorithms.

> -   连接两个大小为 N 和 M 的表的时间复杂度是多少？是 O（NM）吗？O（NlogN）+O（MlogM）？
> -   MySQL 在执行联接操作之前，是否总是首先对联接列进行排序？
> -   我知道 Hadoop 有时会进行“哈希连接”——这是其他数据库引擎也使用的连接策略吗？
> -   当我在一个索引列和一个未索引列之间进行联接时，我需要对未索引列进行排序吗？
> -   当我问这样的超级具体的问题时，我问的人并不总是知道答案（这很好！！），但至少他们理解我感兴趣的问题——比如，我显然对如何使用连接不感兴趣，我想了解一些实现细节和算法。

## Be willing to say what you don’t understand

> 愿意说出你不明白的话

Often when someone is explaining something to me, they’ll say something that I don’t understand.

> 通常，当有人向我解释某事时，他们会说一些我不理解的话。

For example, someone might be explaining something about databases to me and say “well, we use optimistic locking with MySQL, and so…”.

> 例如，有人可能正在向我解释一些关于数据库的事情，并说“好吧，我们在 MySQL 中使用乐观锁定，所以……”。

I have no idea what “optimistic locking” is.

> 我不知道什么是“乐观锁定”。

So that would be a good time to ask! :)

> 所以现在是提问的好时机！：）

Being able to stop someone and say “hey, what does that mean?” is a super important skill.

> 能够阻止某人说“嘿，那是什么意思？”是一项非常重要的技能。

I think of it as being one of the properties of a confident engineer and an awesome thing to grow into.

> 我认为这是一个自信的工程师的特性之一，也是一件很棒的事情。

I see a lot of senior engineers who frequently ask for clarifications – I think when you’re more confident in your skills, this gets easier.

> 我看到很多高级工程师经常要求澄清——我认为当你对自己的技能更有信心时，这会变得更容易。

The more I do this, the more comfortable I feel asking someone to clarify.

> 我做得越多，要求别人澄清就越舒服。

in fact, if someone doesn’t ask me for clarifications when I’m explaining something, I worry that they’re not really listening!

> 事实上，如果有人在我解释某事时没有要求我澄清，我担心他们并没有真正在听！

This also creates space for the question answerer to admit when they’ve reached the end of their knowledge!

> 这也为问题回答者在知识达到极限时提供了承认的空间！

Very frequently when I’m asking someone questions, I’ll ask something that they don’t know.

> 当我问别人问题时，我经常会问一些他们不知道的事情。

People I ask are usually really good at saying “nope, I don’t know that!”

> 我问的人通常都很擅长说“不，我不知道！”

## Identify terms you don’t understand

> 识别你不理解的术语

When I started at my current job, I started on the data team.

> 当我开始从事目前的工作时，我加入了数据团队。

When I started looking at what my new job entailed, there were all these words!Hadoop, Scalding, Hive, Impala, HDFS, zoolander, and more.

> 当我开始考虑我的新工作需要什么时，有这么多术语！Hadoop、Scaling、Hive、Impala、HDFS、zoolander 等。

I had maybe heard of Hadoop before but I didn’t know what basically any of these words meant.

> 我以前可能听说过 Hadoop，但我不知道这些词的基本含义。

Some of the words were internal projects, some of them were open source projects.

> 其中一些是内部项目，一些是开源项目。

So I started just by asking people to help me understand what each of the terms meant and the relationships between them.

> 所以我开始只是要求人们帮助我理解每个术语的含义以及它们之间的关系。

Some kinds of questions I might have asked:

> 我可能会问一些问题：

-   Is HDFS a database? (no, it’s a distributed file system)
-   Does Scalding use Hadoop? (yes)
-   Does Hive use Scalding? (no)

> -   HDFS 是数据库吗？（不，这是一个分布式文件系统）
> -   Scaling 使用 Hadoop 吗？（是）
> -   Hive 使用 Scaling 吗？不

I actually wrote a ‘dictionary’ of all the terms because there were so many of them, and understanding what all the terms meant really helped me orient myself and ask better questions later on.

> 我实际上写了一本所有术语的“词典”，因为它们有很多，理解所有术语的含义真的帮助我定位自己，并在以后提出更好的问题。

## Do some research

> 做一些研究

When I was typing up those SQL questions above, I typed “how are sql joins implemented” into Google.

> 当我在上面键入这些 SQL 问题时，我在谷歌中键入了“SQL 联接是如何实现的”。

I clicked some links, saw “oh, I see, sometimes there is sorting, sometimes there are hash joins, I’ve heard about those”, and then wrote down some more specific questions I had.

> 我点击了一些链接，看到“哦，我知道了，有时有排序，有时有哈希连接，我听说过这些”，然后写下了我遇到的一些更具体的问题。

Googling a little first helped me write slightly better questions!

> 先在谷歌上搜索一下，我写的问题稍微好一些！

That said, I think people sometimes harp too much on “never ask a question without Googling it first” – sometimes I’ll be at lunch with someone and I’ll be curious about their work, and I’ll ask them some kind of basic questions about it. This is totally fine!

> 也就是说，我认为人们有时会过于强调“不先在谷歌上搜索就永远不要问问题” - 有时我会和别人一起吃午饭，我会对他们的工作很好奇，我会问他们一些关于它的基本问题。这完全没问题！

But doing research is really useful, and it’s actually really fun to be able to do enough research to come up with a set of awesome questions.

> 但做研究真的很有用，而且能够做足够的研究来提出一系列很棒的问题真的很有趣。

## Decide who to ask

> 决定问谁

I’m mostly talking here about asking your coworkers questions, since that’s where I spend most of my time.

> 我在这里主要是在问你的同事问题，因为我大部分时都是这样。

Some calculations I try to make when asking my coworkers questions are:

> 在向同事提问时，我尝试进行的一些考虑是：

-   is this a good time for this person? (if they’re in the middle of a stressful thing, probably not)
-   will asking them this question save me as much time as it takes them? (if I can ask a question that takes them 5 minutes to answer, and will save me 2 hours, that’s excellent :D)
-   How much time will it take them to answer my questions? If I have half an hour of questions to ask, I might want to schedule a block of time with them later, if I just have one quick question I can probably just ask it right now.
-   Is this person too senior for this question? I think it’s kind of easy to fall into the trap of asking the most experienced / knowledgeable person every question you have about a topic. But it’s often actually better to find someone who’s a little less knowledgeable – often they can actually answer most of your questions, it spreads the load around, and they get to showcase their knowledge (which is awesome).

> -   现在对这个人来说是个好时机吗？（如果他们正处于紧张的事情中，可能不会）
> -   问他们这个问题能节省我和他们一样多的时间吗？（如果我能问一个需要他们 5 分钟回答的问题，这将为我节省 2 个小时，那太好了：D）
> -   他们需要多少时间来回答我的问题？如果我有半个小时的问题要问，我可能想稍后安排一段时间和他们在一起，如果我只有一个快速的问题，我可能现在就可以问。
> -   这个人对这个问题来说太老了吗？我认为很容易陷入向最有经验/知识渊博的人提出关于某个主题的每一个问题的陷阱。但实际上，最好找一个知识稍浅的人——他们通常可以回答你的大部分问题，这会分散负担，他们可以展示自己的知识（这太棒了）。

I don’t always get this right, but it’s been helpful for me to think about these things.

> 我并不总是做对，但思考这些事情对我很有帮助。

Also, I usually spend more time asking people who I’m closer to questions – there are people who I talk to almost every day, and I can generally ask them questions easily because they have a lot of context about what I’m working on and can easily give me a helpful answer.

> 此外，我通常会花更多的时间问那些我更接近问题的人——有些人我几乎每天都会和他们交谈，我通常可以很容易地问他们问题，因为他们对我正在做的事情有很多了解，可以很容易给我一个有帮助的答案。

How to ask questions the smart way by ESR is a popular and pretty hostile document (it starts out poorly with statements like ‘We call people like this “losers”’, and doesn’t get much better).

> 如何通过 ESR 以聪明的方式提问是一份受欢迎且相当敌对的文件（它以“我们称这样的人为‘失败者’”这样的陈述开头很糟糕，而且没有变得更好）。

It’s also about asking questions to strangers on the internet.

> 这也是关于在互联网上向陌生人提问。

Asking strangers on the internet questions is a super useful skill and can get you really useful information, but it’s also the “hard mode” of asking questions.

> 在互联网上向陌生人提问是一种非常有用的技能，可以为你提供非常有用的信息，但这也是提问的“困难模式”。

The person you’re talking to knows very little about your situation, so it helps to be proportionally more careful about stating what exactly you want to know.

> 与你交谈的人对你的情况知之甚少，因此，在陈述你到底想知道什么时，按比例更小心会有所帮助。

I think “How to ask questions the smart way” puts an extremely unreasonable burden on question-askers (it says that someone should exhaust every other possible option to get the information they want before asking a question otherwise they’re a “lazy sponge”), but the “How To Answer Questions in a Helpful Way” section is good.

> 我认为“如何以聪明的方式提问”给提问者带来了极其不合理的负担（它说，在提问之前，人们应该用尽所有其他可能的选择来获取他们想要的信息，否则他们就是一块“懒惰的海绵”），但“如何以有帮助的方式回答问题”部分很好。

## Ask questions to show what’s not obvious

> 提出问题以显示不明显的内容

A more advanced form of question asking is asking questions to reveal hidden assumptions or knowledge.

> 一种更高级的提问形式是通过提问来揭示隐藏的假设或知识。

This kind of question actually has two purposes – first, to get the answers (there is probably information one person has that other people don’t!) but also to point out that there is some hidden information, and that sharing it is useful.

> 这类问题实际上有两个目的——第一，得到答案（可能有一个人拥有其他人没有的信息！），但也指出有一些隐藏的信息，分享这些信息是有用的。

The “The Art of Asking Questions” section of the Etsy’s Debriefing Facilitation Guide is a really excellent introduction to this, in the context of discussing an incident that has happened. Here are a few of the questions from that guide:

> Etsy《汇报便利指南》的“提问艺术”部分在讨论已发生的事件时，对这一点进行了很好的介绍。以下是该指南中的几个问题：

“What things do you look for when you suspect this type of failure happened?”

> “当你怀疑这种失败发生时，你会寻找什么？”

“How did you judge that this situation was ‘normal?”

> “你怎么判断这种情况是‘正常’的？”

How did you know that the database was down?

> 你怎么知道数据库坏了？

How did you know that was the team you needed to page?

> 你怎么知道那是你需要呼叫的团队？

These kinds of questions (that seem pretty basic, but are not actually obvious) are especially powerful when someone who’s in a position of some authority asks them.

> 当处于某种权威地位的人问这些问题时，这些问题（看起来很基本，但实际上并不明显）尤其有力。

I really like it when a manager / senior engineer asks a basic but important question like “how did you know the database was down?” because it creates space for less-senior people to ask the same kinds of questions later.

> 我真的很喜欢经理/高级工程师问一个基本但重要的问题，比如“你怎么知道数据库宕机了？”，因为这为级别较低的人以后问同样的问题创造了空间。

## Answer questions

> 回答问题

One of my favorite parts of André Arko’s great How to Contribute to Open Source post is where he says

> AndréArko 的《如何为开源做出贡献》一文中，我最喜欢的部分之一是他说

-   Now that you’ve read all the issues and pull requests, start to watch for questions that you can answer. It won’t take too long before you notice that someone is asking a question that’s been answered before, or that’s answered in the docs that you just read. Answer the questions you know how to answer.

> -   现在您已经阅读了所有问题和拉取请求，开始注意您可以回答的问题。不久之后，你就会注意到有人问了一个以前已经回答过的问题，或者在你刚刚阅读的文档中已经回答过了。回答你知道如何回答的问题。

If you’re ramping up on a new project, answering questions from people who are learning the stuff you just learned can be a really awesome way to solidify your knowledge.

> 如果你正在着手一个新项目，回答那些正在学习你刚刚学到的东西的人的问题，可以是巩固你知识的一种非常棒的方式。

Whenever I answer a question about a new topic for the first time I always feel like “omg, what if I answer their question wrong, omg”.

> 每当我第一次回答一个新话题的问题时，我总是觉得“天哪，如果我回答错了他们的问题怎么办，天哪”。

But usually I can answer their question correctly, and then I come away feeling awesome and like I understand the subject better!

> 但通常我能正确地回答他们的问题，然后我离开时感觉很棒，好像我对这个主题有了更好的理解！

## Questions can be a huge contribution

> 提问可以做出巨大贡献

Good questions can be a great contribution to a community!

> 好的问题可以为社区做出巨大贡献！

I asked a bunch of questions about CDNs a while back on twitter and wrote up the answers in CDNs aren’t just for caching.

> 不久前，我在推特上问了很多关于 CDN 的问题，并写下了 CDN 中的答案，这些答案不仅仅是为了缓存。

A lot of people told me they really liked that blog post, and I think that me asking those questions helped a lot of people, not just me.

> 很多人告诉我他们真的很喜欢那篇博客文章，我认为我问这些问题帮助了很多人，而不仅仅是我。

A lot of people really like answering questions!

> 很多人真的很喜欢回答问题！

I think it’s important to think of good questions as an awesome thing that you can do to add to the conversation, not just “ask good questions so that people are only a little annoyed instead of VERY annoyed”.

> 我认为重要的是要把好的问题看作是一件很棒的事情，你可以做这件事来增加谈话的内容，而不仅仅是“问好问题，让人们只是有点恼火，而不是非常恼火”。
