import { useState } from 'react'
import { BookOpen, ChevronRight, ChevronDown, FileText, Folder, ArrowLeft, Pencil } from 'lucide-react'
import { useSkills, useSkill } from '@/hooks/useResources'
import * as api from '@/services/api'
import ResourceEditor from '../Common/ResourceEditor'
import MarkdownRenderer from '../Common/MarkdownRenderer'
import type { SkillTreeNode } from '@/types/resource'

export default function SkillBrowser() {
  const { tree, loading } = useSkills()
  const [selectedPath, setSelectedPath] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const { detail, loading: detailLoading } = useSkill(selectedPath)

  if (selectedPath && detail) {
    return (
      <div className="p-6">
        <button onClick={() => { setSelectedPath(null); setEditing(false) }} className="btn-ghost flex items-center gap-1 mb-4 text-sm">
          <ArrowLeft size={14} />
          Back to skills
        </button>

        {editing ? (
          <ResourceEditor
            resource={detail}
            onSave={async (metadata, content) => {
              await api.updateSkill(selectedPath, { metadata, content })
              setEditing(false)
            }}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <BookOpen size={20} className="text-aws-orange" />
                  {detail.name}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
                  {selectedPath}
                </p>
              </div>
              <button onClick={() => setEditing(true)} className="btn-secondary flex items-center gap-1 text-sm">
                <Pencil size={14} />
                Edit
              </button>
            </div>

            {Object.keys(detail.metadata).length > 0 && (
              <div className="card mb-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {Object.entries(detail.metadata).map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">{key}</dt>
                      <dd className="mt-0.5 font-mono text-code">
                        {Array.isArray(value) ? value.join(', ') : String(value)}
                      </dd>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="card overflow-y-auto" style={{ maxHeight: 'calc(100vh - 280px)' }}>
              <MarkdownRenderer content={detail.content} />
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-4">Skills</h2>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="card">
          <TreeView nodes={tree} onSelect={(path) => setSelectedPath(path)} depth={0} />
        </div>
      )}
    </div>
  )
}

function TreeView({
  nodes,
  onSelect,
  depth,
}: {
  nodes: SkillTreeNode[]
  onSelect: (path: string) => void
  depth: number
}) {
  return (
    <div>
      {nodes.map((node) => (
        <TreeNode key={node.path || node.name} node={node} onSelect={onSelect} depth={depth} />
      ))}
    </div>
  )
}

function TreeNode({
  node,
  onSelect,
  depth,
}: {
  node: SkillTreeNode
  onSelect: (path: string) => void
  depth: number
}) {
  const [expanded, setExpanded] = useState(depth < 1)
  const isDir = node.type === 'directory'
  const hasChildren = isDir && node.children && node.children.length > 0

  return (
    <div>
      <button
        onClick={() => {
          if (isDir) setExpanded(!expanded)
          else onSelect(node.path)
        }}
        className="w-full flex items-center gap-2 px-2 py-1.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 rounded transition-colors"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {isDir ? (
          <>
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <Folder size={14} className="text-aws-orange" />
          </>
        ) : (
          <>
            <span className="w-3.5" />
            <FileText size={14} className="text-slate-400" />
          </>
        )}
        <span className={isDir ? 'font-medium' : ''}>{node.name}</span>
      </button>

      {isDir && expanded && hasChildren && (
        <TreeView nodes={node.children!} onSelect={onSelect} depth={depth + 1} />
      )}
    </div>
  )
}
