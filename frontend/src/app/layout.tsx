import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Stock Trading Competition',
  description: 'A股AI模拟交易竞赛平台',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
