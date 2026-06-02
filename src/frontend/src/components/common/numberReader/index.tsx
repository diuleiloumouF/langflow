/**
 * 数字读取组件
 * 简单的数字展示组件，以 span 标签渲染数字值。
 */
export default function NumberReader({
  number,
}: {
  number: number;
}): JSX.Element {
  return <span>{number}</span>;
}
