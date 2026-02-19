import { useState, useEffect, useCallback } from 'react'
import type { CommandSummary, AgentSummary, SkillTreeNode, ConfigSection, ResourceDetail } from '@/types/resource'
import * as api from '@/services/api'

export function useCommands() {
  const [commands, setCommands] = useState<CommandSummary[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      setCommands(await api.listCommands())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])
  return { commands, loading, refresh }
}

export function useCommand(name: string | null) {
  const [detail, setDetail] = useState<ResourceDetail | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!name) { setDetail(null); return }
    setLoading(true)
    api.getCommand(name).then(setDetail).finally(() => setLoading(false))
  }, [name])

  return { detail, loading }
}

export function useSkills() {
  const [tree, setTree] = useState<SkillTreeNode[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      setTree(await api.listSkills())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])
  return { tree, loading, refresh }
}

export function useSkill(path: string | null) {
  const [detail, setDetail] = useState<ResourceDetail | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!path) { setDetail(null); return }
    setLoading(true)
    api.getSkill(path).then(setDetail).finally(() => setLoading(false))
  }, [path])

  return { detail, loading }
}

export function useAgents() {
  const [agents, setAgents] = useState<AgentSummary[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      setAgents(await api.listAgents())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])
  return { agents, loading, refresh }
}

export function useAgent(name: string | null) {
  const [detail, setDetail] = useState<ResourceDetail | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!name) { setDetail(null); return }
    setLoading(true)
    api.getAgent(name).then(setDetail).finally(() => setLoading(false))
  }, [name])

  return { detail, loading }
}

export function useConfig() {
  const [sections, setSections] = useState<ConfigSection[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      setSections(await api.listConfig())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])
  return { sections, loading, refresh }
}
