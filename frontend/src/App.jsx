import Landing from "./pages/Landing";
import Register from "./pages/accounts/Register";
import Login from "./pages/accounts/Login";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        {/* Future routes: /dashboard, etc. */}
      </Routes>
    </Router>
  );
}

export default App;
