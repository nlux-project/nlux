import { ICmsPage } from '../../../redux/api/returnTypes'

interface IContentPageFallback {
  title?: string
  body?: string
}

export class ContentPageParser {
  data: unknown

  fallback: IContentPageFallback

  constructor(data: unknown, fallback: IContentPageFallback = {}) {
    this.data = data
    this.fallback = fallback
  }

  getAttributes(): Partial<ICmsPage['data']['attributes']> | undefined {
    if (this.data === null || typeof this.data !== 'object') {
      return undefined
    }

    const cmsData = (this.data as Partial<ICmsPage>).data

    if (cmsData === null || typeof cmsData !== 'object') {
      return undefined
    }

    return cmsData.attributes
  }

  getTitle(): string {
    return this.getAttributes()?.title ?? this.fallback.title ?? ''
  }

  getBody(): string {
    return this.getAttributes()?.body ?? this.fallback.body ?? ''
  }
}

export default ContentPageParser
