import './TopScreen/TopScreen.css';
import NavigationButton from './components/NavigationButton';

function TransferScreen({ onBack }) {
  return (
    <main className="next-screen">
      <h1>送金画面</h1>
      <p>送金処理を行う画面です。</p>
      <NavigationButton onClick={onBack}>戻る</NavigationButton>
    </main>
  );
}

export default TransferScreen;
