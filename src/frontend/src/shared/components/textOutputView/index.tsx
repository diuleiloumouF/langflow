import { Textarea } from "../../../components/ui/textarea";

/**
 * 文本输出视图组件
 * 用于展示文本类型的输出结果，支持长文本截断提示
 */
const TextOutputView = ({
  left,
  value,
}: {
  // 是否靠左对齐
  left: boolean | undefined;
  // 要显示的值
  value: any;
}) => {
  // 如果值是对象且包含 text 属性，则提取 text 字段
  if (typeof value === "object" && Object.keys(value).includes("text")) {
    value = value.text;
  }

  // 判断文本是否超过 20000 字符被截断
  const isTruncated = value?.length > 20000;

  return (
    <>
      {" "}
      <Textarea
        className={`w-full resize-none custom-scroll ${left ? "min-h-32" : "h-full"}`}
        placeholder={"Empty"}
        readOnly
        value={value}
      />
      {isTruncated && (
        <div className="mt-2 text-xs text-muted-foreground">
          This output has been truncated due to its size.
        </div>
      )}
    </>
  );
};

export default TextOutputView;
