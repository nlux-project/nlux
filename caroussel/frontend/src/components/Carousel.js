// Carousel.js - Vanilla JS carousel
import { settingsStore } from '../store/CarouselController.js'

export class Carousel {
  constructor(slide, totalSlides, onSlideChange, config) {
    this.slide = slide
    this.totalSlides = totalSlides
    this.onSlideChange = onSlideChange
    this.config = config
    this.currentSlide = 0
    this.slidesContainer = null
    this.slideNav = null
    this.slideNumber = null
    this.slideProgress = null
    this.activeSlide = null
    this.prevSlide = null
    this.nextSlide = null
    this.slideElements = {}

    // Override config with store values if not provided
    this.effectiveConfig = {
      ...this.config,
      ...settingsStore.config,
    }

    this.init()
    this.setupNavigation()
  }

  init() {
    // Create container
    this.slidesContainer = document.createElement('div')
    this.slidesContainer.className = 'carousel-container'
    this.slidesContainer.style.cssText = `
      width: ${this.effectiveConfig.fullscreen ? '100vw' : '800px'};
      height: ${this.effectiveConfig.fullscreen ? '100vh' : '600px'};
      overflow: hidden;
      position: relative;
    `

    document.body.appendChild(this.slidesContainer)

    this.render()
  }

  render() {
    this.slidesContainer.innerHTML = ''

    // Render slide navigation
    if (!this.effectiveConfig.fullscreen) {
      this.renderSlideNav()
      this.renderSlideNumber()
      this.renderSlideProgress()
    }

    // Render slides
    this.slide.forEach((item, index) => {
      const slideElement = this.createSlideElement(item, index)
      this.slideElements[index] = slideElement
      this.slidesContainer.appendChild(slideElement)
    })
  }

  renderSlideNav() {
    this.slideNav = document.createElement('div')
    this.slideNav.className = 'slide-nav carousel-nav'
    this.slideNav.style.cssText = `
      position: absolute;
      left: ${this.currentSlide === 0 ? '20px' : '50px'};
      right: ${this.currentSlide === this.totalSlides - 1 ? '20px' : '50px'};
      top: '50%';
      transform: translateY(-50%);
      display: flex;
      gap: 10px;
      z-index: 30;
    `

    const prevButton = document.createElement('button')
    prevButton.textContent = '⬅️'
    prevButton.className = 'slide-nav-prev'
    prevButton.disabled = this.currentSlide === 0 || this.effectiveConfig.lock
    prevButton.style.cssText = 'padding: 8px 16px; cursor: pointer; background: #2c5282; color: white; border: none; border-radius: 4px; font-size: 14px;'
    prevButton.addEventListener('click', () => this.prev())

    const nextButton = document.createElement('button')
    nextButton.textContent = '➡️'
    nextButton.className = 'slide-nav-next'
    nextButton.disabled = this.currentSlide === this.totalSlides - 1 || this.effectiveConfig.lock
    nextButton.style.cssText = 'padding: 8px 16px; cursor: pointer; background: #2c5282; color: white; border: none; border-radius: 4px; font-size: 14px;'
    nextButton.addEventListener('click', () => this.next())

    this.slideNav.appendChild(prevButton)
    this.slideNav.appendChild(nextButton)
    this.slidesContainer.appendChild(this.slideNav)
  }

  renderSlideNumber() {
    this.slideNumber = document.createElement('div')
    this.slideNumber.className = 'slide-number'
    this.slideNumber.style.cssText = `
      position: absolute;
      right: ${this.currentSlide === 0 ? '20px' : '50px'};
      top: '50%';
      transform: translateY(-50%);
      font-weight: bold;
      font-size: 18px;
      color: white;
      background: rgba(0, 0, 0, 0.7);
      padding: 8px 16px;
      border-radius: 4px;
      z-index: 30;
    `
    this.slideNumber.textContent = `📸 ${this.currentSlide + 1} / ${this.totalSlides}`
    this.slidesContainer.appendChild(this.slideNumber)
  }

  renderSlideProgress() {
    this.slideProgress = document.createElement('div')
    this.slideProgress.className = 'slide-progress progress-indicator'
    this.slideProgress.style.cssText = `
      position: absolute;
      top: '10px';
      left: '50%';
      transform: translateX(-50%);
      display: flex;
      gap: 4px;
      z-index: 25;
    `

    for (let i = 0; i < this.totalSlides; i++) {
      const dot = document.createElement('div')
      dot.className = `progress-dot ${i === this.currentSlide ? 'active' : ''}`
      dot.style.cssText = 'width: 8px; height: 8px; border-radius: 50%; background: #cbd5e0;'
      if (i === this.currentSlide) {
        dot.style.backgroundColor = '#3182ce'
      }
      return dot
    })

    this.slideProgress.appendChild(...Array.from({ length: this.totalSlides }, (_, i) => {
      const dot = document.createElement('div')
      dot.className = `progress-dot ${i === this.currentSlide ? 'active' : ''}`
      dot.style.cssText = 'width: 8px; height: 8px; border-radius: 50%; background: #cbd5e0;'
      if (i === this.currentSlide) {
        dot.style.backgroundColor = '#3182ce'
      }
      return dot
    }))

    this.slidesContainer.appendChild(this.slideProgress)
  }

  createSlideElement(item, index) {
    const slide = document.createElement('div')
    slide.className = 'slide'
    slide.style.cssText = `
      width: 100%;
      height: 100%;
      position: absolute;
      transition: transform 0.5s ease-in-out, opacity 0.5s ease-in-out;
      opacity: ${this.currentSlide === index ? 1 : 0.4};
      transform: translateX(${this.currentSlide === index ? '0' : this.currentSlide - index} * 100%);
    `

    const card = document.createElement('div')
    card.className = 'carousel-card'
    card.style.cssText = `
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    `

    // Image container
    if (item.thumbnail?.url) {
      const imageContainer = document.createElement('div')
      imageContainer.className = 'image-container'
      const maxWidth = item.hasFullUrl ? '90vw' : '600px'
      const maxHeight = item.hasFullUrl ? '60vh' : '400px'
      imageContainer.style.cssText = `
        max-width: ${maxWidth};
        max-height: ${maxHeight};
        top: 40px;
        z-index: 10;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border-radius: 8px;
      `
      const img = document.createElement('img')
      img.src = item.thumbnail.url
      img.alt = item.title?.value || 'Object'
      img.style.cssText = 'max-width: 100%; max-height: 100%; border-radius: 4px; display: block;'
      img.loading = 'lazy'
      imageContainer.appendChild(img)
      card.appendChild(imageContainer)
    }

    // Title
    const title = document.createElement('div')
    title.className = 'object-title'
    title.textContent = `${item.title?.value || 'Untitled'}`
    title.style.cssText = 'font-weight: bold; font-size: 18px; margin-bottom: 12px; line-height: 1.3; color: #2d3748;'
    card.appendChild(title)

    // Description
    if (item.description?.text) {
      const desc = document.createElement('div')
      desc.className = 'object-description'
      desc.textContent = item.description.text
      desc.style.cssText = 'font-size: 14px; line-height: 1.5; color: #4a5568;'
      card.appendChild(desc)
    }

    // Credits
    if (item.credits?.text) {
      const credits = document.createElement('div')
      credits.className = 'object-credits'
      credits.textContent = item.credits.text
      credits.style.cssText = 'font-size: 12px; color: #718096;'
      card.appendChild(credits)
    }

    // Date
    if (item.startDate) {
      const date = document.createElement('div')
      date.className = 'object-date'
      date.textContent = `📅 ${item.startDate}`
      date.style.cssText = 'font-size: 13px; color: #718096;'
      card.appendChild(date)
    }

    // Type
    if (item.type) {
      const type = document.createElement('div')
      type.className = 'object-type'
      type.textContent = `${item.type}`
      type.style.cssText = 'font-size: 12px; color: #718096; margin-top: 8px;'
      card.appendChild(type)
    }

    // Links
    if (item.links && item.links.length > 0) {
      const links = document.createElement('div')
      links.className = 'object-links'
      const ul = document.createElement('ul')
      links.appendChild(ul)
      ul.style.cssText = 'list-style: none; padding: 0; margin: 0;'

      item.links.slice(0, 3).forEach((link, idx) => {
        const li = document.createElement('li')
        li.textContent = link.label || 'Link'
        li.className = link.isExternal ? 'external' : 'internal'
        li.style.cssText = 'display: block; padding: 4px 8px; border-radius: 4px; margin-bottom: 4px; font-weight: 500;'
        if (link.isExternal) {
          li.style.backgroundColor = '#f7fafc'
          li.style.color = '#ed8936'
          li.style.border = '1px dashed #ed8936'
        } else {
          li.style.backgroundColor = '#ebf8ff'
          li.style.color = '#3182ce'
          li.style.border = '1px solid #3182ce'
        }
        ul.appendChild(li)
      })
      card.appendChild(links)
    }

    slide.appendChild(card)
    return slide
  }

  setupNavigation() {
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (this.effectiveConfig.lock) return

      if (e.key === 'ArrowRight') {
        this.next()
      } else if (e.key === 'ArrowLeft') {
        this.prev()
      } else if (e.key === 'ArrowDown' || e.key === ' ') {
        this.next()
      } else if (e.key === 'ArrowUp') {
        this.prev()
      }
    })

    // Touch navigation
    if (this.slidesContainer) {
      const handleTouchStart = (e) => {
        this.touchStart = { x: e.touches[0].clientX }
      }

      const handleTouchMove = (e) => {
        if (this.touchStart) {
          const diff = this.touchStart.x - e.touches[0].clientX
          if (diff > 50) {
            this.next()
          } else if (diff < -50) {
            this.prev()
          }
          this.touchStart = null
        }
      }

      const handleTouchEnd = () => {
        this.touchStart = null
      }

      this.slidesContainer.addEventListener('touchstart', handleTouchStart)
      this.slidesContainer.addEventListener('touchmove', handleTouchMove)
      this.slidesContainer.addEventListener('touchend', handleTouchEnd)
    }
  }

  next() {
    if (this.currentSlide < this.totalSlides - 1 && !this.effectiveConfig.lock) {
      this.currentSlide++
      this.onSlideChange?.(this.currentSlide)
      this.update()
    }
  }

  prev() {
    if (this.currentSlide > 0 && !this.effectiveConfig.lock) {
      this.currentSlide--
      this.onSlideChange?.(this.currentSlide)
      this.update()
    }
  }

  goToSlide(index) {
    if (index >= 0 && index < this.totalSlides && !this.effectiveConfig.lock) {
      this.currentSlide = index
      this.onSlideChange?.(this.currentSlide)
      this.update()
    }
  }

  update() {
    if (!this.slidesContainer) return

    // Update navigation buttons
    const prevBtn = this.slidesContainer.querySelector('.slide-nav-prev')
    const nextBtn = this.slidesContainer.querySelector('.slide-nav-next')
    const slideNumber = this.slidesContainer.querySelector('.slide-number')
    const slideProgress = this.slidesContainer.querySelector('.progress-indicator')

    if (prevBtn) {
      prevBtn.disabled = this.currentSlide === 0 || this.effectiveConfig.lock
      if (this.effectiveConfig.lock) {
        prevBtn.title = 'Navigation locked'
      }
    }

    if (nextBtn) {
      nextBtn.disabled = this.currentSlide === this.totalSlides - 1 || this.effectiveConfig.lock
      if (this.effectiveConfig.lock) {
        nextBtn.title = 'Navigation locked'
      }
    }

    // Update slide number
    if (slideNumber) {
      slideNumber.textContent = `📸 ${this.currentSlide + 1} / ${this.totalSlides}`
    }

    // Update progress dots
    if (this.slideProgress) {
      Array.from(this.slideProgress.children).forEach((dot, i) => {
        dot.className = `progress-dot ${i === this.currentSlide ? 'active' : ''}`
      })
    }

    // Update all slides
    this.slideElements.forEach((element, index) => {
      element.style.cssText = `
        width: 100%;
        height: 100%;
        position: absolute;
        transition: transform 0.5s ease-in-out, opacity 0.5s ease-in-out;
        opacity: ${this.currentSlide === index ? 1 : 0.4};
        transform: translateX(${this.currentSlide === index ? '0' : this.currentSlide - index} * 100%);
      `
    })
  }

  destroy() {
    if (this.slidesContainer && this.slidesContainer.parentNode) {
      this.slidesContainer.parentNode.removeChild(this.slidesContainer)
    }
  }

  show() {
    if (this.slidesContainer && !this.slidesContainer.parentNode) {
      this.init()
    }
  }

  hide() {
    this.destroy()
  }
}
