import './App.css';
import NavigationButton from './components/NavigationButton';

function NextScreen({ onBack }) {
  return (
    <main className="next-screen">
      <h1>遷移先の画面</h1>
      <p>画面遷移に成功しました。</p>
      <NavigationButton onClick={onBack}>
        戻る
      </NavigationButton>
    </main>
  );
}

export default NextScreen;
