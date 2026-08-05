import '../TopScreen/TopScreen.css';
import NavigationButton from '../components/NavigationButton';

function BillingStatusScreen({ onBack }) {
  return (
    <main className="next-screen">
      <h1>請求状態確認</h1>
      <p>請求状態を表示する仮画面です。</p>
      <NavigationButton onClick={onBack}>戻る</NavigationButton>
    </main>
  );
}

export default BillingStatusScreen;
