// App.js - Main entry point (Vanilla JS)
import { Carousel } from './Carousel.js'
import { SettingsModal } from './SettingsModal.js'

// App container
const appContainer = document.getElementById('app-container')

// Create carousel
const carousel = new Carousel()
carousel.render(appContainer)

// Show settings modal by default
const settingsModal = new SettingsModal()
settingsModal.render(document.body)
document.getElementById('settings-modal')?.classList.add('d-none')

// Show app after carousel is ready
appContainer.style.display = 'block'
