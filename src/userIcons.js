import avatarDefault from './images/avatars/avatar-default.png';

const PRIVATE_MODE =
  process.env.REACT_APP_DATA_MODE === 'private';

const ALLOWED_ICONS = new Set([
  'avatar-01.png',
  'avatar-02.png',
  'avatar-03.png',
  'avatar-04.png',
  'avatar-05.png',
]);

export function resolveUserIcon(iconName) {
  if (!PRIVATE_MODE || !iconName) {
    return avatarDefault;
  }

  const normalizedPath = iconName.replaceAll('\\', '/');
  const fileName = normalizedPath.split('/').pop();

  if (!ALLOWED_ICONS.has(fileName)) {
    return avatarDefault;
  }

  return `${process.env.PUBLIC_URL}/private-avatars/${fileName}`;
}
