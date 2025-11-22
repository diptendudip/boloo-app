'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Activity,
  Folder,
  Building2,
  Tags,
  Users,
  BarChart3,
  Settings,
  LogOut
} from 'lucide-react';

const navItems = [
  { href: '/', label: 'Dashboard', icon: Home },
  { href: '/monitoring', label: 'Monitoring', icon: Activity },
  { href: '/cases', label: 'Cases', icon: Folder },
  { href: '/entities', label: 'Entities', icon: Building2 },
  { href: '/taxonomies', label: 'Taxonomies', icon: Tags },
  { href: '/users', label: 'Users', icon: Users },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Navigation() {
  const pathname = usePathname();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  return (
    <nav className="w-64 bg-white border-r border-gray-200 h-screen fixed left-0 top-0 overflow-y-auto">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-primary-600">Boloo</h1>
        <p className="text-sm text-gray-500 mt-1">Admin Console</p>
      </div>

      {/* Navigation Items */}
      <div className="p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                    ${isActive
                      ? 'bg-primary-50 text-primary-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>

      {/* User Info & Logout */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors w-full"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </nav>
  );
}
