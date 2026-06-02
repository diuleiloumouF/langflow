import DictAreaModal from "../../../modals/dictAreaModal";

/**
 * 对象渲染组件
 * 将对象或JSON字符串渲染为可读的预览文本。
 * 点击可打开字典区域弹窗查看完整内容和编辑。
 */
export default function ObjectRender({
  object,
  setValue,
}: {
  object: any;
  setValue?: (value: any) => void;
}): JSX.Element {
  let newObject = object;
  // 尝试将字符串解析为JSON对象
  if (typeof object === "string") {
    try {
      newObject = JSON.parse(object);
    } catch (_e) {
      newObject = object;
    }
  }
  // 生成预览文本，null/undefined 显示为空白
  const preview =
    newObject === null || newObject === undefined
      ? "‎"
      : JSON.stringify(newObject);
  return (
    <DictAreaModal onChange={setValue} value={newObject ?? {}}>
      <div className="flex h-full w-full items-center align-middle transition-all">
        <div className="truncate">{preview}</div>
      </div>
    </DictAreaModal>
  );
}
