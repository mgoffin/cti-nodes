import { BrowserRouter, Routes, Route } from 'react-router'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import NodeDetail from './components/NodeDetail'
import NewNode from './components/NewNode'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="node/:nodeId" element={<NodeDetail />} />
          <Route path="new" element={<NewNode />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
