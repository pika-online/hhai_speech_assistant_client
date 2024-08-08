


# 自然语言理解 API 接口文档

## 基本信息

- **Base URL**: `http://<server_ip>:10096`
- **Content-Type**: `application/json`

## 端点

### 1. `/upload_words` - 上传句子列表

**描述**: 上传句子列表，用于后续的句子匹配操作。

- **方法**: `POST`
- **请求体**:
  
  ```json
  {
      "sentences_to_compare": [
          "句子1",
          "句子2",
          "句子3"
      ]
  }
  ```

- **响应**:

  - **成功**: 状态码 `200`
  
    ```json
    {
        "code": 0,
        "message": "Word list updated successfully"
    }
    ```
  
  - **失败**: 状态码 `400`
  
    ```json
    {
        "code": 1,
        "message": "sentences_to_compare not provided"
    }
    ```

### 2. `/match_sentence` - 句子匹配

**描述**: 输入句子并将其与上传的句子列表进行匹配，返回匹配度最高的句子及其匹配分数。

- **方法**: `POST`
- **请求体**:
  
  ```json
  {
      "source_sentence": "输入的句子"
  }
  ```

- **响应**:

  - **成功**: 状态码 `200`
  
    ```json
    {
        "code": 0,
        "best_match": "匹配度最高的句子",
        "score": 匹配分数
    }
    ```
  
  - **失败**: 状态码 `400`
  
    - 如果未上传句子列表：
  
      ```json
      {
          "code": 1,
          "message": "Word list is empty. Please upload words first."
      }
      ```
  
    - 如果未提供 `source_sentence`：
  
      ```json
      {
          "code": 1,
          "message": "source_sentence not provided"
      }
      ```

## 错误处理

- **状态码 `400`** 表示请求格式错误或缺少必需字段。
- **状态码 `200`** 表示操作成功。

