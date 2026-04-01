import { useState } from 'react'
import Header from './components/shared/Header'
import ChatView from './components/Chat/ChatView'
import DocumentsView from './components/Documents/DocumentsView'
import EvaluationView from './components/Evaluation/EvaluationView'

export type ViewTab = 'chat' | 'documents' | 'evaluation'

export default function App() {
  const [activeTab, setActiveTab] = useState<ViewTab>('chat')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light'
    setTheme(next)
    document.documentElement.setAttribute('data-theme', next)
  }

  return (
    <div className="app-layout">
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <div className="app-body">
        <div className="app-main">
          <div className={`view ${activeTab === 'chat' ? 'view--active' : ''}`}>
            <ChatView />
          </div>
          <div className={`view ${activeTab === 'documents' ? 'view--active' : ''}`}>
            <DocumentsView />
          </div>
          <div className={`view ${activeTab === 'evaluation' ? 'view--active' : ''}`}>
            <EvaluationView />
          </div>
        </div>
      </div>
    </div>
  )
}
