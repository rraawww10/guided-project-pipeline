'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

import type { Bill } from '@/lib/types'

import BillView from './BillView'
import styles from './bill.module.css'

export default function BillPage() {
  const { id } = useParams<{ id: string }>()
  const [bill, setBill] = useState<Bill | null>(null)
  const [status, setStatus] = useState<'loading' | 'loaded' | 'not-found'>('loading')

  useEffect(() => {
    // >>> CUT cut-bill-fetch
    fetch(`/api/bills/${id}`).then((response) => {
      if (response.status === 200) {
        response.json().then((data: Bill) => {
          setBill(data)
          setStatus('loaded')
        })
      } else if (response.status === 404) {
        setStatus('not-found')
      }
    })
    // <<< CUT cut-bill-fetch
  }, [id])

  return (
    <main className={styles.page}>
      {status === 'loading' && <p className={styles.loading}>Loading bill</p>}
      {status === 'not-found' && (
        <>
          <p className={styles.notFound}>Bill not found</p>
          <Link href="/" className={styles.back}>
            Back to saved bills
          </Link>
        </>
      )}
      {status === 'loaded' && bill !== null && <BillView bill={bill} />}
    </main>
  )
}
