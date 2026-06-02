import { useEffect } from "react";
import { customPreLoadImageUrl } from "@/customization/utils/custom-pre-load-image-url";

/**
 * 预加载图片 Hook
 * 预加载头像图片 URL，确保图片在显示前已缓存
 */
const usePreloadImages = (
  setImagesLoaded: (value: boolean) => void,
  loading: boolean,
  profilePictures?: { [key: string]: string[] },
) => {
  const preloadImages = async (imageUrls) => {
    return Promise.all(
      imageUrls.map(
        (src) =>
          new Promise((resolve) => {
            const img = new Image();
            img.src = src;
            img.onload = resolve;
            img.onerror = resolve;
          }),
      ),
    );
  };

  useEffect(() => {
    if (loading || !profilePictures) return;
    const imageArray: string[] = [];

    Object.keys(profilePictures).flatMap((folder) =>
      profilePictures[folder].map((path) =>
        imageArray.push(customPreLoadImageUrl(`${folder}/${path}`)),
      ),
    );

    preloadImages(imageArray).then(() => {
      setImagesLoaded(true);
    });
  }, [profilePictures, loading]);

  return;
};

export default usePreloadImages;
