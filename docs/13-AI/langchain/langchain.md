# [langChain](https://js.langchain.com/)

## Concepts

聊天模型：通过聊天API公开的LLM，处理消息序列作为输入和输出消息。
Chat models: LLMs exposed via a chat API that process sequences of messages as input and output a message.

消息：聊天模型中的通信单位，用于表示模型输入和输出。
Messages: The unit of communication in chat models, used to represent model input and output.

聊天历史：对话表示为一系列消息，在用户消息和模型响应之间交替。
Chat history: A conversation represented as a sequence of messages, alternating between user messages and model responses.

工具：一个具有相关模式的函数，该模式定义了函数的名称、描述及其接受的参数。
Tools: A function with an associated schema defining the function's name, description, and the arguments it accepts.

工具调用：一种聊天模型API，它接受工具模式和消息作为输入，并将这些工具的调用作为输出消息的一部分返回。
Tool calling: A type of chat model API that accepts tool schemas, along with messages, as input and returns invocations of those tools as part of the output message.

结构化输出：一种使聊天模型以结构化格式响应的技术，例如与给定模式匹配的JSON。
Structured output: A technique to make a chat model respond in a structured format, such as JSON that matches a given schema.

记忆：关于对话的信息，它被持久化，以便在未来的对话中使用。
Memory: Information about a conversation that is persisted so that it can be used in future conversations.

多模态：能够处理不同形式的数据，如文本、音频、图像和视频。
Multimodality: The ability to work with data that comes in different forms, such as text, audio, images, and video.

可运行接口：许多LangChain组件和LangChain表达式语言所基于的基本抽象。
Runnable interface: The base abstraction that many LangChain components and the LangChain Expression Language are built on.

流式处理：LangChain流式处理API，用于在生成结果时显示结果。
Streaming: LangChain streaming APIs for surfacing results as they are generated.

LangChain表达式语言（LCEL）：用于编排LangChain组件的语法。对于更简单的应用程序最有用。
LangChain Expression Language (LCEL): A syntax for orchestrating LangChain components. Most useful for simpler applications.

文档加载器：将源加载为文档列表。
Document loaders: Load a source as a list of documents.

检索：信息检索系统可以根据查询从数据源检索结构化或非结构化数据。
Retrieval: Information retrieval systems can retrieve structured or unstructured data from a datasource in response to a query.

文本分割器：将长文本分割成更小的块，这些块可以单独索引，以实现精细检索。
Text splitters: Split long text into smaller chunks that can be individually indexed to enable granular retrieval.

嵌入模型：在向量空间中表示文本或图像等数据的模型。
Embedding models: Models that represent data such as text or images in a vector space.

矢量存储：矢量和相关元数据的存储和高效搜索。
Vector stores: Storage of and efficient search over vectors and associated metadata.

检索器：一个从知识库中返回相关文档以响应查询的组件。
Retriever: A component that returns relevant documents from a knowledge base in response to a query.

检索增强生成（RAG）：一种通过将语言模型与外部知识库相结合来增强语言模型的技术。
Retrieval Augmented Generation (RAG): A technique that enhances language models by combining them with external knowledge bases.

代理：使用语言模型选择要采取的一系列行动。代理可以通过工具与外部资源交互。
Agents: Use a language model to choose a sequence of actions to take. Agents can interact with external resources via tool.

提示模板：用于分解模型“提示”（通常是一系列消息）的静态部分的组件。可用于序列化、版本控制和重用这些静态部分。
Prompt templates: Component for factoring out the static parts of a model "prompt" (usually a sequence of messages). Useful for serializing, versioning, and reusing these static parts.

输出解析器：负责获取模型的输出，并将其转换为更适合下游任务的格式。在工具调用和结构化输出普遍可用之前，输出解析器主要是有用的。
Output parsers: Responsible for taking the output of a model and transforming it into a more suitable format for downstream tasks. Output parsers were primarily useful prior to the general availability of tool calling and structured outputs.

少镜头提示：一种通过在提示中提供几个要执行的任务示例来提高模型性能的技术。
Few-shot prompting: A technique for improving model performance by providing a few examples of the task to perform in the prompt.

示例选择器：用于根据给定的输入从数据集中选择最相关的示例。示例选择器用于少数镜头提示，为提示选择示例。
Example selectors: Used to select the most relevant examples from a dataset based on a given input. Example selectors are used in few-shot prompting to select examples for a prompt.

回调：回调允许在内置组件中执行自定义辅助代码。回调用于流式传输LangChain中LLM的输出，跟踪应用程序的中间步骤等等。
Callbacks: Callbacks enable the execution of custom auxiliary code in built-in components. Callbacks are used to stream outputs from LLMs in LangChain, trace the intermediate steps of an application, and more.

跟踪：记录应用程序从输入到输出的步骤的过程。跟踪对于调试和诊断复杂应用程序中的问题至关重要。
Tracing: The process of recording the steps that an application takes to go from input to output. Tracing is essential for debugging and diagnosing issues in complex applications.

评估：评估人工智能应用程序性能和有效性的过程。这涉及根据一组预定义的标准或基准测试模型的响应，以确保其符合所需的质量标准并实现预期目的。这个过程对于构建可靠的应用程序至关重要。
Evaluation: The process of assessing the performance and effectiveness of AI applications. This involves testing the model's responses against a set of predefined criteria or benchmarks to ensure it meets the desired quality standards and fulfills the intended purpose. This process is vital for building reliable applications.

## Glossary

AIMessageChunk：来自AI消息的部分响应。用于从聊天模型流式传输响应。
AIMessageChunk: A partial response from an AI message. Used when streaming responses from a chat model.

AIMessage：表示来自AI模型的完整响应。
AIMessage: Represents a complete response from an AI model.

StructuredTool：LangChain中所有工具的基类。
StructuredTool: The base class for all tools in LangChain.

批处理：用于执行带有批处理输入runnable的可运行文件。
batch: Use to execute a runnable with batch inputs a Runnable.

bindTools：允许模型与工具交互。
bindTools: Allows models to interact with tools.

缓存：存储结果以避免对聊天模型的冗余调用。
Caching: Storing results to avoid redundant calls to a chat model.

上下文窗口：聊天模型可以处理的最大输入大小。
Context window: The maximum size of input a chat model can process.

对话模式：聊天互动中的常见模式。
Conversation patterns: Common patterns in chat interactions.

文档：LangChain对文档的表示。
Document: LangChain's representation of a document.

嵌入模型：为各种数据类型生成向量嵌入的模型。
Embedding models: Models that generate vector embeddings for various data types.

HumanMessage：表示来自人类用户的消息。
HumanMessage: Represents a message from a human user.

输入和输出类型：Runnables中用于输入和输出的类型。
input and output types: Types used for input and output in Runnables.

集成包：与LangChain集成的第三方包。
Integration packages: Third-party packages that integrate with LangChain.

invoke：调用Runnable的标准方法。
invoke: A standard method to invoke a Runnable.

JSON模式：以JSON格式返回响应。
JSON mode: Returning responses in JSON format.

@langchain/community：社区驱动的langchain组件。
@langchain/community: Community-driven components for LangChain.

@langchain/core：核心langchain包。包括基本接口和内存实现。
@langchain/core: Core langchain package. Includes base interfaces and in-memory implementations.

langchain：用于高级组件的包（例如，一些预构建的链）。
langchain: A package for higher level components (e.g., some pre-built chains).

@langchain/langgraph：langchain强大的编排层。用于构建复杂的管道和工作流。
@langchain/langgraph: Powerful orchestration layer for LangChain. Use to build complex pipelines and workflows.

管理聊天记录：维护和管理聊天记录的技术。
Managing chat history: Techniques to maintain and manage the chat history.

OpenAI格式：OpenAI用于聊天模型的消息格式。
OpenAI format: OpenAI's message format for chat models.

RunnableConfig的传播：通过Runnables传播配置。
Propagation of RunnableConfig: Propagating configuration through Runnables.

RemoveMessage：一种用于从聊天历史记录中删除消息的抽象，主要用于LangGraph。
RemoveMessage: An abstraction used to remove a message from chat history, used primarily in LangGraph.

role：表示聊天消息的角色（例如用户、助理）。
role: Represents the role (e.g., user, assistant) of a chat message.

RunnableConfig：用于将运行时信息传递给Runnables（例如，runName、runId、标签、元数据、maxConcurrency、recursionLimit、可配置）。
RunnableConfig: Use to pass run time information to Runnables (e.g., runName, runId, tags, metadata, maxConcurrency, recursionLimit, configurable).

聊天模型的标准参数：API密钥、温度和maxTokens等参数，
Standard parameters for chat models: Parameters such as API key, temperature, and maxTokens,

stream：用于流式传输Runnable或图形的输出。
stream: Use to stream output from a Runnable or a graph.

令牌化：将数据转换为令牌的过程，反之亦然。
Tokenization: The process of converting data into tokens and vice versa.

令牌：语言模型在底层读取、处理和生成的基本单位。
Tokens: The basic unit that a language model reads, processes, and generates under the hood.

工具工件：将工件添加到工具的输出中，这些工件不会发送到模型，但可用于下游处理。
Tool artifacts: Add artifacts to the output of a tool that will not be sent to the model, but will be available for downstream processing.

工具绑定：将工具绑定到模型。
Tool binding: Binding tools to models.

tool：在LangChain中创建工具的函数。
tool: Function for creating tools in LangChain.

工具包：可以一起使用的工具集合。
Toolkits: A collection of tools that can be used together.

ToolMessage：表示包含工具执行结果的消息。
ToolMessage: Represents a message that contains the results of a tool execution.

矢量存储：专门用于存储和高效搜索矢量嵌入的数据存储。
Vector stores: Datastores specialized for storing and efficiently searching vector embeddings.

withStructuredOutput：聊天模型的辅助方法，它本机支持工具调用，以获得与通过Zod、JSON模式或函数指定的给定模式匹配的结构化输出。
withStructuredOutput: A helper method for chat models that natively support tool calling to get structured output matching a given schema specified via Zod, JSON schema or a function.
