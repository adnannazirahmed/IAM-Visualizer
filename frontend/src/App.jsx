import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AccountPage from './pages/AccountPage';
import DemoPage from './pages/DemoPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AccountPage />} />
        <Route path="/demo" element={<DemoPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
