'use client'

import { useEffect, useState } from 'react'
import { tradingWebSocket } from '@/services/websocket'

// 数字滚动组件
const RollingDigit = ({ digit, previousDigit }: { digit: string; previousDigit: string }) => {
    // 强制状态重置，确保每次数字变化都能触发动画，即使是从不同值变为相同值（虽然这里是逐位比较）
    // 实际上更重要的是确保key变化或者状态能正确响应props变化

    // 我们不需要额外的状态来跟踪是否滚动，而是利用 key 的变化(在RollingPrice中处理)或者CSS类名的变化
    // 但为了简单的进入动画，我们可以比较 prop 变化

    const [prev, setPrev] = useState(previousDigit)
    const [current, setCurrent] = useState(digit)
    const [animating, setAnimating] = useState(false)

    useEffect(() => {
        if (digit !== current) {
            setPrev(current)
            setCurrent(digit)
            setAnimating(true)
            const timer = setTimeout(() => setAnimating(false), 500) // 动画时间
            return () => clearTimeout(timer)
        }
    }, [digit, current])

    if (digit === '.' || digit === ' ') {
        return <span className="inline-block text-center" style={{ width: '0.4em' }}>{digit}</span>
    }

    // 更新逻辑: 如果正在动画，显示旧值向上滚动消失，新值向上滚动出现
    // 使用transform translate

    return (
        <span className="inline-block relative overflow-hidden h-[1.2em] w-[0.65em] align-bottom">
            {/* 旧数字：向上移出 */}
            <span
                className={`absolute left-0 w-full text-center transition-transform duration-500 ease-in-out ${animating ? '-translate-y-full opacity-0' : '-translate-y-full opacity-0 hidden'
                    }`}
            >
                {prev}
            </span>

            {/* 新数字：从下移入或者保持原位 */}
            {/* 如果没有动画（初始状态或动画结束），它应该在原位 translate-y-0 */}
            {/* 如果正在动画，它应该从 translate-y-full 移动到 translate-y-0 */}

            <span
                className={`absolute left-0 w-full text-center transition-transform duration-500 ease-in-out ${animating ? 'translate-y-0' : 'translate-y-0'
                    }`}
            // 当animating为true时，我们需要一个从下往上的动画
            // 但 React 的重渲染机制可能导致直接显示为终态
            // 这里使用key来触发重新挂载可能更简单，或者使用 CSS animation 而不是 transition
            >
                {/* 简化方案：使用两个span，一个代表"当前显示的"，一个代表"即将离开的" */}
                {/* 实际上，上面的实现稍微有点复杂。我们可以简化为：
                    如果不相等，就渲染一个正在滚动的容器。
                */}
            </span>

            {/* 第三次尝试：更加稳健的滚动实现 */}
            <div className={`flex flex-col transition-transform duration-500 ease-in-out ${animating ? '-translate-y-1/2' : 'translate-y-0'}`}>
                {/* 正常显示状态 (静止时) */}
                <span className="h-[1.2em] flex items-center justify-center">{animating ? prev : current}</span>
                {/* 滚动时的下一状态 */}
                <span className="h-[1.2em] flex items-center justify-center">{current}</span>
            </div>
        </span>
    )
}

// 修正后的简单版本 RollingDigit
const SimpleRollingDigit = ({ digit, previousDigit }: { digit: string; previousDigit: string }) => {
    const isChanged = digit !== previousDigit && previousDigit !== ' ';

    // 如果没有变化，直接显示
    if (!isChanged) {
        if (digit === '.' || digit === ',') return <span className="inline-block w-[0.3em] text-center">{digit}</span>;
        return <span className="inline-block w-[0.6em] text-center">{digit}</span>;
    }

    return (
        <span className="inline-block relative overflow-hidden h-[1.3em] w-[0.6em] align-top">
            <div className="flex flex-col animate-slide-up">
                <span className="h-[1.3em] flex items-center justify-center">{previousDigit}</span>
                <span className="h-[1.3em] flex items-center justify-center">{digit}</span>
            </div>
        </span>
    );
}

// CSS 动画需要在全局添加，或者我们使用内联样式 + transition
// 让我们使用内联 translate 实现更可控的动画

const TransitionRollingDigit = ({ digit, previousDigit }: { digit: string; previousDigit: string }) => {
    const [displayDigit, setDisplayDigit] = useState(digit);
    const [prevDisplayDigit, setPrevDisplayDigit] = useState(previousDigit);
    const [animating, setAnimating] = useState(false);
    const [key, setKey] = useState(0); // 用于强制重启动画

    useEffect(() => {
        if (digit !== displayDigit) {
            setPrevDisplayDigit(displayDigit);
            setDisplayDigit(digit);
            setAnimating(true);
            setKey(k => k + 1); // 强制重新渲染动画元素
            const timer = setTimeout(() => setAnimating(false), 500);
            return () => clearTimeout(timer);
        }
    }, [digit, displayDigit]);

    const isSymbol = digit === '.' || digit === ',';
    // 稍微调整宽度以适应不同的符号
    const widthClass = isSymbol ? 'w-[0.35em]' : 'w-[0.65em]';

    if (!animating) {
        return <span className={`inline-block ${widthClass} text-center`}>{digit}</span>;
    }

    return (
        <span className={`inline-block relative overflow-hidden h-[1.2em] ${widthClass} align-bottom`}>
            {/* 定义动画 */}
            <style jsx={true}>{`
                @keyframes slideUp {
                    from { transform: translateY(0); }
                    to { transform: translateY(-1.2em); }
                }
            `}</style>
            <div
                key={key}
                className="flex flex-col"
                style={{ animation: 'slideUp 0.5s ease-out forwards' }}
            >
                <span className="h-[1.2em] flex items-center justify-center">{prevDisplayDigit}</span>
                <span className="h-[1.2em] flex items-center justify-center">{displayDigit}</span>
            </div>
        </span>
    );
};

// 价格滚动组件
const RollingPrice = ({ price, previousPrice }: { price: string; previousPrice: string }) => {
    const priceStr = price;
    const prevPriceStr = previousPrice;

    // 补齐长度，确保每一位都能对应上
    const maxLen = Math.max(priceStr.length, prevPriceStr.length);
    // 从左边补齐还是右边？金额通常是对齐小数点的。
    // 简单起见，假设都有两位小数，并且我们希望对齐小数点。
    // 因为使用了 toFixed(2)，小数点位置是固定的倒数第三位。
    // 所以直接 padStart 是安全的。

    const paddedPrice = priceStr.padStart(maxLen, ' ');
    const paddedPrevPrice = prevPriceStr.padStart(maxLen, ' ');

    return (
        <span className="font-mono flex items-baseline justify-end tabular-nums tracking-tighter">
            {paddedPrice.split('').map((digit, index) => (
                <TransitionRollingDigit
                    key={index}
                    digit={digit}
                    previousDigit={paddedPrevPrice[index] || ' '}
                />
            ))}
        </span>
    )
}

interface StockPrice {
    code: string
    name: string
    price: number
    change_percent?: number
}

export default function StockTickerBar() {
    const [stocks, setStocks] = useState<StockPrice[]>([])
    const [previousPrices, setPreviousPrices] = useState<{ [code: string]: number }>({})

    useEffect(() => {
        // 连接并监听消息
        tradingWebSocket.connect()

        const handleMessage = (data: any) => {
            console.log('StockTickerBar received message:', data.type)
            // 从 trading WebSocket 接收行情数据
            if (data.type === 'trading_update' && data.data?.quotes) {
                console.log('StockTickerBar quotes data:', data.data.quotes)

                // 更新股票数据
                const stockData: StockPrice[] = data.data.quotes.map((quote: any) => ({
                    code: quote.code,
                    name: quote.name || quote.code,
                    price: quote.price || 0,
                    change_percent: quote.change_percent
                }))

                // 在设置新数据前，保存当前的价格作为previousPrices
                setStocks(prevStocks => {
                    const newPrevPrices: { [code: string]: number } = {}
                    prevStocks.forEach(stock => {
                        newPrevPrices[stock.code] = stock.price
                    })
                    setPreviousPrices(newPrevPrices)
                    return stockData
                })

                console.log('StockTickerBar updated with', stockData.length, 'stocks')
            }
        }

        tradingWebSocket.onMessage(handleMessage)

        return () => {
            tradingWebSocket.offMessage(handleMessage)
            tradingWebSocket.disconnect()
        }
    }, []) // 空依赖数组，只运行一次

    if (stocks.length === 0) {
        return (
            <div className="border-b-2 border-border bg-gray-50 px-4 py-2">
                <div className="flex items-center justify-center gap-2">
                    <span className="text-xs text-gray-500">加载股票行情中...</span>
                </div>
            </div>
        )
    }

    return (
        <div className="border-b-2 border-border bg-gray-50 px-4 py-2">
            <div className="flex items-center justify-between gap-6 overflow-x-auto">
                {stocks.map((stock) => {
                    const prevPrice = previousPrices[stock.code] || stock.price
                    // 使用后端返回的涨跌幅来决定颜色，兼容未返回的情况
                    const pct = stock.change_percent || 0
                    const changeColor = pct > 0 ? 'text-red-600' : pct < 0 ? 'text-green-600' : 'text-gray-800'

                    return (
                        <div key={stock.code} className="flex items-baseline gap-2 whitespace-nowrap">
                            <span className="text-xs font-semibold text-gray-700">{stock.name}</span>
                            <span className={`text-sm font-bold font-mono w-24 flex items-baseline justify-end ${changeColor}`}>
                                ¥<RollingPrice
                                    price={stock.price.toFixed(2)}
                                    previousPrice={prevPrice.toFixed(2)}
                                />
                            </span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
