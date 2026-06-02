from sqlalchemy import select

from langflow.services.database.models.folder.model import Folder


async def generate_unique_folder_name(folder_name, user_id, session):
    """为指定用户生成唯一的文件夹名称。

    如果用户已存在同名文件夹，则在名称后追加数字后缀 (1), (2), ... 直到名称唯一为止。
    """
    original_name = folder_name
    n = 1
    while True:
        # Check if a project with the given name exists
        # 检查是否已存在同名文件夹
        existing_folder = (
            await session.exec(
                select(Folder).where(
                    Folder.name == folder_name,
                    Folder.user_id == user_id,
                )
            )
        ).first()

        # If no project with the given name exists, return the name
        # 如果不存在同名文件夹，直接返回当前名称
        if not existing_folder:
            return folder_name

        # If a project with the name already exists, append (n) to the name and increment n
        # 如果已存在同名文件夹，追加数字后缀并递增计数器
        folder_name = f"{original_name} ({n})"
        n += 1
