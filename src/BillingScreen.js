import './TopScreen/TopScreen.css';
import NavigationButton from './components/NavigationButton';

function BillingScreen({ onBack }) {
  return (
    <main className="next-screen">
      <h1>請求画面</h1>
      <p>請求処理を行う画面です。</p>
      <NavigationButton onClick={onBack}>戻る</NavigationButton>
    </main>
  );
}

export default BillingScreen;
