import ContentPageParser from '../../../../../lib/parse/cms/ContentPageParser'

describe('ContentPageParser', () => {
  it('returns title and body from a valid CMS page response', () => {
    const parser = new ContentPageParser({
      data: {
        attributes: {
          title: 'CMS title',
          body: '<p>CMS body</p>',
        },
      },
    })

    expect(parser.getTitle()).toBe('CMS title')
    expect(parser.getBody()).toBe('<p>CMS body</p>')
  })

  it('returns fallback values when the CMS response is missing page attributes', () => {
    const parser = new ContentPageParser('<html>Not JSON API</html>', {
      title: 'Route title',
      body: '<p>Fallback body</p>',
    })

    expect(parser.getTitle()).toBe('Route title')
    expect(parser.getBody()).toBe('<p>Fallback body</p>')
  })
})
