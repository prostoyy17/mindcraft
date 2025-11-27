import { FormEvent, useCallback, useMemo, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

type WorldResponse = {
  world_description: string
  scenario_text: string
  hints_for_image?: string | null
  player_name?: string | null
}

type RequestMode = 'create' | 'random'

function App() {
  const [playerName, setPlayerName] = useState('')
  const [description, setDescription] = useState('')
  const [result, setResult] = useState<WorldResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [modeInFlight, setModeInFlight] = useState<RequestMode | null>(null)

  const isLoading = modeInFlight !== null
  const canCreate = description.trim().length >= 3 && !isLoading

  const trimmedPlayerName = useMemo(() => playerName.trim() || undefined, [playerName])

  const requestWorld = useCallback(
    async (mode: RequestMode) => {
      if (mode === 'create' && !canCreate) {
        return
      }

      setModeInFlight(mode)
      setError(null)

      const payload =
        mode === 'create'
          ? {
              description: description.trim(),
              player_name: trimmedPlayerName,
            }
          : {
              player_name: trimmedPlayerName,
            }

      try {
        const response = await fetch(`${API_BASE}/api/world/${mode === 'create' ? 'create' : 'random'}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

        if (!response.ok) {
          const message = await response.text()
          throw new Error(message || 'Не удалось получить ответ от MindCraft API.')
        }

        const data = (await response.json()) as WorldResponse
        setResult(data)
      } catch (err) {
        console.error(err)
        setError(err instanceof Error ? err.message : 'Произошла неизвестная ошибка.')
        setResult(null)
      } finally {
        setModeInFlight(null)
      }
    },
    [canCreate, description, trimmedPlayerName],
  )

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void requestWorld('create')
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">MindCraft · текстовый прототип</p>
          <h1>Сгенерируй мир и сразу попади в приключение</h1>
          <p className="subtitle">
            Напиши пару фраз о сеттинге или доверься случайному миру. GPT создаст описание, стартовую ситуацию и
            подсказку для фоновой картинки.
          </p>
        </div>
      </header>

      <main className="content">
        <form className="world-form" onSubmit={handleSubmit}>
          <label htmlFor="playerName">Имя героя (опционально)</label>
          <input
            id="playerName"
            name="playerName"
            placeholder="Например, Аэлин или Кай..."
            value={playerName}
            onChange={(event) => setPlayerName(event.target.value)}
            disabled={isLoading}
          />

          <label htmlFor="worldDescription">Опиши свой мир</label>
          <textarea
            id="worldDescription"
            name="worldDescription"
            placeholder="Мир парящих островов, где магия работает через музыку..."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={isLoading}
            rows={6}
          />
          <p className="helper-text">Минимум 3 символа, чтобы запустить кастомный мир.</p>

          <div className="actions">
            <button type="submit" className="primary" disabled={!canCreate}>
              {modeInFlight === 'create' ? 'Генерируем...' : 'Создать по описанию'}
            </button>
            <button
              type="button"
              className="ghost"
              onClick={() => void requestWorld('random')}
              disabled={isLoading}
            >
              {modeInFlight === 'random' ? 'Придумываем...' : 'Случайный мир'}
            </button>
          </div>
          {error && <p className="error">{error}</p>}
        </form>

        <section className="result-panel">
          {isLoading && <p className="status-line">ИИ думает над приключением...</p>}
          {!isLoading && !result && <p className="status-line">Здесь появится твой мир и первый сценарий.</p>}
          {result && !isLoading && (
            <div className="scenario-card">
              <div className="pill">{result.player_name ? `Герой: ${result.player_name}` : 'MindCraft World'}</div>
              <h2>Описание мира</h2>
              <p>{result.world_description}</p>

              <h3>Стартовая ситуация</h3>
              <p>{result.scenario_text}</p>

              {result.hints_for_image && (
                <div className="hints">
                  <span>Подсказки для фоновой картинки:</span>
                  <p>{result.hints_for_image}</p>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
