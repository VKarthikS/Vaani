import { Landing } from './landing'

export default function Page() {
  const configuredNumber = process.env.NEXT_PUBLIC_VAANI_PHONE?.trim() ?? ''
  const number = /^\+[1-9]\d{7,14}$/.test(configuredNumber) ? configuredNumber : undefined
  return <Landing phoneNumber={number} />
}
