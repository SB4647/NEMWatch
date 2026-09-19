import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RegionOverview from '../../src/components/RegionOverview.vue'

describe('RegionOverview', () => {
  it('shows an explicit missing state without fake values', () => {
    const wrapper = mount(RegionOverview, { props: { regions: [{ code: 'QLD1', name: 'Queensland' }], latestByRegion: new Map() } })
    expect(wrapper.get('[data-state="missing"]').text()).toContain('No observation has been received.')
    expect(wrapper.find('[data-testid="market-value"]').exists()).toBe(false)
  })
})
