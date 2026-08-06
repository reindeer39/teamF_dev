import { resolveUserIcon } from './resolveUserIcon';


test('DBのiconsパスをReactに含まれるユーザー画像へ変換する', () => {
  expect(resolveUserIcon('/icons/user1.png')).toContain('human1');
  expect(resolveUserIcon('\\icons\\user2.png')).toContain('human2');
});
