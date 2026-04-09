import { useEffect, useState } from "react";
import Landing from "./pages/Landing";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        {/* More routes later: /signup, /dashboard, etc. */}
      </Routes>
    </Router>
  );
}

export default App;