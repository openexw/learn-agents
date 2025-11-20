import json

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple, ChannelVersions,
)
from typing import Any

import pickle
class FileSaver(BaseCheckpointSaver):
    def __init__(self,*, base_path="./data/checkpoint"):
        super.__init__()
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        checkpoint_path = self._get_checkpoint_path(thread_id, checkpoint_id)
        checkpoint_data = {
            "checkpoint": self._serialize_data(checkpoint),
            "metadata": self._serialize_data(metadata),
        }

        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

            return {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                }
            }

    def _get_checkpoint_path(self, thread_id: str, checkpoint_id: str) -> Path:
        """获取 checkpoint 文件路径"""
        return self.base_path / f"{thread_id}_{checkpoint_id}.json"


    def _serialize_data(obj: Any) -> str:
        """序列化数据为 JSON 可存储的格式"""
        try:
            import base64
            pickled = pickle.dumps(obj)
            return base64.b64encode(pickled).decode('ascii')
        except Exception as e:
            print(f"序列化失败: {e}")
            return None