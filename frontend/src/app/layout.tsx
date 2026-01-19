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
      <head>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Noto+Sans+SC:wght@300;400;500;700;900&family=Space+Grotesk:wght@500;700&family=Inter:wght@300;400;500;600&family=Outfit:wght@400;500;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
