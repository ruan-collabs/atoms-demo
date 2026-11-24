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

浏览器用户主动点击发送按钮旁的麦克风图标→直接申请麦克风（无业务二次确认，首次浏览器权限仍保留）→AudioWorklet单声道PCM16/16k→同源认证WS→Pipecat→官方火山双向流式→全量替换临时文字/最终确认→填入Query，用户手动发送。空闲时不显示语音说明，图标title仅为操作名称；录音、连接、收尾和错误提示按状态显示，录音时图标高亮，再点停止。不接TTS或自动LLM生成，不做实时播报。

- 精确Origin、平台登录、每owner一连接、总并发限额、每包及总音频上限、最长120秒。
- 200ms分包；供应商固定URL，DNS全部公共IP验证、TCP固定IP、原Host和TLS SNI、不读取环境代理、不跟重定向。
- 返回数据二进制协议校验、gzip解压限额、类型及文字长度上限、无原始供应商错误回显；SDK日志禁用，不保存原始音频或转写文本日志。
- 结果采用全量replace，避免同一句多次追加。停止时立即释放麦克风，保持Query编辑与发送锁定，等待最后结果/超时后释放。
- 浏览器取消/离开/退出、后台断连与错误释放上游socket/reader；断连不自动重试计费，不偷偷切Deepgram或DeepSeek批量ASR。

## 本地验收

99后端/21前端单测及TypeScript/Vite构建通过（T-027纯图标布局、点击直接申请麦克风且不调用confirm的组件测试已增加）。火山供应商WebSocket用测试替身：真实Pipecat运输、serializer、worker接受PCM，收到临时全量文字、最终文字和done；停止/上游socket关闭、拒私网DNS/重定向、结果长度/解压限制、脱敏错误都有断言。此为协议契约/管线测试，不证明真实凭证或麦克风成功。

## 部署与真实联调

火山源码8b0c413已推GitHub，固定ZIP116份文件与当时本地一致，CI https://github.com/ruan-collabs/atoms-demo/actions/runs/45369863718 成功。Railway部署Active，用户填入的四项语音变量已应用，/api/voice/status.enabled=true、provider=pipecat-volcengine，页面按钮可用。用户接管进行短录音，交回后Query变为新的测试文本且麦克风/发送恢复；执行器未直接观察interim/final事件，不能只凭输入框文本判定全部真实流式与停止资源验收通过。T-026/T-021保持待验收。

T-027用户进一步要求发送按钮旁纯麦克风图标，去除业务二次确认；99后端/21前端/构建通过，源码7485c4fa458931767f5799e0de5d7c4a8e0822aa已部署Railway Active，固定ZIP117份文件与当时本地一致，CI https://github.com/ruan-collabs/atoms-demo/actions/runs/45372756267 成功。公网工作台与本地已登录编辑器DOM几何核验：Mic紧邻发送左侧、同排、10px间距、无按钮文字；点击直接申请麦克风且不调用confirm由React组件测试断言（模拟权限拒绝，不做本轮自动录音）。未移除浏览器首次权限，录音高亮、停止收尾锁定及提示保留，不自动发送Query。最终收尾文档仅本地追加，不为说明再次部署。
