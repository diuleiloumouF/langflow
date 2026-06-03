import { type ReactNode, useState } from "react";
import Markdown from "react-markdown";
import rehypeMathjax from "rehype-mathjax/browser";
import remarkGfm from "remark-gfm";
import type { ContentType, JSONValue } from "@/types/chat";
import { extractLanguage, isCodeBlock } from "@/utils/codeBlockUtils";
import ForwardedIconComponent from "../../common/genericIconComponent";
import { Dialog, DialogContent, DialogTitle } from "../../ui/dialog";
import SimplifiedCodeTabComponent from "../codeTabsComponent";
import DurationDisplay from "./DurationDisplay";

const VIDEO_EXTENSIONS = [".mp4", ".webm", ".mov", ".m4v", ".ogg"];

function isVideoUrl(url: string): boolean {
  if (url.startsWith("data:video/")) {
    return true;
  }

  const normalizedUrl = url.split("?")[0]?.split("#")[0]?.toLowerCase() ?? "";
  return VIDEO_EXTENSIONS.some((extension) =>
    normalizedUrl.endsWith(extension),
  );
}

export default function ContentDisplay({
  content,
  chatId,
  playgroundPage,
}: {
  content: ContentType;
  chatId: string;
  playgroundPage?: boolean;
}) {
  const [copiedMediaUrl, setCopiedMediaUrl] = useState<string | null>(null);
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null);

  const copyMediaUrl = (url: string) => {
    if (!navigator.clipboard?.writeText) {
      return;
    }

    navigator.clipboard.writeText(url).then(() => {
      setCopiedMediaUrl(url);
      setTimeout(() => {
        setCopiedMediaUrl((currentUrl) =>
          currentUrl === url ? null : currentUrl,
        );
      }, 1500);
    });
  };

  const renderDuration = content.duration !== undefined && !playgroundPage && (
    <div className="absolute right-2 top-4">
      <DurationDisplay duration={content.duration} chatId={chatId} />
    </div>
  );

  // Then render the specific content based on type
  let contentData: ReactNode | null = null;
  switch (content.type) {
    case "text":
      contentData = (
        <div className="ml-1 pr-20">
          <Markdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeMathjax]}
            className="markdown prose max-w-full text-sm font-normal dark:prose-invert"
            components={{
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer">
                  {props.children}
                </a>
              ),
              p({ node, ...props }) {
                return (
                  <span className="block w-fit max-w-full">
                    {props.children}
                  </span>
                );
              },
              pre({ node, ...props }) {
                return <>{props.children}</>;
              },
              code: ({ node, className, children, ...props }) => {
                let content = children as string;
                if (
                  Array.isArray(children) &&
                  children.length === 1 &&
                  typeof children[0] === "string"
                ) {
                  content = children[0] as string;
                }
                if (typeof content === "string") {
                  if (content.length) {
                    if (content[0] === "▍") {
                      return <span className="form-modal-markdown-span"></span>;
                    }
                  }

                  if (isCodeBlock(className, props, content)) {
                    return (
                      <SimplifiedCodeTabComponent
                        language={extractLanguage(className)}
                        code={String(content).replace(/\n$/, "")}
                      />
                    );
                  }

                  return (
                    <code className={className} {...props}>
                      {content}
                    </code>
                  );
                }
              },
            }}
          >
            {String(content.text)}
          </Markdown>
        </div>
      );
      break;

    case "code":
      contentData = (
        <div className="pr-20">
          <SimplifiedCodeTabComponent
            language={content.language}
            code={content.code}
          />
        </div>
      );
      break;

    case "json":
      contentData = (
        <div className="pr-20">
          <SimplifiedCodeTabComponent
            language="json"
            code={JSON.stringify(content.data, null, 2)}
          />
        </div>
      );
      break;

    case "error":
      contentData = (
        <div className="text-destructive">
          {content.reason && <div>Reason: {content.reason}</div>}
          {content.solution && <div>Solution: {content.solution}</div>}
          {content.traceback && (
            <SimplifiedCodeTabComponent
              language="text"
              code={content.traceback}
            />
          )}
        </div>
      );
      break;

    case "tool_use": {
      const formatToolOutput = (output: JSONValue) => {
        if (output === null || output === undefined) return "";

        // If it's a string, render as markdown
        if (typeof output === "string") {
          return (
            <Markdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeMathjax]}
              className="markdown prose max-w-full text-sm font-normal dark:prose-invert"
              components={{
                pre({ node, ...props }) {
                  return <>{props.children}</>;
                },
                ol({ node, ...props }) {
                  return <ol className="max-w-full">{props.children}</ol>;
                },
                ul({ node, ...props }) {
                  return <ul className="max-w-full">{props.children}</ul>;
                },
                code: ({ node, className, children, ...props }) => {
                  const content = String(children);
                  if (isCodeBlock(className, props, content)) {
                    return (
                      <SimplifiedCodeTabComponent
                        language={extractLanguage(className)}
                        code={content.replace(/\n$/, "")}
                      />
                    );
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {output}
            </Markdown>
          );
        }

        // For objects/arrays, format as JSON
        try {
          return (
            <SimplifiedCodeTabComponent
              language="json"
              code={JSON.stringify(output, null, 2)}
            />
          );
        } catch {
          return String(output);
        }
      };

      contentData = (
        <div className="flex flex-col gap-2">
          <Markdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeMathjax]}
            className="markdown prose max-w-full text-sm font-normal dark:prose-invert"
          >
            **Input:**
          </Markdown>
          <SimplifiedCodeTabComponent
            language="json"
            code={JSON.stringify(content.tool_input, null, 2)}
          />
          {content.output !== undefined && (
            <>
              <Markdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeMathjax]}
                className="markdown prose max-w-full text-sm font-normal dark:prose-invert"
              >
                **Output:**
              </Markdown>
              <div className="mt-1">{formatToolOutput(content.output)}</div>
            </>
          )}
          {content.error != null && (
            <div className="text-destructive">
              <Markdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeMathjax]}
                className="markdown prose max-w-full text-sm font-normal dark:prose-invert"
              >
                **Error:**
              </Markdown>
              <SimplifiedCodeTabComponent
                language="json"
                code={JSON.stringify(content.error, null, 2)}
              />
            </div>
          )}
        </div>
      );
      break;
    }

    case "media":
      contentData = (
        <div className="flex flex-col gap-3">
          {content.urls.map((url, index) => (
            <div
              key={`${url}-${index}`}
              className="group relative overflow-hidden rounded-md border"
            >
              <button
                type="button"
                aria-label="Copy media URL"
                className="absolute right-2 top-2 z-10 flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background/90 text-muted-foreground opacity-100 shadow-sm backdrop-blur transition hover:bg-muted hover:text-foreground sm:opacity-0 sm:group-hover:opacity-100"
                data-testid={`copy-media-url-${index}`}
                onClick={(event) => {
                  event.stopPropagation();
                  copyMediaUrl(url);
                }}
              >
                <ForwardedIconComponent
                  name={copiedMediaUrl === url ? "Check" : "Copy"}
                  className="h-4 w-4"
                />
              </button>
              {isVideoUrl(url) ? (
                <video
                  src={url}
                  controls
                  className="max-h-[480px] w-full bg-black"
                  data-testid={`media-video-${index}`}
                >
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    Open video
                  </a>
                </video>
              ) : (
                <button
                  type="button"
                  className="relative flex w-full cursor-zoom-in items-center justify-center bg-muted/30"
                  aria-label="Preview image"
                  data-testid={`preview-media-image-${index}`}
                  onClick={() => setPreviewImageUrl(url)}
                >
                  <img
                    src={url}
                    alt={content.caption || `Media ${index}`}
                    className="max-h-[480px] w-full object-contain"
                    data-testid={`media-image-${index}`}
                  />
                  <span className="pointer-events-none absolute left-2 top-2 flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background/90 text-muted-foreground opacity-100 shadow-sm backdrop-blur transition group-hover:text-foreground sm:opacity-0 sm:group-hover:opacity-100">
                    <ForwardedIconComponent name="ZoomIn" className="h-4 w-4" />
                  </span>
                </button>
              )}
            </div>
          ))}
        </div>
      );
      break;
  }

  return (
    <div className="relative p-[16px]">
      {renderDuration}
      {contentData}
      <Dialog
        open={previewImageUrl !== null}
        onOpenChange={(open) => {
          if (!open) {
            setPreviewImageUrl(null);
          }
        }}
      >
        <DialogContent
          className="max-h-[92vh] w-[min(96vw,1200px)] max-w-none border-border bg-background/95 p-3 shadow-2xl backdrop-blur"
          closeButtonClassName="right-3 top-3 bg-background/90 shadow-sm"
        >
          <DialogTitle className="sr-only">Image preview</DialogTitle>
          {previewImageUrl && (
            <div className="flex max-h-[86vh] items-center justify-center overflow-hidden rounded-lg bg-black/5">
              <img
                src={previewImageUrl}
                alt="Preview"
                className="max-h-[86vh] max-w-full object-contain"
                data-testid="media-image-preview"
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
