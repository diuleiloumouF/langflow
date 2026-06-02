/**
 * 助手面板随机消息
 * 每个数组包含 8 个含义相同但表述不同的变体，用于在处理过程中显示随机提示文本。
 */
// Randomized messages for the assistant panel.
// Each array contains 8 paraphrased variations with the same meaning.

// 推理加载状态的标题文本（"思考中"的同义词）
// Header text for the reasoning loading state (synonyms of "Thinking")
const REASONING_HEADER_MESSAGES = [
  "Thinking...",
  "Processing...",
  "Working on it...",
  "Analyzing...",
  "Reasoning...",
  "Please wait...",
  "Just a moment...",
  "Almost there...",
];

// 推理步骤消息：分析组件需求
// Reasoning step messages
const ANALYZING_MESSAGES = [
  "Analyzing component requirements...",
  "Understanding your component needs...",
  "Reviewing the component specifications...",
  "Processing your request details...",
  "Examining the component structure...",
  "Interpreting your requirements...",
  "Breaking down the component logic...",
  "Assessing what you need...",
];

const IDENTIFYING_INPUTS_MESSAGES = [
  "Identifying input parameters...",
  "Determining required inputs...",
  "Mapping out input fields...",
  "Defining input specifications...",
  "Setting up input parameters...",
  "Configuring the inputs...",
  "Establishing input requirements...",
  "Working out the input structure...",
];

const CHECKING_DEPENDENCIES_MESSAGES = [
  "Checking installed libraries & dependencies...",
  "Verifying available dependencies...",
  "Reviewing library requirements...",
  "Scanning for needed packages...",
  "Confirming dependency availability...",
  "Checking required libraries...",
  "Validating package dependencies...",
  "Ensuring libraries are in place...",
];

const GENERATING_CODE_MESSAGES = [
  "Generating component code...",
  "Writing the component logic...",
  "Building the component code...",
  "Crafting your component...",
  "Assembling the code structure...",
  "Creating the component implementation...",
  "Producing the component code...",
  "Constructing the component...",
];

// 验证消息
// Validation messages
const VALIDATING_MESSAGES = [
  "Validating component...",
  "Checking component validity...",
  "Verifying the component...",
  "Running validation checks...",
  "Testing component integrity...",
  "Confirming component structure...",
  "Ensuring component is valid...",
  "Performing validation...",
];

const VALIDATION_FAILED_MESSAGES = [
  "Validation failed, analyzing errors...",
  "Found issues, reviewing errors...",
  "Validation unsuccessful, checking problems...",
  "Detected errors, analyzing...",
  "Component check failed, investigating...",
  "Issues found, examining errors...",
  "Validation error detected, reviewing...",
  "Problems found, analyzing issues...",
];

const RETRYING_MESSAGES = [
  "Retrying with fixes...",
  "Applying corrections and retrying...",
  "Making adjustments and trying again...",
  "Fixing issues and regenerating...",
  "Correcting errors and retrying...",
  "Implementing fixes...",
  "Addressing issues and retrying...",
  "Applying fixes and trying again...",
];

// 从消息数组中随机获取一条消息
function getRandomMessage(messages: string[]): string {
  const index = Math.floor(Math.random() * messages.length);
  return messages[index];
}

// 获取随机的思考中提示消息
export function getRandomThinkingMessage(): string {
  return getRandomMessage(REASONING_HEADER_MESSAGES);
}

// 生成后步骤中显示在输入框占位符的描述性消息
// Descriptive messages shown in the input placeholder during post-generation steps
const PLACEHOLDER_PROGRESS_MESSAGES = [
  ...ANALYZING_MESSAGES,
  ...IDENTIFYING_INPUTS_MESSAGES,
  ...CHECKING_DEPENDENCIES_MESSAGES,
  ...GENERATING_CODE_MESSAGES,
  ...VALIDATING_MESSAGES,
];

// 获取随机的占位符进度消息
export function getRandomPlaceholderMessage(): string {
  return getRandomMessage(PLACEHOLDER_PROGRESS_MESSAGES);
}
