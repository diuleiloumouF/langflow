import { useContext } from "react";
import { AuthContext } from "@/contexts/authContext";
import { BASE_URL_API } from "@/customization/config-constants";

interface ProfileIconProps {
  className?: string;
}

/**
 * 用户头像图标组件
 * 从认证上下文获取用户数据，显示用户的个人头像图片。
 * 如果用户未设置头像，使用默认的火箭图标。
 */
export function ProfileIcon({ className }: ProfileIconProps = {}) {
  const { userData } = useContext(AuthContext);

  const profileImageUrl = `${BASE_URL_API}files/profile_pictures/${
    userData?.profile_image ?? "Space/046-rocket.svg"
  }`;

  return (
    <img
      src={profileImageUrl}
      alt="User"
      className={className ?? "h-6 w-6 shrink-0 focus-visible:outline-0"}
    />
  );
}
