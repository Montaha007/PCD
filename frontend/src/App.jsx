import Landing from "./pages/Landing";
import Register from "./pages/accounts/Register";
import Login from "./pages/accounts/Login";
import Profile from "./pages/profile/Profile";
import WeeklyReport from "./pages/weeklyreport/WeeklyReport";
import Dashboard from "./pages/dashboard/Dashboard";
import SleepLog from "./pages/sleeplog/SleepLog";
import Journal from "./pages/mood/Journal";
import AudioTherapy from "./pages/audiotherapy/AudioTherapy";
import LifestyleForm from "./pages/lifestyle/LifeStyle";
import RoutineOptimizer from "./pages/routine/RoutineOptimizer";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { UserDataProvider } from "./context/UserDataContext";
import { Toaster } from "sonner";

function App() {
  return (
    <UserDataProvider>
    <Toaster
      theme="dark"
      position="bottom-right"
      toastOptions={{
        style: {
          background: 'linear-gradient(160deg, rgba(8,14,38,0.96), rgba(6,12,28,0.92))',
          border: '1px solid rgba(100,160,255,0.2)',
          color: '#e8eef8',
          backdropFilter: 'blur(20px)',
        },
      }}
    />
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/sleep-log" element={<SleepLog />} />
        <Route path="/lifestyle" element={<LifestyleForm />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/routine-optimizer" element={<RoutineOptimizer />} />
        <Route path="/audio-therapy" element={<AudioTherapy />} />
        <Route path="/weekly-report" element={<WeeklyReport />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Router>
    </UserDataProvider>
  );
}

export default App;
