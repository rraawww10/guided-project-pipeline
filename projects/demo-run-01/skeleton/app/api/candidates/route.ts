import { NextResponse } from "next/server"
import { allCandidates } from "../../../lib/store"
import { Candidate } from "../../../lib/types"

export async function GET(): Promise<Response> {
  let body: Candidate[] = []
  let status = 501
  // TODO(cut-api-candidates-list): Put every candidate from the seed into `body` and set `status` to 200
  return NextResponse.json(body, { status })
}
