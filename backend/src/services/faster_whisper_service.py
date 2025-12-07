import os
import json
from src.core.logging import get_logger

logger = get_logger(__name__)

# 设置 HuggingFace 缓存目录
os.environ.setdefault("HF_HOME", "/tmp/huggingface")
os.environ.setdefault("TRANSFORMERS_CACHE", "/tmp/huggingface")


class WhisperTranscriptionService:
    def __init__(self, model_size="small", device="cpu", compute_type="float32"):
        """
        初始化语音识别服务（延迟加载模型）
        """
        self._model = None
        self._cc = None
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type

    def _ensure_model_loaded(self):
        """确保模型已加载"""
        if self._model is None:
            from faster_whisper import WhisperModel
            from opencc import OpenCC
            logger.info(f"正在加载 Whisper 模型: {self._model_size} ...")
            self._model = WhisperModel(self._model_size, device=self._device, compute_type=self._compute_type)
            self._cc = OpenCC("t2s")
            logger.info("模型加载完成")

    @property
    def model(self):
        self._ensure_model_loaded()
        return self._model

    @property
    def cc(self):
        self._ensure_model_loaded()
        return self._cc

    @staticmethod
    def format_timestamp(seconds: float):
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def transcribe(self, audio_path, output_format="all"):
        """
        执行语音转写任务
        :param audio_path: 音频文件路径
        :param output_format: json / srt / all
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"❌ 找不到音频文件: {audio_path}")

        logger.info(f"🚀 开始识别音频: {audio_path}")

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=10,
            vad_filter=True,
            word_timestamps=True,
            language="zh",
            task="transcribe",
            temperature=0.0,
        )

        logger.info(
            f"ℹ️ 检测语言: {info.language} (置信度: {info.language_probability:.2f})"
        )

        results = []
        srt_content = ""

        for i, segment in enumerate(segments, start=1):

            # 转成简体
            text_simplified = self.cc.convert(segment.text.strip())
            logger.info(
                f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text_simplified}"
            )

            item = {
                "id": i,
                "start": segment.start,
                "end": segment.end,
                "text": text_simplified,
                "words": [],
            }

            if segment.words:
                for w in segment.words:
                    item["words"].append(
                        {
                            "word": self.cc.convert(w.word),
                            "start": w.start,
                            "end": w.end,
                        }
                    )

            results.append(item)

            # 生成 SRT 字幕块
            srt_content += f"{i}\n"
            srt_content += f"{self.format_timestamp(segment.start)} --> {self.format_timestamp(segment.end)}\n"
            srt_content += f"{text_simplified}\n\n"

        base_name = os.path.splitext(audio_path)[0]

        # 保存 JSON
        if output_format in ["json", "all"]:
            json_path = f"{base_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ JSON 时间轴已保存: {json_path}")

        # 保存 SRT
        if output_format in ["srt", "all"]:
            srt_path = f"{base_name}.srt"
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            logger.info(f"✅ SRT 字幕已保存: {srt_path}")

        return results, srt_content


transcription_service = WhisperTranscriptionService()

all = ["WhisperTranscriptionService", "transcription_service"]


# -------------------------
# 使用方式示例
# -------------------------

if __name__ == "__main__":
    INPUT_FILE = "test.mp3"
    if not os.path.exists(INPUT_FILE):
        logger.info(f"❌ 错误: 找不到文件 {INPUT_FILE}")
    else:
        transcription_service.transcribe(INPUT_FILE, output_format="all")
