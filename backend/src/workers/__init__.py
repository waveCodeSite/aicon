"""
Celery任务模块
"""

from .base import app
from .text_processing import process_document, parse_chapters
from .sentence_tasks import generate_sentence_image, generate_sentence_audio
from .image_generation import generate_images_batch
from .audio_generation import generate_audio_batch
from .timeline_tasks import process_timeline, merge_audio_tracks
from .subtitle_tasks import generate_subtitles, sync_subtitles
from .video_synthesis import synthesize_video, add_background_music
from .publication_tasks import publish_to_platform, update_publication_status

__all__ = [
    "app",
    "process_document",
    "parse_chapters",
    "generate_sentence_image",
    "generate_sentence_audio",
    "generate_images_batch",
    "generate_audio_batch",
    "process_timeline",
    "merge_audio_tracks",
    "generate_subtitles",
    "sync_subtitles",
    "synthesize_video",
    "add_background_music",
    "publish_to_platform",
    "update_publication_status",
]