import './NavigationButton.css';

function NavigationButton({
  children,
  onClick,
  width,
  height,
  backgroundColor,
  hoverColor,
  textColor,
}) {
  return (
    <button
      className="navigation-button"
      type="button"
      onClick={onClick}
      style={{
        width,
        height,
        '--button-background-color': backgroundColor,
        '--button-hover-color': hoverColor,
        '--button-text-color': textColor,
      }}
    >
      {children}
    </button>
  );
}

export default NavigationButton;
