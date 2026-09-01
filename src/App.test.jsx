import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App.jsx'

describe('App', () => {
  it('renders with an initial count of 0', () => {
    render(<App />)
    expect(screen.getByTestId('count')).toHaveTextContent('0')
  })

  it('increments the count when the +1 button is clicked', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: '+1' }))
    expect(screen.getByTestId('count')).toHaveTextContent('1')

    await user.click(screen.getByRole('button', { name: '+1' }))
    expect(screen.getByTestId('count')).toHaveTextContent('2')
  })

  it('resets the count to 0 when the reset button is clicked', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: '+1' }))
    await user.click(screen.getByRole('button', { name: '+1' }))
    await user.click(screen.getByRole('button', { name: 'リセット' }))

    expect(screen.getByTestId('count')).toHaveTextContent('0')
  })
})
