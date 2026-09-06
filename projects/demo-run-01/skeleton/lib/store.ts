import { CANDIDATES } from "../data/candidates"
import { Candidate } from "./types"

export const PREFERRED_TAG = "typescript"

export function allCandidates(): Candidate[] {
  return CANDIDATES
}
