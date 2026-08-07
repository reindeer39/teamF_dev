import './AmountInput.css';

function AmountInput({
  id,
  label,
  value,
  onChange,
  min = 1,
  step = 1,
  className = '',
}) {
  return (
    <label className={`amount-input-field ${className}`.trim()} htmlFor={id}>
      <span className="amount-input-field__label">{label}</span>
      <span className="amount-input-field__control">
        <input
          id={id}
          aria-label={label}
          type="number"
          min={min}
          step={step}
          inputMode="numeric"
          placeholder="金額"
          value={value}
          onChange={onChange}
        />
        <span className="amount-input-field__unit">円</span>
      </span>
    </label>
  );
}

export default AmountInput;
