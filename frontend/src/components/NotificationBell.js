import React, { useState, useEffect, useRef } from 'react';
import { Bell } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const NotificationBell = () => {
  const { user, token } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!user || !token) return;
    const fetch = async () => {
      try {
        const res = await axios.get(`${API}/notifications`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setNotifications(res.data.notifications || []);
        setUnreadCount(res.data.unread_count || 0);
      } catch (e) { /* silent */ }
    };
    fetch();
    const interval = setInterval(fetch, 30000);
    return () => clearInterval(interval);
  }, [user, token]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAllRead = async () => {
    try {
      await axios.put(`${API}/notifications/read-all`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (e) { /* silent */ }
  };

  if (!user) return null;

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d`;
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => { setOpen(!open); if (!open && unreadCount > 0) markAllRead(); }}
        className="relative p-2 text-[#6B6661] hover:text-[#2D2A26] transition-colors"
        data-testid="notification-bell"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[#FFBE98] text-[#2D2A26] text-[10px] font-bold rounded-full flex items-center justify-center" data-testid="notification-badge">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-xl border border-stone-100 z-50 overflow-hidden" data-testid="notification-dropdown">
          <div className="px-4 py-3 border-b border-stone-100 flex justify-between items-center">
            <span className="text-sm font-semibold text-[#2D2A26]">Notificações</span>
            {unreadCount > 0 && (
              <button onClick={markAllRead} className="text-xs text-[#FFBE98] hover:text-[#E6A07C]">
                Marcar todas como lidas
              </button>
            )}
          </div>
          <div className="max-h-72 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-[#6B6661]">
                Sem notificações
              </div>
            ) : (
              notifications.slice(0, 10).map((n) => (
                <Link
                  key={n.notification_id}
                  to={n.link || '#'}
                  onClick={() => setOpen(false)}
                  className={`block px-4 py-3 border-b border-stone-50 hover:bg-stone-50 transition-colors ${!n.read ? 'bg-[#FFBE98]/5' : ''}`}
                >
                  <div className="flex justify-between items-start gap-2">
                    <div className="min-w-0">
                      <p className={`text-xs truncate ${!n.read ? 'font-semibold text-[#2D2A26]' : 'text-[#6B6661]'}`}>
                        {n.title}
                      </p>
                      <p className="text-xs text-[#6B6661] mt-0.5 line-clamp-2">{n.message}</p>
                    </div>
                    <span className="text-[10px] text-[#6B6661] whitespace-nowrap flex-shrink-0">{timeAgo(n.created_at)}</span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
