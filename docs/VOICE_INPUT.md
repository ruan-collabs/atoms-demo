# 实时语音输入

## 当前接入

Pipecat WebSocket运输、PCM serializer、PipelineWorker保留；默认兼容旧Deepgram，Railway本轮选择VOICE_PROVIDER=volcengine。火山供应商是自定义FrameProcessor，不假称Pipecat自带火山SDK。

火山官方参考：https://docs.volcengine.com/docs/doubao-voice/large-model-streaming-automatic-speech-recognition-api-1?lang=zh

新版控制台只需API Key，通过X-Api-Key鉴权；旧App ID/Access Token不是本次配置路径。资源ID要与开通服务匹配。固定WSS：wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async。

## Railway变量

- VOICE_PROVIDER=volcengine
- VOLC_ASR_API_KEY：用户在Railway受保护变量中提供，禁止提交源码、发到聊天或日志。
- VOLC_ASR_RESOURCE_ID：volc.seedasr.sauc.duration（2.0小时版）；也支持官方1.0/2.0小时/并发四种ID，必须匹配账号服务授权。
- VOICE_ENABLED=true（上线前可false）
- VOICE_MAX_SECONDS=60、VOICE_MAX_CONNECTIONS=2（可保留默认）

不使用DeepSeek模型Key作为火山语音Key；语音由平台火山凭证支付，生成应用由用户DeepSeek配置支付。设置变量后必须部署生效；仅名称存在不是凭证格式或授权成功证明。

## 链路与安全

浏览器用户点击并确认告知→申请麦克风→AudioWorklet单声道PCM16/16k→同源认证WS→Pipecat→官方火山双向流式→全量替换临时文字/最终确认→填入Query，用户手动发送。不接TTS或自动LLM生成，不做实时播报。

- 精确Origin、平台登录、每owner一连接、总并发限额、每包及总音频上限、最长120秒。
- 200ms分包；供应商固定URL，DNS全部公共IP验证、TCP固定IP、原Host和TLS SNI、不读取环境代理、不跟重定向。
- 返回数据二进制协议校验、gzip解压限额、类型及文字长度上限、无原始供应商错误回显；SDK日志禁用，不保存原始音频或转写文本日志。
- 结果采用全量replace，避免同一句多次追加。停止时立即释放麦克风，保持Query编辑与发送锁定，等待最后结果/超时后释放。
- 浏览器取消/离开/退出、后台断连与错误释放上游socket/reader；断连不自动重试计费，不偷偷切Deepgram或DeepSeek批量ASR。

## 本地验收

99后端/19前端单测及TypeScript/Vite构建通过。火山供应商WebSocket用测试替身：真实Pipecat运输、serializer、worker接受PCM，收到临时全量文字、最终文字和done；停止/上游socket关闭、拒私网DNS/重定向、结果长度/解压限制、脱敏错误都有断言。此为协议契约/管线测试，不证明真实凭证或麦克风成功。

## 部署与真实联调

当前准备同步GitHub/Railway；变量名称已由界面核对存在，无读取密钥值。真实麦克风/火山服务授权/费用待短录音验收，不标已完成。关联T-026，T-021整体语音验收以真实结果为准。
