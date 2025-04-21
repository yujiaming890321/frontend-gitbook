# LLM

## 如何检索本地数据

history+question -> LLM -> standalone question -> OpenAI embed (check for relevant documents that are embedded)-> VectorStore (store your embedding)-> relevant docs -> standalone question + relevant docs -> OpenAI -> answer

### Embedding

普通数据转为向量数据，称为 Embedding

## 如何把数据存储

pdf -> canvert to text -> splot the text into chunks -> craete embedding
