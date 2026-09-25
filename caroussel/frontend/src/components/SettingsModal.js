// SettingsModal.js
// Vanilla JS settings modal using global settingsStore

class SettingsModal {
  constructor() {
    this.isVisible = false
    this.modal = null
    this.initialize()
  }

  initialize() {
    // Store the settings value in a global variable
    window.__settingsModal = this
    
    document.addEventListener('DOMContentLoaded', () => {
      // Fullscreen toggle button
      const fullscreenToggle = document.getElementById('toggle-fullscreen')
      if (fullscreenToggle) {
        fullscreenToggle.addEventListener('change', (e) => {
          this.settings.setFullscreen(e.target.checked)
          this.modal.save()
        })
      }

      // Lock toggle button
      const lockToggle = document.getElementById('toggle-lock')
      if (lockToggle) {
        lockToggle.addEventListener('change', (e) => {
          this.settings.setLock(e.target.checked)
          this.modal.save()
        })
      }

      // Interval slider
      const intervalSlider = document.getElementById('interval-slider')
      if (intervalSlider) {
        intervalSlider.addEventListener('input', (e) => {
          const value = parseInt(e.target.value)
          this.settings.setInterval(value)
          this.modal.save()
        })
      }

      // Count slider
      const countSlider = document.getElementById('count-slider')
      if (countSlider) {
        countSlider.addEventListener('input', (e) => {
          const value = parseInt(e.target.value)
          this.settings.setCount(value)
          this.modal.save()
        })
      }

      // Collection select
      const collectionSelect = document.getElementById('collection-select')
      if (collectionSelect) {
        collectionSelect.addEventListener('change', (e) => {
          this.settings.setCollection(e.target.value)
          this.modal.save()
        })
      }

      // Scope select
      const scopeSelect = document.getElementById('scope-select')
      if (scopeSelect) {
        scopeSelect.addEventListener('change', (e) => {
          this.settings.setScope(e.target.value)
          this.modal.save()
        })
      }
    })
  }

  show() {
    this.isVisible = true
    this.modal.show()
    
    // Sync UI with current settings
    this.updateUI()
  }

  hide() {
    this.isVisible = false
    this.modal.hide()
  }

  get settings() {
    return window.nluxStores?.settingsStore || {
      config: {
        fullscreen: false,
        lock: false,
        interval: 5,
        count: 3,
        maxAge: 5,
      },
      collection: 'teylers',
      scope: 'item',
    }
  }

  getModal() {
    // If modal doesn't exist yet, create it
    if (this.modal === null) {
      this.modal = new Modal('Settings')
    }
    return this.modal
  }

  updateUI() {
    const settings = this.settings

    document.getElementById('collection-select')?.setAttribute('value', settings.collection)
    document.getElementById('scope-select')?.setAttribute('value', settings.scope)
    document.getElementById('interval-slider')?.setAttribute('value', settings.config.interval)
    document.getElementById('count-slider')?.setAttribute('value', settings.config.count)
    document.getElementById('maxage-slider')?.setAttribute('value', settings.config.maxAge)
    document.getElementById('toggle-fullscreen')?.setAttribute('checked', settings.config.fullscreen)
    document.getElementById('toggle-lock')?.setAttribute('checked', settings.config.lock)
  }

  save() {
    this.modal.save()
  }
}

// Vanilla JS modal component
class Modal {
  constructor(title) {
    this.title = title
    this.isVisible = false
    this.elements = {
      backdrop: null,
      container: null,
      content: null,
      header: null,
      body: null,
      footer: null,
    }
    this.init()
  }

  init() {
    // Create modal elements
    this.elements.backdrop = document.createElement('div')
    this.elements.backdrop.className = 'modal-backdrop'
    this.elements.backdrop.addEventListener('click', () => this.hide())

    this.elements.container = document.createElement('div')
    this.elements.container.className = 'modal-container'
    this.elements.container.style.display = 'none'

    this.elements.content = document.createElement('div')
    this.elements.content.className = 'modal-content'

    this.elements.header = document.createElement('div')
    this.elements.header.className = 'modal-header'
    this.elements.header.innerHTML = `
      <h2>${this.title}</h2>
      <button class="modal-close">×</button>
    `

    this.elements.body = document.createElement('div')
    this.elements.body.className = 'modal-body'

    this.elements.footer = document.createElement('div')
    this.elements.footer.className = 'modal-footer'
    this.elements.footer.innerHTML = `
      <button class="modal-save">Save</button>
      <button class="modal-cancel">Cancel</button>
    `

    // Append to document body
    document.body.appendChild(this.elements.backdrop)
    document.body.appendChild(this.elements.container)

    // Bind events
    this.elements.container.addEventListener('click', () => {
      // Prevent closing when clicking inside modal
    })

    this.elements.footer.querySelector('.modal-save').addEventListener('click', () => {
      this.handleSave()
    })

    this.elements.footer.querySelector('.modal-cancel').addEventListener('click', () => {
      this.hide()
    })

    this.elements.header.querySelector('.modal-close').addEventListener('click', () => {
      this.hide()
    })
  }

  show() {
    this.isVisible = true
    this.elements.container.style.display = 'block'
    this.elements.backdrop.style.opacity = '1'
    this.elements.backdrop.style.pointerEvents = 'auto'
  }

  hide() {
    this.isVisible = false
    this.elements.container.style.display = 'none'
    this.elements.backdrop.style.opacity = '0'
    this.elements.backdrop.style.pointerEvents = 'none'
    
    // Remove from DOM after animation
    setTimeout(() => {
      document.body.removeChild(this.elements.backdrop)
      document.body.removeChild(this.elements.container)
    }, 150)
  }

  save() {
    // Default save implementation
    // Override in subclass if needed
  }

  handleSave() {
    this.save()
    alert('Settings saved!')
    this.hide()
  }

  close() {
    this.hide()
  }
}

// Export settings modal
export default SettingsModal
