import { ShieldAlert, Check, X } from 'lucide-react'
import type { PermissionRequestEvent } from '@/types/event'

interface PermissionBannerProps {
  permission: PermissionRequestEvent
  onGrant: (granted: boolean) => void
}

export default function PermissionBanner({ permission, onGrant }: PermissionBannerProps) {
  return (
    <div className="mx-3 p-3 rounded-lg border-l-4 border-aws-orange bg-amber-50 dark:bg-amber-900/20">
      <div className="flex items-start gap-3">
        <ShieldAlert size={18} className="text-aws-orange mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
            Permission Required
          </p>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
            <span className="font-mono text-xs badge-blue">{permission.tool}</span>{' '}
            {permission.description}
          </p>
          {permission.blastRadius && (
            <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
              Blast radius: {permission.blastRadius}
            </p>
          )}
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => onGrant(true)}
              className="btn-primary py-1.5 px-3 text-sm flex items-center gap-1"
            >
              <Check size={14} />
              Approve
            </button>
            <button
              onClick={() => onGrant(false)}
              className="btn-secondary py-1.5 px-3 text-sm flex items-center gap-1"
            >
              <X size={14} />
              Deny
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
