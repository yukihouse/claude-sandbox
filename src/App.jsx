import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-slate-900 text-white">
      <h1 className="text-3xl font-bold">カウンターデモ</h1>

      <p className="text-6xl font-mono tabular-nums" data-testid="count">
        {count}
      </p>

      <div className="flex gap-4">
        <button
          onClick={() => setCount((c) => c + 1)}
          className="rounded-lg bg-indigo-600 px-6 py-3 font-semibold shadow transition hover:bg-indigo-500 active:scale-95"
        >
          +1
        </button>
        <button
          onClick={() => setCount(0)}
          className="rounded-lg bg-slate-700 px-6 py-3 font-semibold shadow transition hover:bg-slate-600 active:scale-95"
        >
          リセット
        </button>
      </div>
    </div>
  )
}

export default App
