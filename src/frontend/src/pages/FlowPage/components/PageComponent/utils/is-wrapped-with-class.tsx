/**
 * 检查事件目标元素是否被指定 CSS 类名的元素包裹
 * 用于判断键盘事件的目标是否在特定容器内
 */
const isWrappedWithClass = (event: any, className: string | undefined) =>
  event.target.closest(`.${className}`);

export default isWrappedWithClass;
