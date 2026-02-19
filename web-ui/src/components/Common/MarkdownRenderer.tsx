import { Children, isValidElement } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownRendererProps {
  content: string
  className?: string
}

/**
 * Checks if a string contains pipe-table syntax (e.g., "| col | col |").
 * Requires at least a header row and a separator row (|---|---|).
 */
function containsPipeTable(text: string): boolean {
  return /^\|.+\|$/m.test(text) && /^\|[-:\s|]+\|$/m.test(text)
}

/**
 * Extracts text content from a React element tree (the <code> inside <pre>).
 */
function extractText(node: React.ReactNode): string {
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (isValidElement(node) && node.props.children) {
    return extractText(node.props.children)
  }
  return ''
}

/** Shared table component overrides for both top-level and code-block tables */
const tableComponents = {
  table: ({ children }: { children?: React.ReactNode }) => (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full text-sm border border-slate-200 dark:border-slate-700 rounded">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }: { children?: React.ReactNode }) => (
    <thead className="bg-slate-50 dark:bg-slate-800">{children}</thead>
  ),
  th: ({ children }: { children?: React.ReactNode }) => (
    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
      {children}
    </th>
  ),
  td: ({ children }: { children?: React.ReactNode }) => (
    <td className="px-3 py-2 text-xs text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">
      {children}
    </td>
  ),
}

/**
 * Renders a fenced code block that contains a mix of text and pipe tables.
 * Splits the content: plain text lines become styled <pre> blocks,
 * pipe-table lines get re-parsed through ReactMarkdown so they render as real tables.
 */
function RichCodeBlock({ text }: { text: string }) {
  // Split into segments: table chunks vs non-table chunks
  const lines = text.split('\n')
  const segments: { type: 'text' | 'table'; content: string }[] = []
  let currentType: 'text' | 'table' | null = null
  let buffer: string[] = []

  for (const line of lines) {
    const isTableLine = /^\|.+\|$/.test(line.trim())
    const lineType: 'text' | 'table' = isTableLine ? 'table' : 'text'

    if (lineType !== currentType) {
      if (currentType !== null && buffer.length > 0) {
        segments.push({ type: currentType, content: buffer.join('\n') })
      }
      buffer = [line]
      currentType = lineType
    } else {
      buffer.push(line)
    }
  }
  if (currentType !== null && buffer.length > 0) {
    segments.push({ type: currentType, content: buffer.join('\n') })
  }

  return (
    <div className="mb-3 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      {segments.map((seg, i) =>
        seg.type === 'table' ? (
          <div key={i} className="px-1">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={tableComponents}>
              {seg.content}
            </ReactMarkdown>
          </div>
        ) : (
          <pre
            key={i}
            className="px-3 py-2 text-xs font-mono bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-300 overflow-x-auto whitespace-pre-wrap"
          >
            {seg.content.replace(/^\n+|\n+$/g, '')}
          </pre>
        ),
      )}
    </div>
  )
}

/**
 * Renders markdown content with proper styling for headings, lists, code blocks, tables, etc.
 * Uses remark-gfm for GitHub Flavored Markdown (pipe tables, strikethrough, task lists).
 * Code blocks that contain pipe tables are rendered as real HTML tables.
 * Used in view mode for Commands, Skills, Agents, and Config (markdown files).
 */
export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`prose prose-sm dark:prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-bold mt-6 mb-3 pb-1 border-b border-slate-200 dark:border-slate-700">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold mt-5 mb-2 pb-1 border-b border-slate-200 dark:border-slate-700">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold mt-4 mb-2">{children}</h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-sm font-semibold mt-3 mb-1">{children}</h4>
          ),

          // Paragraphs
          p: ({ children }) => (
            <p className="text-sm leading-relaxed mb-3 text-slate-700 dark:text-slate-300">{children}</p>
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="list-disc pl-5 mb-3 space-y-1 text-sm text-slate-700 dark:text-slate-300">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 mb-3 space-y-1 text-sm text-slate-700 dark:text-slate-300">{children}</ol>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,

          // Code (inline only — block code is handled by the pre override)
          code: ({ className: cn, children, ...props }) => {
            const isBlock = cn?.includes('language-')
            if (isBlock) {
              return (
                <code
                  className={`block bg-slate-100 dark:bg-slate-900 rounded p-3 text-xs font-mono overflow-x-auto ${cn || ''}`}
                  {...props}
                >
                  {children}
                </code>
              )
            }
            return (
              <code className="bg-slate-100 dark:bg-slate-900 rounded px-1.5 py-0.5 text-xs font-mono text-aws-orange" {...props}>
                {children}
              </code>
            )
          },

          // Pre — detect pipe tables inside code blocks and render them as real tables
          pre: ({ children }) => {
            const text = extractText(children)

            // If this code block contains pipe tables, render as a rich block
            if (containsPipeTable(text)) {
              return <RichCodeBlock text={text} />
            }

            // Check if the child <code> has a language class (e.g., ```bash)
            const childArray = Children.toArray(children)
            const codeChild = childArray.find(
              (c) => isValidElement(c) && (c.props as Record<string, unknown>).className,
            )
            const hasLang =
              codeChild &&
              isValidElement(codeChild) &&
              typeof (codeChild.props as Record<string, unknown>).className === 'string' &&
              ((codeChild.props as Record<string, unknown>).className as string).includes('language-')

            if (hasLang) {
              // Language-tagged code blocks are handled by the code override above
              return <pre className="mb-3 overflow-x-auto">{children}</pre>
            }

            // Plain fenced code blocks (no language) — style as a card
            return (
              <pre className="mb-3 bg-slate-100 dark:bg-slate-900 rounded-lg p-3 text-xs font-mono text-slate-700 dark:text-slate-300 overflow-x-auto whitespace-pre-wrap">
                {children}
              </pre>
            )
          },

          // Tables (top-level, parsed by remark-gfm)
          ...tableComponents,

          // Block quotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-3 border-aws-orange pl-4 italic text-sm text-slate-600 dark:text-slate-400 mb-3">
              {children}
            </blockquote>
          ),

          // Horizontal rule
          hr: () => <hr className="border-slate-200 dark:border-slate-700 my-4" />,

          // Strong/em
          strong: ({ children }) => <strong className="font-semibold text-slate-800 dark:text-slate-200">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,

          // Links
          a: ({ href, children }) => (
            <a href={href} className="text-aws-orange hover:underline" target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
