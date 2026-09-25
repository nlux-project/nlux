import React, { useState, useRef, useEffect } from 'react'
import { settingsStore } from '../store/StoreProvider'
import settingsStore from '../store/SettingsStore'

export default function SettingsModal() {
  const [isVisible, setIsVisible] = useState(false)
  const modalRef = useRef(null)

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isVisible) {
        handleClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isVisible])

  const handleOpen = () => {
    setIsVisible(true)
  }

  const handleClose = () => {
    setIsVisible(false)
    settingsStore.reset()
  }

  const handleSettingsSave = () => {
    settingsStore.save()
    alert('Settings saved!')
  }

  return (
    <div
      className={`settings-modal ${isVisible ? 'visible' : ''}`}
      onClick={handleClose}
    >
      <div
        className="settings-content"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="settings-header">
          <h2>⚙️ NLUX Carousell Settings</h2>
          <button
            className="close-button"
            onClick={handleClose}
            title="Close settings (Esc)"
          >
            ✕
          </button>
        </div>

        {/* Collection & Scope */}
        <div className="settings-section">
          <h3>📚 Collection & Scope</h3>
          
          <div className="form-group">
            <label>
              <span>Collection</span>
            </label>
            <select value={settingsStore.collection} onChange={handleCollectionChange}>
              <option value="all">All Collections</option>
            </select>
          </div>

          <div className="form-group">
            <label>
              <span>Scope</span>
            </label>
            <select value={settingsStore.scope} onChange={handleScopeChange}>
              <option value="item">Physical Objects</option>
              <option value="work">Creative Works</option>
              <option value="agent">People & Organizations</option>
              <option value="place">Places</option>
              <option value="concept">Concepts</option>
              <option value="event">Events</option>
              <option value="digital">Digital Objects</option>
            </select>
          </div>
        </div>

        {/* Display Settings */}
        <div className="settings-section">
          <h3>🖼️ Display Settings</h3>

          <div className="form-group">
            <label>
              <span>Fullscreen</span>
              <span>Hide navigation controls</span>
            </label>
            <div className="toggle">
              <span>Fullscreen</span>
              <div className="toggle-slider">
                <input
                  type="checkbox"
                  id="toggle-fullscreen"
                  checked={settingsStore.fullscreen}
                  onChange={handleFullscreenChange}
                />
              </div>
            </div>
          </div>

          <div className="form-group">
            <label>
              <span>Lock Navigation</span>
              <span>Disable arrow keys and buttons</span>
            </label>
            <div className="toggle">
              <span>Lock Navigation</span>
              <div className="toggle-slider">
                <input
                  type="checkbox"
                  id="toggle-lock"
                  checked={settingsStore.lock}
                  onChange={handleLockChange}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Carousel Settings */}
        <div className="settings-section">
          <h3>🎯 Carousel Settings</h3>

          <div className="form-group">
            <label>
              <span>Slide Interval</span>
              <span>{settingsStore.interval}s</span>
            </label>
            <div className="slider">
              <input
                type="range"
                id="interval-slider"
                min="5"
                max="20"
                value={settingsStore.interval}
                onChange={handleIntervalChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>
              <span>Slides Per Carousel</span>
              <span>{settingsStore.count} slides</span>
            </label>
            <div className="slider">
              <input
                type="range"
                id="count-slider"
                min="1"
                max="10"
                value={settingsStore.count}
                onChange={handleCountChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>
              <span>Refresh Threshold</span>
              <span>{settingsStore.maxAge} minutes</span>
            </label>
            <div className="slider">
              <input
                type="range"
                id="maxage-slider"
                min="2"
                max="20"
                value={settingsStore.maxAge}
                onChange={handleMaxAgeChange}
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="settings-section">
          <h3>🎮 Actions</h3>
          <div className="button-group">
            <button
              id="generate-seed"
              className="button"
              onClick={handleGenerateSeed}
            >
              🎲 Random Seed
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Event handlers
const handleCollectionChange = (e) => {
  settingsStore.setCollection(e.target.value)
}

const handleScopeChange = (e) => {
  settingsStore.setScope(e.target.value)
}

const handleFullscreenChange = (e) => {
  settingsStore.setFullscreen(e.target.checked)
}

const handleLockChange = (e) => {
  settingsStore.setLock(e.target.checked)
}

const handleIntervalChange = (e) => {
  settingsStore.setInterval(parseInt(e.target.value))
}

const handleCountChange = (e) => {
  settingsStore.setCount(parseInt(e.target.value))
}

const handleMaxAgeChange = (e) => {
  settingsStore.setMaxAge(parseInt(e.target.value))
}

const handleGenerateSeed = () => {
  settingsStore.generateSeed()
}
