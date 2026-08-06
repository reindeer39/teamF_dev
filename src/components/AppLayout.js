import TopBar from './TopBar';
import './AppLayout.css';

function AppLayout({ title, onBack, children }) {
  return (
    <div className="app-layout">
      <TopBar title={title} onBack={onBack} />
      <div className="app-layout__content">{children}</div>
    </div>
  );
}

export default AppLayout;
