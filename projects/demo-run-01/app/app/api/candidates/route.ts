import { NextResponse } from "next/server"
import { allCandidates } from "../../../lib/store"
import { Candidate } from "../../../lib/types"

export async function GET(): Promise<Response> {
  let body: Candidate[] = []
  let status = 501
  // >>> CUT cut-api-candidates-list
  body = allCandidates()
  status = 200
  // <<< CUT cut-api-candidates-list
  return NextResponse.json(body, { status })
}
