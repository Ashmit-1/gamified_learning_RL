import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import QuizGame from './pages/QuizGame';
import History from './pages/History';
import Profile from './pages/Profile';
import { authStore } from './state/authStore';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const isAuthenticated = authStore.isAuthenticated();
  const role = authStore.getRole();

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(role)) return <Navigate to="/" replace />;

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Student Routes */}
        <Route path="/student/dashboard" element={
          <ProtectedRoute allowedRoles={['student']}><StudentDashboard /></ProtectedRoute>
        } />
        <Route path="/student/history" element={
          <ProtectedRoute allowedRoles={['student']}><History /></ProtectedRoute>
        } />
        <Route path="/quiz/:topicId" element={
          <ProtectedRoute allowedRoles={['student']}><QuizGame /></ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute><Profile /></ProtectedRoute>
        } />

        {/* Teacher Routes */}
        <Route path="/teacher/dashboard" element={
          <ProtectedRoute allowedRoles={['teacher']}><TeacherDashboard /></ProtectedRoute>
        } />

        {/* Fallback */}
        <Route path="/" element={
          authStore.isAuthenticated() ? (
            authStore.getRole() === 'student' ? <Navigate to="/student/dashboard" /> : <Navigate to="/teacher/dashboard" />
          ) : <Navigate to="/login" />
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
