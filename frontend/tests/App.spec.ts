import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import App from '../src/App.vue'

describe('App', () => {
  it('identifies the product and market dashboard', () => {
    const wrapper = mount(App)

    expect(wrapper.get('h1').text()).toBe('NEMWatch')
    expect(wrapper.text()).toContain('Regional overview')
  })

  it('shows the educational-use disclaimer without fake market values', () => {
    const wrapper = mount(App)

    expect(wrapper.text()).toContain(
      'Educational use only. Not a trading, dispatch, or operational control system.',
    )
    expect(wrapper.text()).toContain('Fixture values are not current market information.')
  })
})
