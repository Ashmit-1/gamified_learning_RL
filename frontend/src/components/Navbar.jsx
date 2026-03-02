import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authStore } from '../state/authStore';
import { LogOut, Home, Book, FileText, User as UserIcon, BarChart } from 'lucide-react';

const Navbar = () => {
    const navigate = useNavigate();
    const role = authStore.getRole();
    const isAuthenticated = authStore.isAuthenticated();
    const user = authStore.getUser();

    if (!isAuthenticated) return null;

    return (
        <nav className="navbar">
            <div className="nav-container">
                <Link to="/" className="nav-logo">
                    <img src="/assets/logo.png" alt="Logo" className="logo-img" />
                    <span>Gyan</span>
                </Link>
                <div className="nav-links">
                    {role === 'student' ? (
                        <>
                            <Link to="/student/dashboard" className="nav-link"><Home size={18} /> Dashboard</Link>
                            <Link to="/student/history" className="nav-link"><FileText size={18} /> History</Link>
                        </>
                    ) : (
                        <>
                            <Link to="/teacher/dashboard" className="nav-link"><BarChart size={18} /> Dashboard</Link>
                        </>
                    )}
                    <Link to="/profile" className="nav-profile">
                        <UserIcon size={18} /> <span>{user} ({role})</span>
                    </Link>
                    <button onClick={() => authStore.logout()} className="logout-btn">
                        <LogOut size={18} /> Logout
                    </button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
