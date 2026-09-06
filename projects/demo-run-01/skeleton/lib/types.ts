export type ToggleToken = "years" | "tag"

export interface Candidate {
  id: string
  name: string
  years: number
  tags: string[]
}

export interface RankItem {
  id: string
  name: string
  score: number // rounded to two decimals in API response
  reasons: string[]
}

// Internal working item used for sorting and filtering on the server
export interface RankWorking extends RankItem {
  unrounded: number
  years: number
  hasPreferredTag: boolean
}
