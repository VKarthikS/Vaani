import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import '@fontsource-variable/inter'
import '@fontsource-variable/anek-telugu'
import '@fontsource-variable/anek-devanagari'
import './site.css'

export const metadata: Metadata = {
  title: 'Vaani — Book it by voice',
  description: 'A multilingual AI voice receptionist for restaurant and hospital bookings.',
}

export default function Layout({ children }: { children: ReactNode }) {
  return <html lang="en"><body>{children}</body></html>
}
