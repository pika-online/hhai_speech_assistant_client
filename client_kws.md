

# 语音唤醒服务端接口文档


## WebSocket API

### 连接地址

```
ws://<server_ip>:10094
```

### 消息格式

所有消息均采用JSON格式进行传输。

#### 请求消息

```json
{
  "remote": "<action>",
  "words": ["word1", "word2"],      // 仅在"init"操作中使用
  "samples": [0.1, 0.2, ...],       // 仅在"listen"操作中使用,每次发送960点
  "sample_rate": 16000              // 仅在"listen"操作中使用
}
```

#### 响应消息

```json
{
  "code": <status_code>,
  "message": "<response_message>",
  "remote": "<action>"
}
```

### 请求参数

| 参数名       | 类型            | 描述                                                                                       |
| ------------ | --------------- | ------------------------------------------------------------------------------------------ |
| `remote`     | `string`        | 指定要执行的操作。可能的值有`init`, `deinit`, `listen`。                                    |
| `words`      | `array[string]` | 仅在`init`操作中使用，指定要监测的关键词列表。                                              |
| `samples`    | `array[int16]`  | 仅在`listen`操作中使用，包含音频数据的样本。                                                |
| `sample_rate`| `int`           | 仅在`listen`操作中使用，指定音频样本的采样率。                                              |

### 响应参数

| 参数名       | 类型            | 描述                                                                                       |
| ------------ | --------------- | ------------------------------------------------------------------------------------------ |
| `code`       | `int`           | 状态码。`0`表示成功，`1`表示失败。                                                          |
| `message`    | `string`        | 返回的响应信息。                                                                            |
| `remote`     | `string`        | 指定对应的操作。                                                                            |

## 操作说明

### 1. 初始化模型

**描述**：初始化关键词检测模型。

**请求示例**：

```json
{
  "remote": "init",
  "words": ["你好", "小明"]
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "ni3 hao3 @你好/xiao3 ming2 @小明",
  "remote": "init"
}
```

### 2. 反初始化模型

**描述**：反初始化模型并释放资源。

**请求示例**：

```json
{
  "remote": "deinit"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Deinitialization successful",
  "remote": "deinit"
}
```

### 3. 监听唤醒词

**描述**：接受音频样本并进行关键词检测。

**请求示例**：

```json
{
  "remote": "listen",
  "samples": [0.1, 0.2, ...],
  "sample_rate": 16000
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "Detected keyword: 你好",
  "remote": "listen"
}
```

## 错误处理

在发生错误时，服务端将返回`code`为`1`的响应，并在`message`字段中包含错误信息。

**响应示例**：

```json
{
  "code": 1,
  "message": "Error description here",
  "remote": "listen"
}
```

---
