// マージ元に残っていた旧CRAテストの退避ファイルです。
// 現行画面のテストは src/TopScreen.test.js を参照してください。
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
