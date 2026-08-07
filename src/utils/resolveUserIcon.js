import human1 from '../images/human1.png';
import human2 from '../images/human2.png';
import human3 from '../images/human3.png';
import human4 from '../images/human4.png';
import human5 from '../images/human5.png';
import human6 from '../images/human6.png';


const USER_ICONS = {
  'user1.png': human1,
  'user2.png': human2,
  'user3.png': human3,
  'user4.png': human4,
  'user5.png': human5,
  'user6.png': human6,
  'human1.png': human1,
  'human2.png': human2,
  'human3.png': human3,
  'human4.png': human4,
  'human5.png': human5,
  'human6.png': human6,
};


export function resolveUserIcon(iconPath, fallback = human1) {
  if (!iconPath) return fallback;
  const normalizedPath = iconPath.replaceAll('\\', '/');
  const fileName = normalizedPath.split('/').pop();
  return USER_ICONS[fileName] || normalizedPath;
}
