# 视频合成服务 - 使用说明

## 1. 数据库迁移

已创建迁移文件: `migrations/versions/006_create_video_tasks_table.py`

### 执行迁移

```bash
cd backend
alembic upgrade head
```

这将创建 `video_tasks` 表及相关索引。

---

## 2. 测试单个句子视频生成

### 前提条件

1. **FFmpeg 已安装**
   ```bash
   ffmpeg -version
   ```

2. **句子有素材**
   - 句子必须有 `image_url` (图片)
   - 句子必须有 `audio_url` (音频)

### 使用测试脚本

```bash
cd backend
python scripts/test_single_sentence_video.py --sentence-id <句子UUID>
```

**示例:**
```bash
python scripts/test_single_sentence_video.py --sentence-id 123e4567-e89b-12d3-a456-426614174000
```

### 输出

- 视频将保存到: `backend/test_output/sentence_<id>.mp4`
- 日志会显示处理进度和结果

---

## 3. 关于 ffmpeg-python

### 当前实现 (subprocess)

**优点:**
- ✅ 直接控制，命令清晰可见
- ✅ 易于调试，可以直接复制命令测试
- ✅ 无额外依赖
- ✅ 完全控制超时和错误处理

**缺点:**
- ❌ 需要手动构建命令字符串
- ❌ 参数转义需要小心处理

### ffmpeg-python 方案

**优点:**
- ✅ Pythonic API，更优雅
- ✅ 自动处理参数转义
- ✅ 链式调用，代码更简洁

**缺点:**
- ❌ 额外依赖 (`pip install ffmpeg-python`)
- ❌ 调试时不直观（需要 `.compile()` 查看命令）
- ❌ 某些高级功能可能不支持

### 示例对比

**当前实现 (subprocess):**
```python
command = [
    "ffmpeg", "-y",
    "-loop", "1", "-framerate", "25",
    "-i", image_path,
    "-i", audio_path,
    "-filter_complex", filter_complex,
    "-map", "[v0]", "-map", "1:a",
    "-c:v", "libx264", "-preset", "veryfast",
    output_path
]
subprocess.run(command)
```

**ffmpeg-python 实现:**
```python
import ffmpeg

input_image = ffmpeg.input(image_path, loop=1, framerate=25)
input_audio = ffmpeg.input(audio_path)

video = (
    input_image
    .filter('scale', width=1920, height=1080, force_original_aspect_ratio='increase')
    .filter('crop', w=1920, h=1080)
    .filter('zoompan', z='zoom+0.0005', s='1920x1080', d=f'25*{duration}')
)

# 添加字幕
if subtitle_filter:
    video = video.drawtext(...)  # 需要解析subtitle_filter

output = ffmpeg.output(
    video, input_audio,
    output_path,
    vcodec='libx264',
    acodec='aac',
    preset='veryfast',
    shortest=None
)

ffmpeg.run(output, overwrite_output=True)
```

### 建议

**当前阶段保持 subprocess 实现:**

1. **项目已接近完成** - 当前实现已经工作，重构风险大
2. **调试友好** - 可以直接看到和测试 FFmpeg 命令
3. **性能相同** - 两种方式最终都调用 FFmpeg
4. **无额外依赖** - 保持项目依赖简洁

**未来考虑 ffmpeg-python:**

如果遇到以下情况可以考虑重构:
- 需要更复杂的滤镜链
- 需要动态生成大量不同的 FFmpeg 命令
- 团队更熟悉 Python API 而非命令行

---

## 4. 完整使用流程

### 4.1 创建视频任务

```python
from src.services.video_task import VideoTaskService

async def create_task():
    service = VideoTaskService()
    
    task = await service.create_video_task(
        user_id="user-uuid",
        project_id="project-uuid",
        chapter_id="chapter-uuid",
        gen_setting={
            "resolution": "1920x1080",
            "fps": 25,
            "zoom_speed": 0.0005,
            "subtitle_style": {
                "font_size": 48,
                "color": "white"
            }
        }
    )
    
    return task.id
```

### 4.2 执行视频合成

```python
from src.services.video_synthesis import video_synthesis_service

async def generate_video(task_id):
    result = await video_synthesis_service.synthesize_video(task_id)
    
    print(f"成功: {result['success']}")
    print(f"失败: {result['failed']}")
    print(f"视频: {result['video_key']}")
    print(f"时长: {result['duration']}秒")
```

### 4.3 查询任务状态

```python
from src.services.video_task import VideoTaskService

async def check_status(task_id):
    service = VideoTaskService()
    task = await service.get_video_task_by_id(task_id)
    
    print(f"状态: {task.status}")
    print(f"进度: {task.progress}%")
    
    if task.status == "completed":
        video_url = task.get_video_url(expires_hours=24)
        print(f"视频URL: {video_url}")
```

---

## 5. 故障排查

### FFmpeg 未安装
```
错误: FFmpeg未安装或不可用
解决: 安装 FFmpeg 并确保在 PATH 中
```

### 素材缺失
```
错误: 句子缺少图片/音频
解决: 确保句子已生成图片和音频素材
```

### 字体问题
```
错误: 找不到字体文件
解决: 修改 video_synthesis.py 中的字体路径
当前: /Windows/Fonts/arial.ttf
Linux: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
```

### 内存不足
```
错误: 并发处理导致内存溢出
解决: 减少并发数 (video_synthesis.py line 395)
当前: Semaphore(3)
改为: Semaphore(1) 或 Semaphore(2)
```

---

## 6. 性能优化建议

1. **调整并发数**: 根据服务器配置调整 `Semaphore` 值
2. **视频预设**: 使用 `veryfast` 预设加快编码速度
3. **分辨率**: 可以降低到 1280x720 减少处理时间
4. **跳过字幕**: 如果不需要字幕，可以返回空滤镜

---

## 7. 下一步

- [ ] 执行数据库迁移
- [ ] 测试单个句子视频生成
- [ ] 创建 API 端点
- [ ] 集成到前端
- [ ] 添加后台任务队列 (Celery)
