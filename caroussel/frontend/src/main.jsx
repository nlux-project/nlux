import './styles.css'
import './store/StoreProvider.js'
import App from './App.jsx'

const rootElement = document.getElementById('root')
const app = new App()

// Mount app to root
rootElement.appendChild(app)

// Sync window.LUX_API with localStorage
window.LUX_API = localStorage.getItem('nlux_api') || 'http://localhost:8000'
