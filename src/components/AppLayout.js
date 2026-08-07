import TopBar from './TopBar';
import './AppLayout.css';

function AppLayout({ title, onBack, onLogout, showTopBar = true, children }) {
  return (
    <div className={`app-layout ${showTopBar ? '' : 'app-layout--without-top-bar'}`.trim()}>
      {showTopBar && <TopBar title={title} onBack={onBack} onLogout={onLogout} />}
      <div className="app-layout__content">{children}</div>
    </div>
  );
}

export default AppLayout;
