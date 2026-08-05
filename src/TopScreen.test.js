import { render, screen } from '@testing-library/react';
import TopScreen from './TopScreen/TopScreen';

test('renders transfer and billing buttons', () => {
  render(<TopScreen />);
  expect(screen.getByRole('button', { name: '送金する' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '請求する' })).toBeInTheDocument();
});
