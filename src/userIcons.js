import avatar01 from './images/avatars/avatar-01.png';
import avatar02 from './images/avatars/avatar-02.png';
import avatar03 from './images/avatars/avatar-03.png';
import avatar04 from './images/avatars/avatar-04.png';
import avatar05 from './images/avatars/avatar-05.png';
import avatarDefault from './images/avatars/avatar-default.png';

const USER_ICONS = {
  'avatar-01.png': avatar01,
  'avatar-02.png': avatar02,
  'avatar-03.png': avatar03,
  'avatar-04.png': avatar04,
  'avatar-05.png': avatar05,
};

export function resolveUserIcon(iconName) {
  if (!iconName) return avatarDefault;

  // 将来APIがパスを返してもファイル名で解決できる
  const normalizedPath = iconName.replaceAll('\\', '/');
  const fileName = normalizedPath.split('/').pop();

  return USER_ICONS[fileName] ?? avatarDefault;
}
