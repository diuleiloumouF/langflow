import TextModal from "../../../modals/textModal";

/**
 * 字符串读取组件
 * 以截断文本形式显示字符串内容。
 * 点击可打开文本弹窗查看完整内容，支持编辑模式。
 */
export default function StringReader({
  string,
  setValue,
  editable = false,
}: {
  string: string | null;
  setValue: (value: string) => void;
  editable: boolean;
}): JSX.Element {
  return (
    <TextModal editable={editable} setValue={setValue} value={string ?? ""}>
      {/* INVISIBLE CHARACTER TO PREVENT AGgrid bug */}
      <span className="truncate">{string ?? "‎"}</span>
    </TextModal>
  );
}
