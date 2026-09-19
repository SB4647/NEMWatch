import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import App from '../src/App.vue'

describe('App', () => {
  it('identifies the product and its current development state', () => {
    const wrapper = mount(App)

    expect(wrapper.get('h1').text()).toBe('NEMWatch')
    expect(wrapper.text()).toContain('Local development shell')
  })

  it('shows the educational-use disclaimer without fake market values', () => {
    const wrapper = mount(App)

    expect(wrapper.text()).toContain(
      'Educational use only. Not a trading, dispatch, or operational control system.',
    )
    expect(wrapper.find('[data-testid="market-value"]').exists()).toBe(false)
  })
})
