const mockUsers = [
  {
    id: 1,
    name: '田中太郎',
    iconUrl: null,
  },
  {
    id: 2,
    name: '佐藤花子',
    iconUrl: null,
  },
  {
    id: 3,
    name: '鈴木一郎',
    iconUrl: null,
  },
];

export async function fetchUsers() {
  // API通信っぽく少し待たせる
  await new Promise((resolve) => setTimeout(resolve, 500));

  return mockUsers;
}
