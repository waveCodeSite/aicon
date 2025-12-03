from src.core.logging import get_logger
from src.services.base import SessionManagedService

logger = get_logger(__name__)


# ============================================================
# VideoService 主体
# ============================================================

class VideoService(SessionManagedService):
    def __init__(self):
        super().__init__()
        logger.info("✅ VideoService 初始化完成")
        
    
    def process_video(self, chapater_id: str):
        """
        处理视频

        Args:
            chapater_id (str): 章节id
        
        Returns:
            dict: 处理结果
        """
        
        # 1.获取章节信息,如果不是已生成素材状态，抛出异常
        
        # 2.获取所有句子
        
        # 3.用句子的素材合成句子的视频
        
        # 4.合成章节视频


video_service = VideoService()
__all__ = ["VideoService", "video_service"]

if __name__ == "__main__":
    import asyncio


    async def test():
        service = VideoService()


    asyncio.run(test())
