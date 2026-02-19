import { useState, useEffect } from 'react'
import {
  FolderOpen, Download, Trash2, Upload, LayoutGrid, List,
  FileImage, FileText, FileCode, FileSpreadsheet, File,
} from 'lucide-react'
import type { ArtifactSummary } from '@/types/resource'
import * as api from '@/services/api'

interface ArtifactBrowserProps {
  sessionId: string | null
}

const FILE_ICONS: Record<string, React.ElementType> = {
  svg: FileImage, png: FileImage, jpg: FileImage, jpeg: FileImage, gif: FileImage,
  md: FileText, txt: FileText, log: FileText,
  py: FileCode, ts: FileCode, js: FileCode, json: FileCode, yaml: FileCode, yml: FileCode,
  dockerfile: FileCode, sh: FileCode, mmd: FileCode,
  csv: FileSpreadsheet, xlsx: FileSpreadsheet, xls: FileSpreadsheet,
}

function getIcon(name: string): React.ElementType {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  return FILE_ICONS[ext] || File
}

const SOURCE_COLORS: Record<string, string> = {
  'model-generated': 'badge-purple',
  'user-uploaded': 'badge-blue',
  'system-exported': 'badge-gray',
}

export default function ArtifactBrowser({ sessionId }: ArtifactBrowserProps) {
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list')
  const [selected, setSelected] = useState<ArtifactSummary | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    setLoading(true)
    api.listArtifacts(sessionId).then(setArtifacts).finally(() => setLoading(false))
  }, [sessionId])

  const handleDelete = async (id: string) => {
    if (!sessionId) return
    await api.deleteArtifact(sessionId, id)
    setArtifacts((prev) => prev.filter((a) => a.id !== id))
    setConfirmDelete(null)
    if (selected?.id === id) setSelected(null)
  }

  if (!sessionId) {
    return (
      <div className="p-6 text-center py-12">
        <FolderOpen size={32} className="text-slate-300 mx-auto" />
        <p className="text-sm text-slate-500 mt-3">Select a session to view its artifacts</p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <FolderOpen size={20} className="text-aws-orange" />
          Artifacts
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`btn-ghost p-1.5 ${viewMode === 'grid' ? 'bg-slate-200 dark:bg-slate-600' : ''}`}
          >
            <LayoutGrid size={16} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`btn-ghost p-1.5 ${viewMode === 'list' ? 'bg-slate-200 dark:bg-slate-600' : ''}`}
          >
            <List size={16} />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
        </div>
      ) : artifacts.length === 0 ? (
        <div className="card text-center py-12">
          <FolderOpen size={32} className="text-slate-300 mx-auto" />
          <p className="text-sm text-slate-500 mt-3">No artifacts in this session yet</p>
        </div>
      ) : viewMode === 'list' ? (
        <div className="space-y-2">
          {artifacts.map((artifact) => {
            const Icon = getIcon(artifact.name)
            return (
              <div
                key={artifact.id}
                className={`card flex items-center justify-between cursor-pointer hover:border-aws-orange/50 transition-colors ${
                  selected?.id === artifact.id ? 'border-aws-orange ring-1 ring-aws-orange/30' : ''
                }`}
                onClick={() => setSelected(artifact)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Icon size={16} className="text-slate-400 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{artifact.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-slate-400">{formatBytes(artifact.size)}</span>
                      <span className={`text-xs ${SOURCE_COLORS[artifact.source] || 'badge-gray'}`}>
                        {artifact.source}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 ml-4 shrink-0">
                  <a
                    href={api.getArtifactUrl(sessionId, artifact.id)}
                    download
                    onClick={(e) => e.stopPropagation()}
                    className="btn-ghost p-1.5"
                    title="Download"
                  >
                    <Download size={14} />
                  </a>
                  <button
                    onClick={(e) => { e.stopPropagation(); setConfirmDelete(artifact.id) }}
                    className="btn-ghost p-1.5 text-red-500"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {artifacts.map((artifact) => {
            const Icon = getIcon(artifact.name)
            return (
              <div
                key={artifact.id}
                className={`card text-center cursor-pointer hover:border-aws-orange/50 transition-colors ${
                  selected?.id === artifact.id ? 'border-aws-orange ring-1 ring-aws-orange/30' : ''
                }`}
                onClick={() => setSelected(artifact)}
              >
                <Icon size={28} className="text-slate-400 mx-auto mb-2" />
                <p className="text-xs font-medium truncate">{artifact.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">{formatBytes(artifact.size)}</p>
              </div>
            )
          })}
        </div>
      )}

      {/* Delete confirmation */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-80">
            <h3 className="font-semibold mb-2">Delete Artifact?</h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">
              This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button className="btn-secondary" onClick={() => setConfirmDelete(null)}>Cancel</button>
              <button className="btn-danger" onClick={() => handleDelete(confirmDelete)}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}
