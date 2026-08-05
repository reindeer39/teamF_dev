import './NavigationButton.css';

function NavigationButton({ children, onClick }) {
  return (
    <button className="navigation-button" type="button" onClick={onClick}>
      {children}
    </button>
  );
}

export default NavigationButton;
