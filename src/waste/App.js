import { useState } from 'react';
import Toppage from './Toppage';
import Subpage from './Subpage';

function App() {
  const [showTop, setShowTop] = useState(true);

  if (showTop) {
    return (
      <Toppage
        onOpenSubpage={() => setShowTop(false)}
      />
    );
  }

  return <Subpage />;
}

export default App;
