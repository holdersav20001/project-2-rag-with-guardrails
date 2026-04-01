
import type { ViewTab } from '../../App'

interface HeaderProps {
  activeTab: ViewTab
  onTabChange: (tab: ViewTab) => void
  theme: 'light' | 'dark'
  onToggleTheme: () => void
}

const TABS: { id: ViewTab; label: string }[] = [
  { id: 'chat', label: 'Chat' },
  { id: 'documents', label: 'Documents' },
  { id: 'evaluation', label: 'Evaluation' },
]

export default function Header({ activeTab, onTabChange, theme, onToggleTheme }: HeaderProps) {
  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__brand">
          <span className="header__logo" aria-hidden="true">🛡️</span>
          <span className="header__title">RAG Guardrails</span>
        </div>

        <nav className="header__nav" role="tablist" aria-label="Main navigation">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`header__tab ${activeTab === tab.id ? 'header__tab--active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <button
          className="header__theme-toggle"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
      </div>
    </header>
  )
}
