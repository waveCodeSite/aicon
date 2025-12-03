"""
FFmpeg工具函数 - 视频处理相关的FFmpeg操作
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from src.core.logging import get_logger

logger = get_logger(__name__)


def check_ffmpeg_installed() -> bool:
    """
    检查FFmpeg是否已安装

    Returns:
        如果FFmpeg可用返回True，否则返回False
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("FFmpeg已安装并可用")
            return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.error(f"FFmpeg检查失败: {e}")
        return False


def get_audio_duration(audio_path: str) -> Optional[float]:
    """
    获取音频文件时长

    Args:
        audio_path: 音频文件路径

    Returns:
        音频时长（秒），如果失败返回None
    """
    try:
        # 使用ffprobe获取音频时长
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            duration = float(result.stdout.strip())
            logger.debug(f"音频时长: {audio_path} = {duration}秒")
            return duration
        else:
            logger.error(f"获取音频时长失败: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"获取音频时长异常: {e}")
        return None


def create_concat_file(video_paths: List[Path], output_path: Path) -> None:
    """
    创建FFmpeg concat文件

    Args:
        video_paths: 视频文件路径列表
        output_path: concat文件输出路径
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for video_path in video_paths:
                # 使用绝对路径并转义特殊字符
                abs_path = video_path.absolute()
                # FFmpeg concat文件格式: file 'path'
                f.write(f"file '{abs_path}'\n")

        logger.info(f"创建concat文件成功: {output_path}, 包含{len(video_paths)}个视频")

    except Exception as e:
        logger.error(f"创建concat文件失败: {e}")
        raise


def run_ffmpeg_command(command: List[str], timeout: int = 300) -> Tuple[bool, str, str]:
    """
    执行FFmpeg命令

    Args:
        command: FFmpeg命令列表
        timeout: 超时时间（秒），默认300秒

    Returns:
        (是否成功, 标准输出, 标准错误)
    """
    try:
        logger.info(f"执行FFmpeg命令: {' '.join(command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        success = result.returncode == 0

        if success:
            logger.info("FFmpeg命令执行成功")
        else:
            logger.error(f"FFmpeg命令执行失败: {result.stderr}")

        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        error_msg = f"FFmpeg命令执行超时（{timeout}秒）"
        logger.error(error_msg)
        return False, "", error_msg

    except Exception as e:
        error_msg = f"FFmpeg命令执行异常: {e}"
        logger.error(error_msg)
        return False, "", error_msg


def build_sentence_video_command(
        image_path: str,
        audio_path: str,
        output_path: str,
        subtitle_filter: str,
        gen_setting: dict
) -> List[str]:
    """
    构建单句视频合成命令

    Args:
        image_path: 图片路径
        audio_path: 音频路径
        output_path: 输出视频路径
        subtitle_filter: 字幕滤镜字符串
        gen_setting: 生成设置

    Returns:
        FFmpeg命令列表
    """
    # 获取音频时长
    duration = get_audio_duration(audio_path)
    if not duration:
        raise ValueError(f"无法获取音频时长: {audio_path}")

    # 解析设置
    resolution = gen_setting.get("resolution", "1920x1080")
    fps = gen_setting.get("fps", 25)
    video_codec = gen_setting.get("video_codec", "libx264")
    audio_codec = gen_setting.get("audio_codec", "aac")
    audio_bitrate = gen_setting.get("audio_bitrate", "192k")
    zoom_speed = gen_setting.get("zoom_speed", 0.0005)

    # 解析分辨率
    width, height = resolution.split('x')

    # 构建filter_complex
    # 1. 图片缩放和裁剪
    # 2. zoompan效果
    # 3. 字幕叠加
    filter_complex = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='zoom+{zoom_speed}':s={width}x{height}:d={fps}*{duration}[bg];"
        f"[bg]{subtitle_filter}[v0]"
    )

    # 构建命令
    command = [
        "ffmpeg",
        "-y",  # 覆盖输出文件
        "-loop", "1",  # 循环图片
        "-framerate", str(fps),
        "-i", image_path,  # 输入图片
        "-i", audio_path,  # 输入音频
        "-filter_complex", filter_complex,
        "-map", "[v0]",  # 映射视频流
        "-map", "1:a",  # 映射音频流
        "-c:v", video_codec,  # 视频编码器
        "-preset", "veryfast",  # 编码预设
        "-c:a", audio_codec,  # 音频编码器
        "-b:a", audio_bitrate,  # 音频比特率
        "-pix_fmt", "yuv420p",  # 像素格式
        "-shortest",  # 以最短流为准
        output_path
    ]

    return command


def concatenate_videos(video_paths: List[Path], output_path: Path, concat_file_path: Path) -> bool:
    """
    拼接多个视频文件

    Args:
        video_paths: 视频文件路径列表
        output_path: 输出视频路径
        concat_file_path: concat文件路径

    Returns:
        是否成功
    """
    try:
        # 创建concat文件
        create_concat_file(video_paths, concat_file_path)

        # 构建拼接命令
        command = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file_path),
            "-c", "copy",  # 直接复制流，不重新编码
            str(output_path)
        ]

        # 执行命令
        success, stdout, stderr = run_ffmpeg_command(command, timeout=600)

        if success:
            logger.info(f"视频拼接成功: {output_path}")
        else:
            logger.error(f"视频拼接失败: {stderr}")

        return success

    except Exception as e:
        logger.error(f"视频拼接异常: {e}")
        return False


__all__ = [
    "check_ffmpeg_installed",
    "get_audio_duration",
    "create_concat_file",
    "run_ffmpeg_command",
    "build_sentence_video_command",
    "concatenate_videos",
]
