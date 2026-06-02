# 数据库连接字符串解析工具
# 对连接字符串中的密码部分进行 URL 编码，确保特殊字符被正确处理
from urllib.parse import quote


# 将连接字符串中的密码进行 URL 编码处理
def transform_connection_string(connection_string) -> str:
    auth_part, db_url_name = connection_string.rsplit("@", 1)
    protocol_user, password_string = auth_part.rsplit(":", 1)
    encoded_password = quote(password_string)
    return f"{protocol_user}:{encoded_password}@{db_url_name}"
