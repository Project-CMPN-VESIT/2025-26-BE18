/* eslint-disable no-unused-vars */
import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import ChatbotInterface from './pages/ChatbotInterface'
import NormalPage from './pages/NormalChat'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
     <ChatbotInterface/>
     {/* <NormalPage/> */}
    </>
  )
}

export default App
