import React from 'react';
import {
  LayoutDashboard,
  Eye,
  TrendingUp,
  ShoppingBag,
  Settings,
  HelpCircle,
  LogOut,
  ChevronRight,
  Search,
  Bell,
  User,
  Plus
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  active?: boolean;
  onClick?: () => void;
  badge?: string | number;
}

const SidebarItem = ({ icon: Icon, label, active, onClick, badge }: SidebarItemProps) => (
  <button
    onClick={onClick}
    className={cn(
      "sidebar-item w-full",
      active ? "sidebar-item-active" : "sidebar-item-inactive"
    )}
  >
    <Icon size={18} />
    <span className="flex-1 text-left">{label}</span>
    {badge && (
      <span className="bg-primary text-white text-[10px] px-1.5 py-0.5 rounded-full">
        {badge}
      </span>
    )}
  </button>
);

export default function AppLayout({ children, activeTab, onTabChange }: { children: React.ReactNode, activeTab: string, onTabChange: (tab: string) => void }) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-[#f0f1f3] p-4 flex flex-col gap-8 border-r border-black/5">
        <div className="px-4 py-2">
          <h1 className="text-xl font-bold tracking-tight">VINTED INTEL</h1>
        </div>

        <nav className="flex-1 flex flex-col gap-1">
          <SidebarItem 
            icon={LayoutDashboard} 
            label="Dashboard" 
            active={activeTab === 'Dashboard'} 
            onClick={() => onTabChange('Dashboard')}
          />
          <SidebarItem 
            icon={Eye} 
            label="Watchlist" 
            active={activeTab === 'Watchlist'} 
            onClick={() => onTabChange('Watchlist')}
          />
          <SidebarItem
            icon={TrendingUp}
            label="Opportunities"
            active={activeTab === 'Opportunities'}
            onClick={() => onTabChange('Opportunities')}
          />
          <SidebarItem
            icon={ShoppingBag}
            label="Purchases"
            active={activeTab === 'Purchases'}
            onClick={() => onTabChange('Purchases')}
          />
          <div className="mt-8 mb-2 px-4 text-[10px] font-bold uppercase tracking-wider text-gray-400">
            System
          </div>
          <SidebarItem 
            icon={Settings} 
            label="Settings" 
            active={activeTab === 'Settings'} 
            onClick={() => onTabChange('Settings')}
          />
          <SidebarItem 
            icon={HelpCircle} 
            label="Support" 
            active={activeTab === 'Support'} 
            onClick={() => onTabChange('Support')}
          />
        </nav>

        <div className="glass-card p-4 mt-auto relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Plus size={14} className="cursor-pointer" />
          </div>
          <div className="bg-primary text-white w-8 h-8 rounded-lg flex items-center justify-center mb-3">
            <TrendingUp size={16} />
          </div>
          <h3 className="text-sm font-bold mb-1">Upgrade to Pro</h3>
          <p className="text-[11px] text-gray-500 mb-3">Get real-time alerts and advanced fuzzy matching.</p>
          <button className="w-full bg-primary text-white text-xs py-2 rounded-lg font-medium hover:bg-black/80 transition-colors">
            Upgrade now
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-black/5 flex items-center justify-between px-8">
          <div className="relative w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input 
              type="text" 
              placeholder="Quick search listings..." 
              className="w-full bg-gray-100 border-none rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-primary/10 transition-all"
            />
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors relative">
              <Bell size={20} className="text-gray-600" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-accent rounded-full border-2 border-white"></span>
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <Settings size={20} className="text-gray-600" />
            </button>
            <div className="h-8 w-[1px] bg-gray-200 mx-2"></div>
            <div className="flex items-center gap-3 pl-2">
              <div className="text-right">
                <p className="text-xs font-bold">Mattia Castiello</p>
                <p className="text-[10px] text-gray-500">mattia.c@intel.it</p>
              </div>
              <div className="w-9 h-9 bg-gray-200 rounded-full overflow-hidden border border-black/5">
                <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Mattia" alt="Avatar" />
              </div>
            </div>
          </div>
        </header>

        {/* Viewport */}
        <div className="flex-1 overflow-y-auto p-8 bg-[#f8f9fa]">
          {children}
        </div>
      </main>
    </div>
  );
}
