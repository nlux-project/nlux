import React, { useMemo } from 'react'
import { settingsStore } from '../store/StoreProvider'

export default function Carousel({ slide, totalSlides, onSlideChange, config }) {
  // Override config with store values if not provided
  const effectiveConfig = {
    ...config,
    ...settingsStore.config,
  }

  const [currentSlide, setCurrentSlide] = React.useState(0)

  return (
    <div
      className="carousel-container"
      style={{
        ...styles.container,
        width: effectiveConfig.fullscreen ? '100vw' : '800px',
        height: effectiveConfig.fullscreen ? '100vh' : '600px',
      }}
    >
      {/* Slide Navigation */}
      {!effectiveConfig.fullscreen && (
        <div
          className="slide-nav"
          style={{
            ...styles.slideNav,
            left: currentSlide === 0 ? '20px' : '50px',
            right: currentSlide === totalSlides - 1 ? '20px' : '50px',
          }}
        >
          <button
            onClick={() => (currentSlide > 0 && !effectiveConfig.lock) && handlePrev()}
            disabled={currentSlide === 0 || effectiveConfig.lock}
            className="slide-nav-prev"
          >
            ⬅️
          </button>
          <button
            onClick={() => (currentSlide < totalSlides - 1 && !effectiveConfig.lock) && handleNext()}
            disabled={currentSlide === totalSlides - 1 || effectiveConfig.lock}
            className="slide-nav-next"
          >
            ➡️
          </button>
        </div>
      )}

      {/* Slide Number */}
      {!effectiveConfig.fullscreen && (
        <div
          className="slide-number"
          style={{
            ...styles.slideNumber,
            right: currentSlide === 0 ? '20px' : '50px',
          }}
        >
          📸 {currentSlide + 1} / {totalSlides}
        </div>
      )}

      {/* Slide Progress */}
      {!effectiveConfig.fullscreen && (
        <div className="slide-progress">
          {Array.from({ length: totalSlides }, (_, i) => (
            <div
              key={i}
              className={`progress-dot ${i === currentSlide ? 'active' : ''}`}
            />
          ))}
        </div>
      )}

      {/* Slides */}
      {slide.map((item, index) => (
        <SlideItem
          key={item.uri}
          item={item}
          isActive={currentSlide === index}
          isPrev={currentSlide === index - 1}
          isNext={currentSlide === index + 1}
        />
      ))}
    </div>
  )
}

function SlideItem({ item, isActive, isPrev, isNext }) {
  const containerStyle = useMemo(() => ({
    ...styles.slide,
    opacity: isActive ? 1 : 0.4,
    transform: isActive ? 'translateX(0)' : isPrev ? 'translateX(-20px)' : 'translateX(20px)',
  }), [isActive, isPrev, isNext])

  return (
    <div className="slide" style={containerStyle}>
      <div className="carousel-card">
        {/* Image Container */}
        {item.hasThumbnail && (
          <div
            className="image-container"
            style={{
              ...styles.imageContainer,
              'max-width': item.hasFullUrl ? '90vw' : '600px',
              'max-height': item.hasFullUrl ? '60vh' : '400px',
              top: '40px',
              zIndex: 10,
            }}
          >
            <img
              src={item.thumbnail?.url}
              alt={item.title?.value || 'Object'}
              loading="lazy"
            />
          </div>
        )}

        {/* Title */}
        <div className="object-title">
          <strong>{item.title?.value || 'Untitled'}</strong>
        </div>

        {/* Description */}
        {item.description?.text && (
          <div className="object-description">
            {item.description.text}
          </div>
        )}

        {/* Credits */}
        {item.credits?.text && (
          <div className="object-credits">
            {item.credits.text}
          </div>
        )}

        {/* Date */}
        {item.startDate && (
          <div className="object-date">
            📅 {item.startDate}
          </div>
        )}

        {/* Type */}
        {item.type && (
          <div className="object-type">
            {item.type}
          </div>
        )}

        {/* Links */}
        {item.links?.length > 0 && (
          <div className="object-links">
            <ul>
              {item.links.slice(0, 3).map((link, idx) => (
                <li key={idx} className={link.isExternal ? 'external' : 'internal'}>
                  {link.label || 'Link'}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

// Navigation handlers
function handlePrev() {
  const prevIndex = settingsStore.currentSlide - 1
  if (prevIndex >= 0) {
    settingsStore.setCurrentSlide(prevIndex)
  }
}

function handleNext() {
  const nextIndex = settingsStore.currentSlide + 1
  if (nextIndex < settingsStore.totalSlides) {
    settingsStore.setCurrentSlide(nextIndex)
  }
}

// Styles
const styles = {
  container: {
    width: '100%',
    height: '100%',
    overflow: 'hidden',
    position: 'relative',
  },
  slide: {
    width: '100%',
    height: '100%',
    position: 'absolute',
    transition: 'transform 0.5s ease-in-out, opacity 0.5s ease-in-out',
  },
  'slide.active': {
    zIndex: 10,
  },
  'slide.is-prev': {
    zIndex: 5,
  },
  'slide.is-next': {
    zIndex: 0,
  },
  carouselCard: {
    position: 'absolute',
    left: 0,
    top: 0,
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
  },
  'carousel-card.is-prev': {
    transform: 'translateX(-150px)',
    transition: 'transform 0.3s ease',
  },
  'carousel-card.is-next': {
    transform: 'translateX(150px)',
    transition: 'transform 0.3s ease',
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
    height: 'auto',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
    borderRadius: '8px',
  },
  'image-container.is-external': {
    maxWidth: '600px',
    maxHeight: '400px',
  },
  carouselMeta: {
    position: 'absolute',
    top: '20px',
    left: '20px',
    zIndex: 20,
  },
  carouselMetaItem: {
    marginBottom: '8px',
  },
  icon: {
    marginRight: '6px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
  },
  carouselCardTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    marginBottom: '12px',
    lineHeight: '1.3',
    color: '#2d3748',
  },
  carouselCardContent: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: '#4a5568',
  },
  carouselCardDate: {
    fontSize: '13px',
    color: '#718096',
  },
  carouselCardType: {
    fontSize: '12px',
    color: '#718096',
    marginTop: '8px',
  },
  carouselCardLinks: {
    fontSize: '12px',
    color: '#718096',
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid #e2e8f0',
  },
  link: {
    display: 'block',
    padding: '4px 8px',
    borderRadius: '4px',
    marginBottom: '4px',
    fontWeight: '500',
  },
  'link.is-external': {
    backgroundColor: '#f7fafc',
    color: '#ed8936',
    border: '1px dashed #ed8936',
  },
  'link.is-internal': {
    backgroundColor: '#ebf8ff',
    color: '#3182ce',
    border: '1px solid #3182ce',
  },
}
