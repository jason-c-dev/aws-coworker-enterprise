import { useState } from 'react'
import { Settings, Save, X, Pencil, FileText, FileCode } from 'lucide-react'
import { useConfig } from '@/hooks/useResources'
import * as api from '@/services/api'
import MarkdownRenderer from '../Common/MarkdownRenderer'

export default function ConfigBrowser() {
  const { sections, loading, refresh } = useConfig()
  const [activeTab, setActiveTab] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)

  const active = activeTab || (sections.length > 0 ? sections[0].section : null)
  const currentSection = sections.find((s) => s.section === active)

  const startEdit = () => {
    if (!currentSection) return
    setEditContent(currentSection.content)
    setEditing(true)
  }

  const handleSave = async () => {
    if (!active) return
    setSaving(true)
    try {
      await api.updateConfig(active, { content: editContent })
      setEditing(false)
      refresh()
    } finally {
      setSaving(false)
    }
  }

  // Group sections by category for better organization
  const isYaml = (section: typeof sections[0]) => section.fileType === 'yaml'

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Configuration</h2>
        {currentSection && !editing && (
          <button onClick={startEdit} className="btn-secondary flex items-center gap-1 text-sm">
            <Pencil size={14} />
            Edit
          </button>
        )}
        {editing && (
          <div className="flex gap-2">
            <button onClick={() => setEditing(false)} className="btn-secondary flex items-center gap-1 text-sm">
              <X size={14} />
              Cancel
            </button>
            <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-1 text-sm">
              <Save size={14} />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {/* Tabs */}
          <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700 mb-4 overflow-x-auto">
            {sections.map((section) => (
              <button
                key={section.section}
                onClick={() => { setActiveTab(section.section); setEditing(false) }}
                className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                  active === section.section
                    ? 'border-aws-orange text-aws-orange'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                {isYaml(section)
                  ? <FileCode size={14} className="shrink-0" />
                  : <Settings size={14} className="shrink-0" />
                }
                {section.section}
              </button>
            ))}
          </div>

          {/* Content */}
          {currentSection && (
            <div className="card">
              {editing ? (
                <div className="flex flex-col" style={{ height: 'calc(100vh - 300px)' }}>
                  <textarea
                    className="input-field font-mono text-code flex-1 min-h-0 resize-none"
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                  />
                </div>
              ) : isYaml(currentSection) ? (
                /* YAML files: syntax-highlighted preformatted text */
                <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 280px)' }}>
                  <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed text-slate-700 dark:text-slate-300">
                    {currentSection.content}
                  </pre>
                </div>
              ) : (
                /* Markdown files: rendered as markdown */
                <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 280px)' }}>
                  <MarkdownRenderer content={currentSection.content} />
                </div>
              )}
            </div>
          )}

          {sections.length === 0 && (
            <p className="text-sm text-slate-500 text-center py-8">No configuration files found</p>
          )}
        </>
      )}
    </div>
  )
}
