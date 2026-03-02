import React from 'react';
import { authStore } from '../state/authStore';
import { User, Shield, Calendar } from 'lucide-react';

const Profile = () => {
    const username = authStore.getUser();
    const role = authStore.getRole();

    return (
        <div className="container">
            <h1>My Profile</h1>
            <div className="card" style={{ maxWidth: '600px', marginTop: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    <div style={{ background: 'var(--primary)', padding: '2rem', borderRadius: '50%' }}>
                        <User size={64} />
                    </div>
                    <div>
                        <h2 style={{ margin: 0 }}>{username}</h2>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)', marginTop: '0.5rem' }}>
                            <Shield size={18} /> Role: {role.charAt(0).toUpperCase() + role.slice(1)}
                        </div>
                        <p style={{ color: 'var(--text-muted)' }}>Level 1 Shooter • Survival Grade: A</p>
                    </div>
                </div>
            </div>

            <div className="grid">
                <div className="card">
                    <h3>Achievements</h3>
                    <p>Locked: Win first 5 survivor rounds without a scratch.</p>
                </div>
                <div className="card">
                    <h3>Preferences</h3>
                    <p>BGM Volume: 50%</p>
                    <p>Canvas Quality: High</p>
                </div>
            </div>
        </div>
    );
};

export default Profile;
