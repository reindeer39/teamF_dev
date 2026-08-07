import './MessageInput.css';

function MessageInput({
  id,
  label = 'メッセージ',
  value = '',
  onChange,
  placeholder = '',
  maxLength,
  readOnly = false,
  className = '',
}) {
  return (
    <label className={`message-input-field ${className}`.trim()} htmlFor={id}>
      <span className="message-input-field__label">{label}</span>
      <textarea
        id={id}
        className="message-input-field__textarea"
        aria-label={label}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        maxLength={maxLength}
        readOnly={readOnly}
      />
    </label>
  );
}

export default MessageInput;
