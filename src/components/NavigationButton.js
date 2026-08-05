import './NavigationButton.css';

function NavigationButton({
  children,
  onClick,
  disabled = false,
  width = null,
  height = null,
  backgroundColor = null,
  hoverColor = null,
  textColor = null,
  disabled = false,
}) {
  return (
    <button
      className="navigation-button"
      type="button"
      onClick={onClick}
      disabled={disabled}
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
